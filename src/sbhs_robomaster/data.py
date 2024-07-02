from enum import Enum, IntFlag, auto
from dataclasses import dataclass
from typing import TypeVar


class Frequency(Enum):
    """"""
    Off = "0"
    Hz1 = "1"
    Hz5 = "5"
    Hz10 = "10"
    Hz20 = "20"
    Hz30 = "30"
    Hz50 = "50"


class Mode(Enum):
    """"""
    ChassisLead = "chassis_lead"
    GimbalLead = "gimbal_lead"
    Free = "free"


class GripperStatus(Enum):
    """"""
    Closed = "0"
    PartiallyOpen = "1"
    Open = "2"


class LineType(Enum):
    """"""
    NoLine = "0"
    Straight = "1"
    Fork = "2"
    Intersection = "3"


class LineColour(Enum):
    """"""
    Red = "red"
    Blue = "blue"
    Green = "green"


class LedPosition(IntFlag):
    """
    Use the flag combining operator (`|`) to combine multiple leds.

    ```py
    front_and_left_leds = LedPosition.Front | LedPosition.Left
    ```

    `LedPosition.All` is equivalent to `LedPosition.Front | LedPosition.Back | LedPosition.Left | LedPosition.Right`.
    It's just a lot faster to type.
    """
    Front = auto()
    Back = auto()
    Left = auto()
    Right = auto()
    All = Front | Back | Left | Right


class LedEffect(Enum):
    """"""
    Off = "off"
    Solid = "solid"
    Pulse = "pulse"
    Blink = "blink"
    Scrolling = "scrolling"


@dataclass
class Response:
    """
    Wrapper around the data returned by the robot.

    Provides convenience functions for getting the data in the correct type.
    """
    data: list[str]

    def get_str(self, index: int) -> str:
        return self.data[index]
    
    def get_int(self, index: int) -> int:
        return int(self.data[index])

    def get_float(self, index: int) -> float:
        return float(self.data[index])
    
    def get_bool(self, index: int) -> bool:
        if self.data[index] == "on":
            return True
        elif self.data[index] == "off":
            return False
        elif self.data[index] == "1":
            return True
        elif self.data[index] == "0":
            return False
        else:
            raise Exception("Invalid bool value")
    
    GetEnumT = TypeVar("GetEnumT", bound=Enum)
    def get_enum(self, index: int, enum: type[GetEnumT]) -> GetEnumT:
        """
        Example usage:
        ```py
        class MyEnum(Enum):
            A = "a"
            B = "b"
            C = "c"

        response = Response(["a", "b", "c"])

        response.get_enum(0, MyEnum) # MyEnum.A
        response.get_enum(1, MyEnum) # MyEnum.B
        response.get_enum(2, MyEnum) # MyEnum.C
        ```

        **NOTE:** This only works for enums that have strings as their underlying values.
        """
        return enum(self.data[index])


@dataclass
class WheelSpeed:
    """All speeds are in rpm."""

    front_right: float
    front_left: float
    back_right: float
    back_left: float


@dataclass
class ChassisSpeed:
    z: float
    """
    Movement forwards/backwards (relative to the rotation of the robot) in m/s.
    """
    
    x: float
    """
    Movement right/left (relative to the rotation of the robot) in m/s.
    """

    clockwise: float
    """
    Rotational speed around the vertical axis in the clockwise direction in degrees/s.
    """

    wheels: WheelSpeed

    @staticmethod
    def parse(data: Response) -> "ChassisSpeed":
        return ChassisSpeed(
            z         = data.get_float(0),
            x         = data.get_float(1),
            clockwise = data.get_float(2),
            wheels    = WheelSpeed(
                front_right = data.get_float(3),
                front_left  = data.get_float(4),
                back_right  = data.get_float(5),
                back_left   = data.get_float(6)
            )
        )


@dataclass
class ChassisRotation:
    """
    This actually parses the position data from the robot,
    but removes the x and z coordinates due to them being
    too inaccurate and being a major footgun.
    """

    clockwise: float
    """
    The rotation in degrees clockwise around the vertical axis,
    relative to the robot's starting orientation.
    """

    @staticmethod
    def parse(data: Response) -> "ChassisRotation":
        return ChassisRotation(
            clockwise = data.get_float(2)
        )


@dataclass
class ChassisAttitude:
    """All values are in degrees."""

    pitch: float
    roll: float
    yaw: float

    @staticmethod
    def parse(data: Response) -> "ChassisAttitude":
        return ChassisAttitude(
            pitch = data.get_float(0),
            roll  = data.get_float(1),
            yaw   = data.get_float(2)
        )


@dataclass
class ChassisStatus:
    static: bool
    up_hill: bool
    down_hill: bool
    on_slope: bool
    pick_up: bool
    slip: bool
    impact_x: bool
    impact_y: bool
    impact_z: bool
    roll_over: bool
    hill_static: bool

    @staticmethod
    def parse(data: Response) -> "ChassisStatus":
        return ChassisStatus(
            static      = data.get_bool(0),
            up_hill     = data.get_bool(1),
            down_hill   = data.get_bool(2),
            on_slope    = data.get_bool(3),
            pick_up     = data.get_bool(4),
            slip        = data.get_bool(5),
            impact_x    = data.get_bool(6),
            impact_y    = data.get_bool(7),
            impact_z    = data.get_bool(8),
            roll_over   = data.get_bool(9),
            hill_static = data.get_bool(10)
        )


@dataclass
class Point:
    x: float
    y: float
    tangent: float
    curvature: float


@dataclass
class Line:
    type: LineType
    points: list[Point]

    @staticmethod
    def parse(data: Response) -> "Line":
        point_count = (len(data.data) - 1) // 4

        match data.get_int(0):
            case 0:
                line_type = LineType.NoLine
            case 1:
                line_type = LineType.Straight
            case 2:
                line_type = LineType.Fork
            case 3:
                line_type = LineType.Intersection
            case _:
                raise Exception("Invalid line type")

        points: list[Point] = []

        for i in range(point_count):
            points.append(Point(
                x         = data.get_float(i * 4 + 1),
                y         = data.get_float(i * 4 + 2),
                tangent   = data.get_float(i * 4 + 3),
                curvature = data.get_float(i * 4 + 4)
            ))

        return Line(line_type, points)


@dataclass
class Colour:
    """All values are from 0 to 255, inclusive."""
    
    r: float
    g: float
    b: float