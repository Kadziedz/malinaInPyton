from Models.Serializable import Serializable
from Models.Thermometer import Thermometer


class ObjectState(Serializable):
    def __init__(self):
        super().__init__()
        self.LowerSensorTemp: float = 0
        self.HigherSensorTemp: float = 0
        self.AmbientSensorTemp: float = 0
        self.LowerTempSensor: str = ""
        self.AmbientTempSensor: str = ""
        self.HigherTempSensor: str = ""
        self.IsRelayOn: bool = False
        self.IsAutoMode = False
        self.Device = list()

    def __ne__(self, __value) -> bool:
        return self.LowerSensorTemp != __value.LowerSensorTemp or \
            self.HigherSensorTemp != __value.HigherSensorTemp or \
            self.AmbientSensorTemp != __value.AmbientSensorTemp or \
            self.LowerTempSensor != __value.LowerTempSensor or \
            self.AmbientTempSensor != __value.AmbientTempSensor or \
            self.HigherTempSensor != __value.HigherTempSensor or \
            self.IsRelayOn != __value.IsRelayOn or \
            self.IsAutoMode != __value.IsAutoMode or\
            not self.__isDevicesEqual(__value)
        
    def __isDevicesEqual(self, __value) -> bool:
        if len(self.Device) != len(__value.Device):
            return False
        for item in self.Device:
            if item not in __value.Device:
                return False
        return True
    
    def toDictionary(self):
        document = dict()
        document["LowerSensorTemp"] = self.LowerSensorTemp
        document["HigherSensorTemp"] = self.HigherSensorTemp
        document["AmbientSensorTemp"] = self.AmbientSensorTemp
        document["LowerTempSensor"] = self.LowerTempSensor
        document["AmbientTempSensor"] = self.AmbientTempSensor
        document["HigherTempSensor"] = self.HigherTempSensor
        document["IsAutoMode"] = self.IsAutoMode
        document["IsRelayOn"] = self.IsRelayOn
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
            self.IsRelayOn = src.IsRelayOn
            self.Device = [item.copy() for item in src.Device]
        elif isinstance(src, dict):
            self.LowerSensorTemp: float = src["LowerSensorTemp"]
            self.HigherSensorTemp: float = src["HigherSensorTemp"]
            self.AmbientSensorTemp: float = src["AmbientSensorTemp"]
            self.LowerTempSensor: str = src["LowerTempSensor"]
            self.AmbientTempSensor: str = src["AmbientTempSensor"]
            self.HigherTempSensor: str = src["HigherTempSensor"]
            self.IsAutoMode: bool = bool(src["IsAutoMode"])
            self.IsRelayOn: bool = bool(src["IsRelayOn"])
            self.Device: list = [Thermometer(item["Name"], item["Temperature"]) for item in src["Device"]]
        self.LowerSensorTemp = -999 if self.LowerSensorTemp is None else src.LowerSensorTemp
        self.HigherSensorTemp = -999 if self.HigherSensorTemp is None else src.HigherSensorTemp
        self.AmbientSensorTemp = -999 if self.AmbientSensorTemp is None else src.AmbientSensorTemp
