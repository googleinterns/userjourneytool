import generated.graph_structures_pb2

my_service = generated.graph_structures_pb2.Service()
my_service.name = "chuan_service"
my_endpoint = my_service.endpoints.add()
my_endpoint.name = "chuan_endpoint"
my_endpoint.service_name = my_service.name
print(my_service)

# python -m grpc.tools.protoc --proto_path=protos --python_out=generated --mypy_out=generated protos/*
