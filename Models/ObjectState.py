from Models.Serializable import Serializable
from Models.Thermometer import Thermometer


class ObjectState(Serializable):
    def __init__(self):
        self.LowerSensorTemp: float = 0
        self.HigherSensorTemp: float = 0
        self.AmbientSensorTemp: float = 0
        self.LowerTempSensor: str = ""
        self.AmbientTempSensor: str = ""
        self.HigherTempSensor: str = ""
        self.IsRelayOn: bool = False
        self.IsAutoMode = False
        self.Device = list()

    def toDictionary(self):
        document = dict()
        document["LowerSensorTemp"] = self.LowerSensorTemp
        document["HigherSensorTemp"] = self.HigherSensorTemp
        document["AmbientSensorTemp"] = self.AmbientSensorTemp
        document["LowerTempSensor"] = self.LowerTempSensor
        document["AmbientTempSensor"] = self.AmbientTempSensor
        document["HigherTempSensor"] = self.HigherTempSensor
        document["IsAutoMode"] = self.IsAutoMode
        document["Device"] = [item.toDictionary() for item in self.Device]

        return document

    def update(self, src):
        if isinstance(src, ObjectState):
            self.LowerSensorTemp = src.LowerSensorTemp
            self.HigherSensorTemp = src.HigherSensorTemp
            self.AmbientSensorTemp = src.AmbientSensorTemp
            self.LowerTempSensor = src.LowerTempSensor
            self.AmbientTempSensor = src.AmbientTempSensor
            self.HigherTempSensor = src.HigherTempSensor
            self.IsAutoMode = src.IsAutoMode
            self.Device = [item.copy() for item in src.Device]
        elif isinstance(src, dict):
            self.LowerSensorTemp: float = src["LowerSensorTemp"]
            self.HigherSensorTemp: float = src["HigherSensorTemp"]
            self.AmbientSensorTemp: float = src["AmbientSensorTemp"]
            self.LowerTempSensor: str = src["LowerTempSensor"]
            self.AmbientTempSensor: str = src["AmbientTempSensor"]
            self.HigherTempSensor: str = src["HigherTempSensor"]
            self.IsAutoMode: bool = bool(src["IsAutoMode"])
            self.Device: list = [Thermometer(item["Name"], item["Temperature"]) for item in src["Device"]]
