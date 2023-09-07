from enum import Enum
import asyncio
from data import *
from push_receiver import PushReceiver
from feed import Feed

async def connect_to_robomaster(ip: str) -> "RoboMasterClient":
    command_socket = await asyncio.open_connection(ip, CONTROL_PORT)

    return RoboMasterClient(ip, command_socket)


class RoboMasterClient:
    conn: tuple[asyncio.StreamReader, asyncio.StreamWriter]

    command_lock: asyncio.Lock = asyncio.Lock()

    push_receiver: PushReceiver

    line: Feed[Line] = Feed()

    command_task: asyncio.Task
    handle_push_task: asyncio.Task

    def __init__(self, ip: str, command_conn: tuple[asyncio.StreamReader, asyncio.StreamWriter]) -> None:
        self.conn = command_conn

        self.push_receiver = PushReceiver(ip, PUSH_PORT)

        self.command_task = asyncio.create_task(self._do("command"))
        self.handle_push_task = asyncio.create_task(self.handle_push(self.push_receiver.feed))

    def __del__(self):
        self.command_task.cancel()
        self.handle_push_task.cancel()

    async def handle_push(self, feed: Feed[Response]):
        async for response in feed:
            topic = response.data[0]
            subject = response.data[2]
            parseData = Response(response.data[3:])

            if (topic == "AI"):
                if (subject == "line"): await self.line.feed(Line.parse(parseData))
                else: print(f"Unknown AI subject: {subject}")
            else:
                print(f"Unknown topic: {topic}")

    async def _do(self, command: str):
        await self.command_lock.acquire()

        self.conn[1].write(command.encode())
        await self.conn[1].drain()

        data = await self.conn[0].readuntil(b";")

        self.command_lock.release()

        return Response(data.decode()[:-1].split(" "))

    async def do(self, *commands: str | int | float | bool | Enum):
        command = ' '.join(map(command_to_str, commands)) + ';'
        return await self._do(command)

    async def get_version(self):
        return (await self.do("version")).get_str(0)
    
    async def set_robot_mode(self, mode: Mode):
        return await self.do("robot", "mode", mode)

    async def get_robot_mode(self):
        return (await self.do("robot", "mode", "?")).get_str(0)
    
    async def set_speed(self, forwards: float, right: float, clockwise: float):
        return await self.do("chassis", "speed", "x", forwards, "y", right, "z", clockwise)

    async def set_wheel_speed(self, front_right: float, front_left: float, back_left: float, back_right: float):
        return await self.do(
            "chassis", "wheel",
            "w1", front_right,
            "w2", front_left,
            "w3", back_left,
            "w4", back_right
        )
    
    async def get_wheel_speed(self):
        return ChassisSpeed.parse(await self.do("chassis", "speed", "?"))
    
    """
    NOTE: This does *not* wait until the robot has finished moving.
    """
    async def move(self, forwards: float, right: float, clockwise: float, speed: float | None = None, rotationSpeed: float | None = None):
        args = [
            "chassis", "move",
            "x", forwards,
            "y", right,
            "z", clockwise
        ]

        if speed is not None:
            args.append("vxy")
            args.append(speed)

        if rotationSpeed is not None:
            args.append("vz")
            args.append(rotationSpeed)

        await self.do(*args)

    async def get_position(self):
        return ChassisPosition.parse(await self.do("chassis", "position", "?"))
    
    async def get_attitude(self):
        return ChassisAttitude.parse(await self.do("chassis", "attitude", "?"))
    
    async def get_status(self):
        return ChassisStatus.parse(await self.do("chassis", "status", "?"))

    async def set_chassis_push_rate(self, position_freq: int | None = None, attitude_freq: int | None = None, status_freq: int | None = None):
        if position_freq is None and attitude_freq is None and status_freq is None:
            raise ValueError("At least one frequency must be set.")

        position_args = []
        if position_freq == 0:
            position_args = ["position", False]
        elif position_freq is not None:
            position_args = ["position", True, "pfreq", position_freq]

        attitude_args = []
        if attitude_freq == 0:
            attitude_args = ["attitude", False]
        elif attitude_args is not None:
            attitude_args = ["attitude", True, "afreq", attitude_freq]

        status_args = []
        if status_freq == 0:
            status_args = ["status", False]
        elif status_freq is not None:
            status_args = ["status", True, "sfreq", status_freq]

        await self.do("chassis", "push", *position_args, *attitude_args, *status_args)

    async def set_ir_enabled(self, enabled: bool = True):
        return await self.do("ir_distance_sensor", "measure", enabled)
    
    async def get_ir_distance(self, ir_id: int):
        return (await self.do("ir_distance_sensor", "distance", ir_id, "?")).get_float(0)
    
    async def move_arm(self, x_dist: float, y_dist: float):
        return await self.do("robotic_arm", "move", "x", x_dist, "y", y_dist)
    
    async def set_arm_position(self, x: float, y: float):
        return await self.do("robotic_arm", "moveto", "x", x, "y", y)
    
    async def get_arm_position(self):
        response = await self.do("robotic_arm", "position", "?")
        return (response.get_float(0), response.get_float(1))
    
    # TODO Allow different levels of force when opening?
    # https://robomaster-dev.readthedocs.io/en/latest/text_sdk/protocol_api.html#mechanical-gripper-opening-control
    async def open_gripper(self):
        return await self.do("robotic_gripper", "open", 1)
    
    # TODO Allow different levels of force when closing?
    # https://robomaster-dev.readthedocs.io/en/latest/text_sdk/protocol_api.html#mechanical-gripper-opening-control
    async def close_gripper(self):
        return await self.do("robotic_gripper", "close", 1)
    
    async def get_gripper_status(self):
        return (await self.do("robotic_gripper", "status", "?")).get_enum(0, GripperStatus)
    
    async def set_line_recognition_colour(self, colour: LineColour):
        await self.do("AI", "attribute", "line_color", colour)

    async def set_line_recognition_enabled(self, enabled: bool = True):
        await self.do("AI", "push", "line", enabled)
