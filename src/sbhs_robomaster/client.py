from enum import Enum
from typing import Final
import asyncio
from .data import *
from .push_receiver import PushReceiver
from .feed import Feed


DIRECT_CONNECT_IP: Final[str] = "192.168.2.1"

_CONTROL_PORT: Final[int] = 40923
_PUSH_PORT: Final[int] = 40924


async def connect_to_robomaster(ip: str) -> "RoboMasterClient":
    """
    Connects to a RoboMaster robot at the given IP address.
    
    If the host computer (the computer the code is running on) is connected directly to robot's WiFi, and not over another
    network, pass in `DIRECT_CONNECT_IP`:

    ```py
    import asyncio
    from sbhs_robomaster import connect_to_robomaster, DIRECT_CONNECT_IP

    async def main():
        async with await connect_to_robomaster(DIRECT_CONNECT_IP) as robot:
            # Do stuff with robot
            pass

    asyncio.run(main())
    ```
    """

    command_socket = await asyncio.open_connection(ip, _CONTROL_PORT)

    client = RoboMasterClient(command_socket)

    await client.do("command")

    return client


def command_to_str(command: str | int | float | bool | Enum):
    """
    Converts a data type to a string that can be sent to the robot.
    """

    match command:
        case str():
            return command
        case bool():
            return "on" if command else "off"
        case int() | float():
            return str(command)
        case Enum():
            if isinstance(command.value, str) or isinstance(command.value, int) or isinstance(command.value, float) \
                or isinstance(command.value, bool) or isinstance(command.value, Enum):
                return command_to_str(command.value)
            else:
                raise Exception("Invalid enum type")


class RoboMasterClient:
    line: Feed[Line]
    """
    A feed of line recognition data.

    Line recognition has to be enabled first with `set_line_recognition_enabled` and
    the line colour has to be set with `set_line_recognition_colour`.
    """

    position: Feed[ChassisPosition]
    """
    A feed of the robot's position.

    This has to be enabled first with `set_chassis_position_push_rate`.
    """

    attitude: Feed[ChassisAttitude]
    """
    A feed of the robot's attitude.

    This has to be enabled first with `set_chassis_attitude_push_rate`.
    """

    status: Feed[ChassisStatus]
    """
    A feed of the robot's status.

    This has to be enabled first with `set_chassis_status_push_rate`.
    """

    _conn: tuple[asyncio.StreamReader, asyncio.StreamWriter]
    _command_lock: asyncio.Lock
    _push_receiver: PushReceiver
    _handle_push_task: asyncio.Task
    _exiting: bool

    def __init__(self, command_conn: tuple[asyncio.StreamReader, asyncio.StreamWriter]) -> None:
        """
        This constructor shouldn't be used directly. Use `connect_to_robomaster` instead.
        """

        self.line = Feed()
        self.position = Feed()
        self.attitude = Feed()
        self.status = Feed()

        self._conn = command_conn
        self._command_lock = asyncio.Lock()
        self._push_receiver = PushReceiver(_PUSH_PORT)
        self._handle_push_task = asyncio.create_task(self._handle_push(self._push_receiver.feed))
        self._exiting = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.do("quit")

        self._exiting = True

        self._handle_push_task.cancel()
        self._conn[1].close()

    async def _handle_push(self, feed: Feed[Response]):
        async for response in feed:
            topic = response.data[0]
            subject = response.data[2]
            parseData = Response(response.data[3:])

            if topic == "chassis":
                if subject == "position": await self.position.feed(ChassisPosition.parse(parseData))
                elif subject == "attitude": await self.attitude.feed(ChassisAttitude.parse(parseData))
                elif subject == "status": await self.status.feed(ChassisStatus.parse(parseData))
                else: print(f"Unknown chassis subject: {subject}")
            elif topic == "AI":
                if subject == "line": await self.line.feed(Line.parse(parseData))
                else: print(f"Unknown AI subject: {subject}")
            else:
                print(f"Unknown topic: {topic}")

    async def _do(self, command: str):
        await self._command_lock.acquire()

        if self._exiting:
            raise Exception("Client is exiting.")

        self._conn[1].write(command.encode())
        await self._conn[1].drain()

        data = await self._conn[0].readuntil(b";")

        self._command_lock.release()

        return Response(data.decode()[:-1].split(" "))

    async def do(self, *commands: str | int | float | bool | Enum) -> Response:
        """
        Low level command sending. Every function that influences the robot's behaviour
        uses this internally.

        It's better to use the higher level functions instead of this.

        Arguments:
         - *commands: The commands to send to the robot. These can be strings, numbers, booleans or enums.
                      All of these will be converted to strings using `command_to_str`.
        """
        
        command = ' '.join(map(command_to_str, commands)) + ';'
        return await self._do(command)

    async def get_version(self) -> str:
        return (await self.do("version")).get_str(0)

    async def set_speed(self, forwards: float, right: float, clockwise: float) -> None:
        """
        Causes the robot to move with the given speeds indefinitely.

        Arguments:
         - forwards: The forwards speed in m/s
         - right: The right speed in m/s
         - clockwise: The clockwise speed in degrees/s
        """
        await self.do("chassis", "speed", "x", forwards, "y", right, "z", clockwise)

    async def set_wheel_speed(self, front_right: float, front_left: float, back_left: float, back_right: float) -> None:
        """
        All speeds are in rpm.
        """
        await self.do(
            "chassis", "wheel",
            "w1", front_right,
            "w2", front_left,
            "w3", back_left,
            "w4", back_right
        )

    async def get_wheel_speed(self) -> ChassisSpeed:
        """
        Returns:
         - The current wheel speeds in rpm.
        """
        return ChassisSpeed.parse(await self.do("chassis", "speed", "?"))

    async def move(self, forwards: float, right: float, clockwise: float,
                   speed: float | None = None, rotation_speed: float | None = None) -> None:
        """
        Moves the robot and rotates it. The robot rotates *as* it moves.
        
        **NOTE:** This does *not* wait until the robot has finished moving. Use `await asyncio.sleep` to manually wait.

        Arguments:
         - forwards: The distance forwards in metres
         - right: The distance right in metres
         - clockwise: The rotation in degrees
         - speed: The forwards and right speed in m/s. Leave as `None` to use the default.
         - rotation_speed: The rotation speed in degrees/s. Leave as `None` to use the default.
        """

        args = [
            "chassis", "move",
            "x", forwards,
            "y", right,
            "z", clockwise
        ]

        if speed is not None:
            args.append("vxy")
            args.append(speed)

        if rotation_speed is not None:
            args.append("vz")
            args.append(rotation_speed)

        await self.do(*args)

    async def get_position(self) -> ChassisPosition:
        return ChassisPosition.parse(await self.do("chassis", "position", "?"))
    
    async def get_attitude(self) -> ChassisAttitude:
        return ChassisAttitude.parse(await self.do("chassis", "attitude", "?"))
    
    async def get_status(self) -> ChassisStatus:
        return ChassisStatus.parse(await self.do("chassis", "status", "?"))

    async def set_chassis_position_push_rate(self, freq: int) -> None:
        """
        Sets the push rate of the chassis position in Hz. Set to `0` to disable.

        Allowed frequencies are 0, 1, 5, 10, 20, 30, 50.
        """

        if freq == 0:
            await self.do("chassis", "push", "position", False)
        else:
            await self.do("chassis", "push", "position", True, "pfreq", freq)

    async def set_chassis_attitude_push_rate(self, freq: int) -> None:
        """
        Sets the push rate of the chassis attitude in Hz. Set to `0` to disable.

        Allowed frequencies are 0, 1, 5, 10, 20, 30, 50.
        """

        if freq == 0:
            await self.do("chassis", "push", "attitude", False)
        else:
            await self.do("chassis", "push", "attitude", True, "afreq", freq)

    async def set_chassis_status_push_rate(self, freq: int) -> None:
        """
        Sets the push rate of the chassis status in Hz. Set to `0` to disable.

        Allowed frequencies are 0, 1, 5, 10, 20, 30, 50.
        """

        if freq == 0:
            await self.do("chassis", "push", "status", False)
        else:
            await self.do("chassis", "push", "status", True, "sfreq", freq)

    async def set_ir_enabled(self, enabled: bool = True) -> None:
        await self.do("ir_distance_sensor", "measure", enabled)
    
    async def get_ir_distance(self, ir_id: int) -> float:
        """
        The IR sensor has to be enabled first with `set_ir_enabled`.

        Arguments:
         - ir_id: The ID of the IR sensor. There appears to be only one IR sensor, so this should always be `1`.
        
        Returns:
         - The distance in millimetres.
        """
        return (await self.do("ir_distance_sensor", "distance", ir_id, "?")).get_float(0)
    
    async def move_arm(self, x_dist: float, y_dist: float) -> None:
        """
        Moves the robotic arm by the given distance. To move to a specific position,
        use `set_arm_position` instead.

        The units are unknown. Use `get_arm_position` to find positions to move to.
        """
        await self.do("robotic_arm", "move", "x", x_dist, "y", y_dist)
    
    async def set_arm_position(self, x: float, y: float) -> None:
        """
        Moves the robotic arm to the given position. To move relative to the current position,
        use `move_arm` instead.

        The units are unknown. Use `get_arm_position` to find positions want to move to.
        """
        await self.do("robotic_arm", "moveto", "x", x, "y", y)
    
    async def get_arm_position(self) -> tuple[float, float]:
        """
        Returns:
         - The current position of the robotic arm in unknown units. The format is `(x, y)`.
        """

        response = await self.do("robotic_arm", "position", "?")
        return (response.get_float(0), response.get_float(1))
    
    # TODO Allow different levels of force when opening?
    # https://robomaster-dev.readthedocs.io/en/latest/text_sdk/protocol_api.html#mechanical-gripper-opening-control
    async def open_gripper(self) -> None:
        await self.do("robotic_gripper", "open", 1)
    
    # TODO Allow different levels of force when closing?
    # https://robomaster-dev.readthedocs.io/en/latest/text_sdk/protocol_api.html#mechanical-gripper-opening-control
    async def close_gripper(self) -> None:
        """
        This closes the gripper until it encounters any resistance. If there is an object in
        the way, the gripper will close until it is tightly gripping the object, but it will
        not damage itself.
        """
        await self.do("robotic_gripper", "close", 1)

    async def get_gripper_status(self) -> GripperStatus:
        return (await self.do("robotic_gripper", "status", "?")).get_enum(0, GripperStatus)

    async def set_line_recognition_colour(self, colour: LineColour) -> None:
        await self.do("AI", "attribute", "line_color", colour)

    async def set_line_recognition_enabled(self, enabled: bool = True) -> None:
        await self.do("AI", "push", "line", enabled)
