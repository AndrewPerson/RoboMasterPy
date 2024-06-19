# How To

## Connect to the robot
```py
import asyncio
from sbhs_robomaster import connect_to_robomaster, DIRECT_CONNECT_IP

async def main():
    async with await connect_to_robomaster(DIRECT_CONNECT_IP) as robot:
        # Do stuff with the robot
        pass

asyncio.run(main())
```

## Move the robot
```py
import asyncio
from sbhs_robomaster import connect_to_robomaster, DIRECT_CONNECT_IP

async def main():
    async with await connect_to_robomaster(DIRECT_CONNECT_IP) as robot:
        # Rotate the robot 90° clockwise
        await robot.rotate(90)

        # Rotate all wheels indefinitely at 50rpm
        await robot.set_all_wheel_speeds(50)
        await asyncio.sleep(5)

        # Stop the robot
        await robot.set_all_wheel_speeds(0)

        # Get the left wheels to rotate at 50rpm and the right wheels at 20
        await robot.set_left_right_wheel_speeds(50, 20)
        await asyncio.sleep(5)

        await robot.set_all_wheel_speeds(0)

asyncio.run(main())
```

## Move the arm
```py
import asyncio
from sbhs_robomaster import connect_to_robomaster, DIRECT_CONNECT_IP

async def main():
    async with await connect_to_robomaster(DIRECT_CONNECT_IP) as robot:
        # Move the arm to the position (79, 150). Each robot has its coordinates
        # relative to a different origin, so you will have to find the coordinates
        # for your robot yourself. (Using `robot.get_arm_position`)
        await robot.set_arm_position(79, 150)

        # Move the arm 10 units in the x direction and 10 units in the y direction.
        await robot.move_arm(10, 10)

        # Using `move_arm` is the same as:
        x, y = await robot.get_arm_position()
        await robot.set_arm_position(x + 10, y + 10)

asyncio.run(main())
```

## Get line information
```py
import asyncio
from sbhs_robomaster import connect_to_robomaster, DIRECT_CONNECT_IP, DroppingFeed, LineColour

async def main():
    async with await connect_to_robomaster(DIRECT_CONNECT_IP) as robot:
        await robot.set_line_recognition_enabled()
        await robot.set_line_recognition_color(LineColour.Red)

        # We use a `DroppingFeed` so we always get the most recent line data
        # even if we can't process it as fast as we receive it.
        line = DroppingFeed(robot.line)

        while True:
            print(await line.get_most_recent())

asyncio.run(main())
```

Also look at `.feed.Feed` and `.dropping_feed.DroppingFeed` for more explanation and help.

## Get IR information
```py
import asyncio
from sbhs_robomaster import connect_to_robomaster, DIRECT_CONNECT_IP

async def main():
    async with await connect_to_robomaster(DIRECT_CONNECT_IP) as robot:
        await robot.set_ir_enabled()

        # Get the distance from the IR sensor 1
        print(await robot.get_ir_distance(1))

asyncio.run(main())
```