from abc import ABC, abstractmethod
from datetime import datetime
class IActualDateProvider(ABC):
    
    @abstractmethod
    def GetActualDate(self) -> datetime:
        pass


