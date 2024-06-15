from enum import Enum
from types import TracebackType
from typing import Final, Optional, Type
import asyncio
from time import time
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
    await client.async_init()

    return client


def command_to_str(command: str | int | float | bool | Enum) -> str:
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

    rotation: Feed[ChassisRotation]
    """
    A feed of the robot's rotation.

    This has to be enabled first with `set_chassis_rotation_push_rate`.
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

    _line_enabled: bool
    _rotation_frequency: Frequency
    _attitude_frequency: Frequency
    _status_frequency: Frequency

    _conn: tuple[asyncio.StreamReader, asyncio.StreamWriter]
    _command_lock: asyncio.Lock
    _push_receiver: PushReceiver
    _handle_push_task: asyncio.Task[None]
    _exiting: bool

    def __init__(self, command_conn: tuple[asyncio.StreamReader, asyncio.StreamWriter]) -> None:
        """
        This constructor shouldn't be used directly. Use `connect_to_robomaster` instead.
        """

        self.line = Feed()
        self.rotation = Feed()
        self.attitude = Feed()
        self.status = Feed()

        self._line_enabled = False
        self._rotation_frequency = Frequency.Off
        self._attitude_frequency = Frequency.Off
        self._status_frequency = Frequency.Off

        self._conn = command_conn
        self._command_lock = asyncio.Lock()
        self._push_receiver = PushReceiver(_PUSH_PORT)
        self._handle_push_task = asyncio.create_task(self._handle_push(self._push_receiver.feed))
        self._exiting = False

    async def async_init(self):
        """
        Performs any asynchronous initialisation required. Should be called
        immediately after the class is constructed. `connect_to_robomaster`
        handles this automatically.
        """
        await self.do("command")

        await self.set_line_recognition_enabled(False)
        await self.set_rotation_push_rate(Frequency.Off)
        await self.set_attitude_push_rate(Frequency.Off)
        await self.set_status_push_rate(Frequency.Off)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type: Optional[Type[BaseException]], exc: Optional[BaseException], tb: Optional[TracebackType]):
        await self.do("quit")

        self._exiting = True

        self._handle_push_task.cancel()
        self._conn[1].close()

    async def _handle_push(self, feed: Feed[Response]):
        while True:
            response = await feed.get()

            topic = response.data[0]
            subject = response.data[2]
            parseData = Response(response.data[3:])

            if topic == "chassis":
                if subject == "position":   self.rotation.feed(ChassisRotation.parse(parseData))
                elif subject == "attitude": self.attitude.feed(ChassisAttitude.parse(parseData))
                elif subject == "status":   self.status.feed(ChassisStatus.parse(parseData))
                else:                       print(f"Unknown chassis subject: {subject}")
            elif topic == "AI":
                if subject == "line": self.line.feed(Line.parse(parseData))
                else:                 print(f"Unknown AI subject: {subject}")
            else:
                print(f"Unknown topic: {topic}")

    async def _do(self, command: str):
        async with self._command_lock:
            if self._exiting:
                raise Exception("Client is exiting.")

            self._conn[1].write(command.encode())
            await self._conn[1].drain()

            data = await self._conn[0].readuntil(b";")

            return Response(data.decode()[:-1].split(" "))

    async def do(self, *command_data: str | int | float | bool | Enum) -> Response:
        """
        Low level command sending. Every function that influences the robot's behaviour
        uses this internally.

        It's better to use the higher level functions instead of this.

        Arguments:
         - *command_data: The parts of the command to send to the robot. These can be strings, numbers, booleans or enums.
                          All of these will be converted to strings using `command_to_str`.
        """
        
        command = ' '.join(map(command_to_str, command_data)) + ';'
        return await self._do(command)

    async def get_version(self) -> str:
        return (await self.do("version")).get_str(0)

    async def set_speed(self, forwards: float, right: float, clockwise: float = 0) -> None:
        """
        Causes the robot to move with the given speeds indefinitely.

        Arguments:
         - forwards: The forwards speed in m/s
         - right: The right speed in m/s
         - clockwise: The rotational speed in degrees/s clockwise
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

    async def set_left_right_wheel_speeds(self, left: float, right: float) -> None:
        """
        All speeds are in rpm.
        """
        await self.set_wheel_speed(right, left, left, right)

    async def set_all_wheel_speeds(self, speed: float) -> None:
        """
        All speeds are in rpm.
        """
        await self.set_wheel_speed(speed, speed, speed, speed)

    async def get_speed(self) -> ChassisSpeed:
        return ChassisSpeed.parse(await self.do("chassis", "speed", "?"))

    async def rotate(self, clockwise: float, rotation_speed: float | None = None, timeout: float = 10) -> None:
        """
        **NOTE:** This function constantly polls the robot for its rotation and
        may starve out other areas in the program trying to send messages to
        the robot. In general, due to the serial nature of the communication
        protocol, any communication with the robot should not be largely
        parallel.

        Arguments:
         - clockwise: The degrees clockwise to rotate.
         - rotation_speed: The speed to rotate, in degrees/s. (Must be positive.)
         - timeout: How long to wait for the turn to finish (in seconds).
        """

        args = [
            "chassis", "move",
            "x", 0,
            "y", 0,
            "z", clockwise
        ]

        if rotation_speed is not None:
            args.append("vz")
            args.append(rotation_speed)

        await self.do(*args)

        start_time = time()
        while time() - start_time > timeout:
            status = await self.get_status()

            if status.static:
                return
            
            await asyncio.sleep(0.02) # 50Hz
            
        raise TimeoutError()

    async def get_rotation(self) -> ChassisRotation:
        return ChassisRotation.parse(await self.do("chassis", "position", "?"))
    
    async def get_attitude(self) -> ChassisAttitude:
        return ChassisAttitude.parse(await self.do("chassis", "attitude", "?"))
    
    async def get_status(self) -> ChassisStatus:
        return ChassisStatus.parse(await self.do("chassis", "status", "?"))

    async def set_rotation_push_rate(self, freq: Frequency) -> None:
        """
        Sets the push rate of the chassis rotation in Hz. Use `Frequency.Off` to disable.
        """

        # This sets the "position" push frequency because
        # that is where the rotation is stored.
        if freq == Frequency.Off:
            await self.do("chassis", "push", "position", False)
        else:
            await self.do("chassis", "push", "position", True, "pfreq", freq)

        self._rotation_frequency = freq

    def get_rotation_push_rate(self) -> Frequency:
        """
        Gets the push rate of the chassis rotation in Hz. `Frequency.Off` means it is disabled.
        """
        return self._rotation_frequency

    async def set_attitude_push_rate(self, freq: Frequency) -> None:
        """
        Sets the push rate of the chassis attitude in Hz. Use `Frequency.Off` to disable.
        """

        if freq == Frequency.Off:
            await self.do("chassis", "push", "attitude", False)
        else:
            await self.do("chassis", "push", "attitude", True, "afreq", freq)

        self._attitude_frequency = freq

    def get_attitude_push_rate(self) -> Frequency:
        """
        Gets the push rate of the chassis rotation in Hz. `Frequency.Off` means it is disabled.
        """
        return self._attitude_frequency

    async def set_status_push_rate(self, freq: Frequency) -> None:
        """
        Sets the push rate of the chassis status in Hz. Use `Frequency.Off` to disable.
        """

        if freq == Frequency.Off:
            await self.do("chassis", "push", "status", False)
        else:
            await self.do("chassis", "push", "status", True, "sfreq", freq)

        self._status_frequency = freq

    def get_status_push_rate(self) -> Frequency:
        """
        Gets the push rate of the chassis rotation in Hz. `Frequency.Off` means it is disabled.
        """
        return self._status_frequency

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
        Moves the robotic arm by the given distance relative to its current position.
        To move to a specific position, use `set_arm_position` instead.

        The units are unknown. Physically move the arm around and record the results from
        `get_arm_position` to determine the desired inputs for this function.
        """
        await self.do("robotic_arm", "move", "x", x_dist, "y", y_dist)
    
    async def set_arm_position(self, x: float, y: float) -> None:
        """
        Moves the robotic arm to the given position. To move relative to the current position,
        use `move_arm` instead.

        The units are unknown. Physically move the arm to the desired position and then use
        `get_arm_position` to find the desired inputs for this function. The origin for the
        x and y values appears to be different for every robot, so values for one robot will
        not carry over to another.
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
        """
        Gets whether the gripper is Open, Closed, or Partially Open.
        """
        return (await self.do("robotic_gripper", "status", "?")).get_enum(0, GripperStatus)

    async def set_line_recognition_colour(self, colour: LineColour) -> None:
        await self.do("AI", "attribute", "line_color", colour)

    async def set_line_recognition_enabled(self, enabled: bool = True) -> None:
        await self.do("AI", "push", "line", enabled)

        self._line_enabled = enabled

    def get_line_recognition_enabled(self) -> bool:
        return self._line_enabled
