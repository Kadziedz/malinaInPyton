from abc import ABC, abstractmethod


class IMeasurementFilter(ABC):

    @abstractmethod
    def updateMeasurements(self, key: str, val: float, tailLen: int) -> None:
        pass

    @abstractmethod
    def Get(self, key: str) -> float:
        pass
