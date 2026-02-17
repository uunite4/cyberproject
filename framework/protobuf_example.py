from framework.protobufs import protobuf_compiler


def run():
    protobuf_compiler.recompile_all()

    test_message = TestM()
    test_message.player_id = 5
    test_message.direction_x = 1
    test_message.direction_y = 1

    encoded = test_message.SerializeToString()

    decoded = PlayerState()
    decoded.ParseFromString(encoded)

    print(encoded)
    print(decoded)


if __name__ == '__main__':
    run()
