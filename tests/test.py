import asyncio
from src.sbhs_robomaster import *

async def main():
    async with await connect_to_robomaster(DIRECT_CONNECT_IP) as robot:
        await robot.set_line_recognition_colour(LineColour.Red)
        await robot.set_line_recognition_enabled()

        async for line in DroppingAsyncEnumerable(robot.line):
            print(f"LINE: {line}")
            # print(line.points)

    # async for test in Feed():
    #     print(test)


asyncio.run(main())
