from abc import ABC, abstractmethod


class IRelay(ABC):

    @abstractmethod
    def get(self) -> bool:
        pass

    @abstractmethod
    def set(self, value: bool) -> None:
        pass
