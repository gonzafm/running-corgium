# Corgium Runner

A tool for helping visualize my running data and build models

# Running the app

    uvicorn src.main:app --reload

# Tasks
  - [x] Create a Basic Shell
  - [x] Upload it to github
  - [x] Create basic action to build 
  - [ ] Create gRPC Model
  - [ ] Conect to Strava

# gRPC

## Regenerating gRPC Code

If you make changes to the `.proto` files, you will need to regenerate the Python gRPC code. You can do this by running the following command from the root of the project:

```bash
python -m grpc_tools.protoc -I protos --python_out=src/generated --pyi_out=src/generated --grpc_python_out=src/generated protos/helloworld.proto
```
