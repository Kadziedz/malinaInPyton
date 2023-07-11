from datetime import datetime
from Interfaces.IGauge import IGauge


class Gauge(IGauge):

    def __init__(self) -> None:
        super().__init__()
        self._sensors = Gauge.getDevices()

    @staticmethod
    def getDevices() -> list:
        return ["28-00000c05b380",
                "28-011935a9c96f", "28-011936392d0d"]

    def measure(self, key=None):
        if isinstance(key, str) and key != None:
            if not key in self._sensors:
                return None
            return self._read(key)

        if len(self._sensors) == 0:
            self._sensors = self.getDevices()

        return [self._read(sensor) for sensor in self._sensors]

    def _read(self, sensorName: str) -> float:
        return (datetime.now().microsecond % 10000) / 1000.0
