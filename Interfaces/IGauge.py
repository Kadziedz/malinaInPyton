from abc import ABC, abstractmethod
from datetime import datetime


class IGauge(ABC):

    @abstractmethod
    def getDevices(self) -> list:
        pass

    @abstractmethod
    def measure(self, key=None):
        pass
