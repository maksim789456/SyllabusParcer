from dataclasses import dataclass
from enum import Enum


class HourType(Enum):
    Lecture = "Лекция"
    PracticalWork = "Практ. работа"


@dataclass()
class TopicHour:
    selection: str
    topic: str
    content: str
    homework: str
    countHours: int
    hourType: HourType

    def __int__(self):
        self.countHours = 1
        self.hourType = HourType.Lecture
