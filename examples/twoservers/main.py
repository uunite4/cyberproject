import asyncio

from examples.twoservers.server_test1 import ServerTest1
from examples.twoservers.server_test2 import ServerTest2
from examples.twoservers.settings_test import TEST2_SERVER_PORT, TEST2_SERVER_IP, TEST1_SERVER_PORT, TEST1_SERVER_IP


async def main():
    server1 = ServerTest1()
    server2 = ServerTest2()

    # Start servers as background tasks
    task1 = asyncio.create_task(server1.run())
    task2 = asyncio.create_task(server2.run())

    # Wait a moment to ensure servers are up
    await asyncio.sleep(1)

    # Connect them
    await asyncio.gather(
        server1.server.connect_to_server(
            ip=TEST2_SERVER_IP,
            port=TEST2_SERVER_PORT
        ),
        server2.server.connect_to_server(
            ip=TEST1_SERVER_IP,
            port=TEST1_SERVER_PORT
        ),
    )

    # Keep program running
    await asyncio.gather(task1, task2)


if __name__ == "__main__":
    asyncio.run(main())
