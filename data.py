from enum import Enum
from dataclasses import dataclass
from typing import TypeVar

DIRECT_CONNECT_IP = "192.168.2.1"

VIDEO_PORT = 40921
AUDIO_PORT = 40922
CONTROL_PORT = 40923
PUSH_PORT = 40924
EVENT_PORT = 40925
IP_PORT = 40926


def command_to_str(command: str | int | float | bool | Enum):
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


class Mode(Enum):
    ChassisLead = "chassis_lead"
    GimbalLead = "gimbal_lead"
    Free = "free"


class GripperStatus(Enum):
    Closed = "0"
    PartiallyOpen = "1"
    Open = "2"


class LineType(Enum):
    NoLine = "0"
    Straight = "1"
    Fork = "2"
    Intersection = "3"


class LineColour(Enum):
    Red = "red"
    Blue = "blue"
    Green = "green"


@dataclass
class Response:
    data: list[str]

    def get_str(self, index: int):
        return self.data[index]
    
    def get_int(self, index: int):
        return int(self.data[index])

    def get_float(self, index: int):
        return float(self.data[index])
    
    def get_bool(self, index: int):
        if self.data[index] == "on":
            return True
        elif self.data[index] == "off":
            return False
        else:
            raise Exception("Invalid bool value")
    
    GetEnumT = TypeVar("GetEnumT", bound=Enum)
    def get_enum(self, index: int, enum: type[GetEnumT]):
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
    def parse(data: Response):
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
    def parse(data: Response):
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
    def parse(data: Response):
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
    def parse(data: Response):
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
    def parse(data: Response):
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

        points = []

        for i in range(point_count):
            points.append(Point(
                x         = data.get_float(i * 4 + 1),
                y         = data.get_float(i * 4 + 2),
                tangent   = data.get_float(i * 4 + 3),
                curvature = data.get_float(i * 4 + 4)
            ))

        return Line(line_type, points)
