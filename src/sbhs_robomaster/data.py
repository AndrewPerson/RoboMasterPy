from enum import Enum
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
    front_right: float
    front_left: float
    back_right: float
    back_left: float


@dataclass
class ChassisSpeed:
    z: float
    x: float
    clockwise: float
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
class ChassisPosition:
    z: float
    x: float
    clockwise: float | None

    @staticmethod
    def parse(data: Response) -> "ChassisPosition":
        return ChassisPosition(
            z = data.get_float(0),
            x = data.get_float(1),
            clockwise = data.get_float(2) if len(data.data) == 3 else None
        )


@dataclass
class ChassisAttitude:
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
