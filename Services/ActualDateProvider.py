from datetime import datetime
from Interfaces.IActualDateProvider import IActualDateProvider


class ActualDateProvider(IActualDateProvider):
    
    def getActualDate(self) -> datetime:
        return datetime.now()
