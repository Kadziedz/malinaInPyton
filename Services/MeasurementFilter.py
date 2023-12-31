from Interfaces.IActualDateProvider import IActualDateProvider
from Interfaces.IContainer import IContainer
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
    HISTORY_VALID_BOUNDARY: int = 10
    
    def __init__(self, ioc: IContainer = None) -> None:
        super().__init__()
        self._dateProvider: IActualDateProvider = ioc.getInstance(IActualDateProvider)
        self._logger = logging.getLogger(__name__)
        self._sync = Lock()
        self._measurements = defaultdict()
        self._tailLen: int = 30
        self._lock = Lock()

    def updateMeasurements(self, key: str, val: float, tailLen: int) -> None:
        with self._lock:
            if key not in self._measurements:
                self._measurements[key] = deque()
            self._tailLen = tailLen
            self.removeOldMeasurements(key)

            self._measurements[key].append(Measurement(self._dateProvider.getActualDate(), val))

    def get(self, key: str) -> float:

        with self._lock:
            self.removeOldMeasurements(key)
            if key not in self._measurements or len(self._measurements[key]) <= 0:
                return None
            return sum([point.value for point in self._measurements[key]])/len(self._measurements[key])

    def removeOldMeasurements(self, key: str):
        now: datetime = self._dateProvider.getActualDate()
        nowMinus10: datetime = now + timedelta(minutes=-MeasurementFilter.HISTORY_VALID_BOUNDARY)
        if key in self._measurements:
            while len(self._measurements[key]) > 0 and self._measurements[key][-1].dateTime < nowMinus10:
                self._measurements[key].popleft()
            while len(self._measurements[key]) > self._tailLen:
                self._measurements[key].popleft()
