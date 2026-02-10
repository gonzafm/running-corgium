# Corgium Runner

A tool for helping visualize my running data and build models

# Running the app

    uvicorn src.main:app --reload

# gRPC

## Regenerating gRPC Code

If you make changes to the `.proto` files, you will need to regenerate the Python gRPC code. You can do this by running the following command from the root of the project:

# Docker Commands

## Build the docker image    
    docker compose up -d 

## Delete the docker image
    docker compose down 
## Delete the docker volume
    docker volume rm corgium-runner_postgres-data


```bash
python -m grpc_tools.protoc -I protos --python_out=src/generated --pyi_out=src/generated --grpc_python_out=src/generated protos/helloworld.proto
```

# JustFile Commands

- `just build` - Build the docker image
- `just run` - Run the docker image

# FrontEnd Commands                                                                                                                                                                                                                                                                    
                                                                                                                                                                                                                                                                              
  - bun dev - Start dev server (port 5173)                                                                                                                                                                                                                                    
  - bun run test - Run all tests                                                                                                                                                                                                                                              
  - bun run test:unit - Run unit tests only                                                                                                                                                                                                                                   
  - bun run test:integration - Run integration tests (requires backend)    
