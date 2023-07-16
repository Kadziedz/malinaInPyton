from datetime import datetime


class Measurements:
    def __init__(self, data:dict, isWorking:bool, timeStamp:datetime) -> None:
        self.data:dict=data.copy()
        self.isWorking:bool = isWorking
        self.eventTimestamp:datetime = timeStamp