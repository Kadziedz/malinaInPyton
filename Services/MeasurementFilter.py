from Interfaces.IMeasurementFilter import IMeasurementFilter
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import deque, defaultdict
from threading import Lock
import logging


@dataclass(frozen=True)
class Measurement:
    dateTime: datetime
    value: float = 0


class MeasurementFilter(IMeasurementFilter):

    def __init__(self) -> None:
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self._sync = Lock()
        self._measurements = defaultdict()
        self._tailLen: int = 30
        self._lock = Lock()

    def updateMeasurements(self, key: str, val: float, tailLen: int) -> None:
        with self._lock:
            if not key in self._measurements:
                self._measurements[key] = deque()
            self._tailLen = tailLen
            self.removeOldMeasurements(key)

            self._measurements[key].append(Measurement(datetime.now(), val))

    def Get(self, key: str) -> float:

        with self._lock:
            self.removeOldMeasurements(key)
            if not key in self._measurements or len(self._measurements[key]) <= 0:
                return None
            return sum([point.value for point in self._measurements[key]])/len(self._measurements)

    def removeOldMeasurements(self, key: str):
        now = datetime.now()
        nowMinus10 = now + timedelta(minutes=-10)
        while key in self._measurements and len(self._measurements[key]) > 0 and self._measurements[key][-1].dateTime < nowMinus10:
            self._measurements[key].popleft()
