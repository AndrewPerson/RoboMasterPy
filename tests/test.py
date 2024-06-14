import asyncio
from src.sbhs_robomaster import *

async def main():
    async with await connect_to_robomaster(DIRECT_CONNECT_IP) as robot:
        await robot.set_line_recognition_colour(LineColour.Red)
        await robot.set_line_recognition_enabled()

        dropping_line = DroppingFeed(robot.line)
        while True:
            line = await dropping_line.get_most_recent()
            print(f"LINE: {line}")

asyncio.run(main())
