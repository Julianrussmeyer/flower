mod client;
mod grpc_bidi;
mod grpc_rere;
mod message_handler;
mod serde;
mod start;
mod task_handler;
mod typing;

pub mod flwr_proto {
    tonic::include_proto!("flwr.proto");
}

struct TestClient;

impl client::Client for TestClient {
    fn get_parameters(&self) -> typing::GetParametersRes {
        println!("get_parameters");
        typing::GetParametersRes {
            parameters: typing::Parameters {
                tensors: vec![vec![1 as u8]],
                tensor_type: "".to_string(),
            },
            status: typing::Status {
                code: typing::Code::OK,
                message: "".to_string(),
            },
        }
    }

    fn get_properties(&self, ins: typing::GetPropertiesIns) -> typing::GetPropertiesRes {
        println!("get_properties");
        typing::GetPropertiesRes {
            properties: std::collections::HashMap::new(),
            status: typing::Status {
                code: typing::Code::OK,
                message: "".to_string(),
            },
        }
    }

    fn fit(&self, ins: typing::FitIns) -> typing::FitRes {
        println!("fit");
        typing::FitRes {
            parameters: typing::Parameters {
                tensors: vec![vec![1 as u8]],
                tensor_type: "".to_string(),
            },
            num_examples: 1,
            metrics: std::collections::HashMap::new(),
            status: typing::Status {
                code: typing::Code::OK,
                message: "".to_string(),
            },
        }
    }

    fn evaluate(&self, ins: typing::EvaluateIns) -> typing::EvaluateRes {
        println!("evaluate");
        typing::EvaluateRes {
            num_examples: 1,
            metrics: std::collections::HashMap::new(),
            loss: 1.0,
            status: typing::Status {
                code: typing::Code::OK,
                message: "".to_string(),
            },
        }
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("Start client...");
    let _client =
        start::start_client("http://127.0.0.1:9092", &TestClient, None, Some("rere")).await?;
    Ok(())
}
