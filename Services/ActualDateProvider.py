from datetime import datetime
from Interfaces.IActualDateProvider import IActualDateProvider


class ActualDateProvider(IActualDateProvider):
    
     def GetActualDate(self) -> datetime:
        return datetime.now()