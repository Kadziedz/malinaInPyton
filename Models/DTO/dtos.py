
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DataPoint:
    EventTimeStamp: datetime = None
    Value: float = 0
    DayIndx: int = 0
    IsWorking: bool = False
    DeviceID: int = 0


@dataclass
class Device:
    Id: int = 0
    Name: str = None
    DataPoints: list = field(default_factory=lambda: list())


@dataclass
class ControlEvent:
    EventTimestamp: datetime = None
    Status: int = 0
    DayIndx: int = 0
