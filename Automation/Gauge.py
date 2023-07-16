import logging
from datetime import datetime
from Interfaces.ISensor import ISensor

class Gauge(ISensor):

    def __init__(self, deviceName:str) -> None:
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self._deviceName = deviceName

    @staticmethod
    def getDevices() -> dict:
        fakeDevices = ["28-00000eb84fe0",
                "28-011935a9c96f", "28-011936392d0d"]
        return {label:Gauge(label) for label in fakeDevices}

    def measure(self):
        return self._read(self._deviceName)
        
    def _read(self, sensorName:str) -> float:
        value = 19.0 + (datetime.now().microsecond % 10000) / 1000000.0
        self._logger.debug(f"temp[{sensorName}] = {value}")
        return value
