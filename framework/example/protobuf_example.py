from framework.protobufs import protobuf_compiler
from framework.protobufs.compiled_protobufs.example_pb2 import *


def run():
    protobuf_compiler.recompile_all()

    test_message = ExampleMessage(
        name="hi",
        number=23
    )

    encoded = test_message.SerializeToString()
    print(encoded)

    decoded = ExampleMessage()
    decoded.ParseFromString(encoded)

    name = test_message.name
    number = test_message.number

    print(decoded)
    print(f"{name}")
    print(f"{number=}")


if __name__ == '__main__':
    run()
