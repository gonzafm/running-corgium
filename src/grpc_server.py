import grpc
from concurrent import futures
import time

# Import the generated classes
from generated import helloworld_pb2
from generated import helloworld_pb2_grpc


# Create a class to define the server functions, derived from
# helloworld_pb2_grpc.GreeterServicer
class Greeter(helloworld_pb2_grpc.GreeterServicer):
    # The SayHello RPC function, as defined in the .proto file
    def SayHello(self, request, context):
        # For this example, we ignore the request and return a fixed message
        # to replicate the behavior of the root() endpoint.
        return helloworld_pb2.HelloReply(message="Hello World")


def serve():
    # Create a gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Add the defined class to the server
    helloworld_pb2_grpc.add_GreeterServicer_to_server(Greeter(), server)

    # Listen on port 50051
    print("Starting gRPC server. Listening on port 50051.")
    server.add_insecure_port("[::]:50051")
    server.start()

    # Keep the server running
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    serve()
