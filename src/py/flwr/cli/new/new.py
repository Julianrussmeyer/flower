# Copyright 2024 Flower Labs GmbH. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Flower command line interface `new` command."""

import re
from enum import Enum
from pathlib import Path
from string import Template
from typing import Dict, Optional

import typer
from typing_extensions import Annotated

from ..utils import (
    is_valid_project_name,
    prompt_options,
    prompt_text,
    sanitize_project_name,
)


class MlFramework(str, Enum):
    """Available frameworks."""

    NUMPY = "NumPy"
    PYTORCH = "PyTorch"
    TENSORFLOW = "TensorFlow"
    JAX = "JAX"
    HUGGINGFACE = "HF"
    MLX = "MLX"
    SKLEARN = "sklearn"
    FLOWERTUNE = "FlowerTune"


class LlmChallengeName(str, Enum):
    """Available LLM challenges."""

    GENERALNLP = "GeneralNLP"
    FINANCE = "Finance"
    MEDICAL = "Medical"
    CODE = "Code"


class TemplateNotFound(Exception):
    """Raised when template does not exist."""


def load_template(name: str) -> str:
    """Load template from template directory and return as text."""
    tpl_dir = (Path(__file__).parent / "templates").absolute()
    tpl_file_path = tpl_dir / name

    if not tpl_file_path.is_file():
        raise TemplateNotFound(f"Template '{name}' not found")

    with open(tpl_file_path, encoding="utf-8") as tpl_file:
        return tpl_file.read()


def render_template(template: str, data: Dict[str, str]) -> str:
    """Render template."""
    tpl_file = load_template(template)
    tpl = Template(tpl_file)
    if ".gitignore" not in template:
        return tpl.substitute(data)
    return tpl.template


def create_file(file_path: Path, content: str) -> None:
    """Create file including all nessecary directories and write content into file."""
    file_path.parent.mkdir(exist_ok=True)
    file_path.write_text(content)


def render_and_create(file_path: Path, template: str, context: Dict[str, str]) -> None:
    """Render template and write to file."""
    content = render_template(template, context)
    create_file(file_path, content)


# pylint: disable=too-many-locals,too-many-branches,too-many-statements
def new(
    project_name: Annotated[
        Optional[str],
        typer.Argument(metavar="project_name", help="The name of the project"),
    ] = None,
    framework: Annotated[
        Optional[MlFramework],
        typer.Option(case_sensitive=False, help="The ML framework to use"),
    ] = None,
    username: Annotated[
        Optional[str],
        typer.Option(case_sensitive=False, help="The Flower username of the author"),
    ] = None,
) -> None:
    """Create new Flower project."""
    if project_name is None:
        project_name = prompt_text("Please provide the project name")
    if not is_valid_project_name(project_name):
        project_name = prompt_text(
            "Please provide a name that only contains "
            "characters in {'-', a-zA-Z', '0-9'}",
            predicate=is_valid_project_name,
            default=sanitize_project_name(project_name),
        )

    # Set project directory path
    package_name = re.sub(r"[-_.]+", "-", project_name).lower()
    import_name = package_name.replace("-", "_")
    project_dir = Path.cwd() / package_name

    if project_dir.exists():
        if not typer.confirm(
            typer.style(
                f"\n💬 {project_name} already exists, do you want to override it?",
                fg=typer.colors.MAGENTA,
                bold=True,
            )
        ):
            return

    if username is None:
        username = prompt_text("Please provide your Flower username")

    if framework is not None:
        framework_str = str(framework.value)
    else:
        framework_value = prompt_options(
            "Please select ML framework by typing in the number",
            sorted([mlf.value for mlf in MlFramework]),
        )
        selected_value = [
            name
            for name, value in vars(MlFramework).items()
            if value == framework_value
        ]
        framework_str = selected_value[0]

    framework_str = framework_str.lower()

    llm_challenge_str = None
    if framework_str == "flowertune":
        llm_challenge_value = prompt_options(
            "Please select LLM challenge by typing in the number",
            sorted([challenge.value for challenge in LlmChallengeName]),
        )
        selected_value = [
            name
            for name, value in vars(LlmChallengeName).items()
            if value == llm_challenge_value
        ]
        llm_challenge_str = selected_value[0]
        llm_challenge_str = llm_challenge_str.lower()

    print(
        typer.style(
            f"\n🔨 Creating Flower project {project_name}...",
            fg=typer.colors.GREEN,
            bold=True,
        )
    )

    context = {
        "project_name": project_name,
        "package_name": package_name,
        "import_name": import_name.replace("-", "_"),
        "username": username,
    }

    # List of files to render
    if llm_challenge_str:
        files = {
            ".gitignore": {"template": "app/.gitignore.tpl"},
            "pyproject.toml": {"template": f"app/pyproject.{framework_str}.toml.tpl"},
            "README.md": {"template": f"app/README.{framework_str}.md.tpl"},
            f"{import_name}/__init__.py": {"template": "app/code/__init__.py.tpl"},
            f"{import_name}/server.py": {
                "template": "app/code/flwr_tune/server.py.tpl"
            },
            f"{import_name}/client.py": {
                "template": "app/code/flwr_tune/client.py.tpl"
            },
            f"{import_name}/app.py": {"template": "app/code/flwr_tune/app.py.tpl"},
            f"{import_name}/models.py": {
                "template": "app/code/flwr_tune/models.py.tpl"
            },
            f"{import_name}/dataset.py": {
                "template": "app/code/flwr_tune/dataset.py.tpl"
            },
            f"{import_name}/conf/config.yaml": {
                "template": "app/code/flwr_tune/config.yaml.tpl"
            },
            f"{import_name}/conf/static_config.yaml": {
                "template": "app/code/flwr_tune/static_config.yaml.tpl"
            },
        }

        # Challenge specific context
        fraction_fit = "0.2" if llm_challenge_str == "code" else "0.1"
        if llm_challenge_str == "generalnlp":
            challenge_name = "General NLP"
            num_clients = "20"
            dataset_name = "vicgalle/alpaca-gpt4"
        elif llm_challenge_str == "finance":
            challenge_name = "Finance"
            num_clients = "50"
            dataset_name = "FinGPT/fingpt-sentiment-train"
        elif llm_challenge_str == "medical":
            challenge_name = "Medical"
            num_clients = "20"
            dataset_name = "medalpaca/medical_meadow_medical_flashcards"
        else:
            challenge_name = "Code"
            num_clients = "10"
            dataset_name = "lucasmccabe-lmi/CodeAlpaca-20k"

        context["llm_challenge_str"] = llm_challenge_str
        context["fraction_fit"] = fraction_fit
        context["challenge_name"] = challenge_name
        context["num_clients"] = num_clients
        context["dataset_name"] = dataset_name
    else:
        files = {
            ".gitignore": {"template": "app/.gitignore.tpl"},
            "README.md": {"template": "app/README.md.tpl"},
            "pyproject.toml": {"template": f"app/pyproject.{framework_str}.toml.tpl"},
            f"{import_name}/__init__.py": {"template": "app/code/__init__.py.tpl"},
            f"{import_name}/server_app.py": {
                "template": f"app/code/server.{framework_str}.py.tpl"
            },
            f"{import_name}/client_app.py": {
                "template": f"app/code/client.{framework_str}.py.tpl"
            },
        }

        # Depending on the framework, generate task.py file
        frameworks_with_tasks = [
            MlFramework.PYTORCH.value.lower(),
            MlFramework.JAX.value.lower(),
            MlFramework.HUGGINGFACE.value.lower(),
            MlFramework.MLX.value.lower(),
            MlFramework.TENSORFLOW.value.lower(),
        ]
        if framework_str in frameworks_with_tasks:
            files[f"{import_name}/task.py"] = {
                "template": f"app/code/task.{framework_str}.py.tpl"
            }

    for file_path, value in files.items():
        render_and_create(
            file_path=project_dir / file_path,
            template=value["template"],
            context=context,
        )

    print(
        typer.style(
            "🎊 Project creation successful.\n\n"
            "Use the following command to run your project:\n",
            fg=typer.colors.GREEN,
            bold=True,
        )
    )

    _add = "	huggingface-cli login\n" if framework_str == "flowertune" else ""
    print(
        typer.style(
            f"	cd {package_name}\n" + "	pip install -e .\n" + _add + "	flwr run\n",
            fg=typer.colors.BRIGHT_CYAN,
            bold=True,
        )
    )
