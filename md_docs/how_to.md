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
await robot.move(0.5, 0.5, 0) # Move forward by 0.5m and to the right by 0.5m

await robot.move(0, 0, 90) # Rotate clockwise by 90 degrees

await robot.set_speed(0.5, 0.5, 0) # Move the robot indefinitely at a speed of 0.5m/s forward and 0.5m/s to the right

await robot.set_speed(0, 0, 10) # Rotate the robot indefinitely at a speed of 10 degrees/s clockwise

await robot.set_wheel_speed(50, 50, 50, 50) # Rotate all wheels indefinitely at 50rpm
```

## Move the arm
```py
await robot.set_arm_position(79, 150) # Move the arm to the position (79, 150). Each robot has its coordinate relative to a different origin, so you will have to find the coordinates for your robot yourself. (Using `robot.get_arm_position()``)

await robot.move_arm(10, 10) # Move the arm 10 units in the x direction and 10 units in the y direction.

# Using `move_arm` is the same as:
x, y = await robot.get_arm_position()
await robot.set_arm_position(x + 10, y + 10)
```

## Get line information
```py
from sbhs_robomaster import LineColour

await robot.set_line_recognition_enabled()
await robot.set_line_recognition_colour(LineColour.Red)

async for line in robot.line:
    print(line)
```

Also look at `.feed.Feed` and `.dropping_async_enumerable.DroppingAsyncEnumerable` for more explanation and help.

## Get IR information
```py
await robot.set_ir_enabled()

print(await robot.get_ir_distance(1)) # Get the distance from the IR sensor 1
```