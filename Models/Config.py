from dataclasses import dataclass
from Models.Settings import Settings
import json
import sys
from Models.Serializable import Serializable

@dataclass
class ConnectionString(Serializable):
    User = ''
    Password = ''
    Host = ''
    Database = ''

    def __init__(self, src) -> None:
        super().__init__()
        self.update(src)

    def update(self, src):
        if isinstance(src, ConnectionString):
            self.User = src.User
            self.Password = src.Password
            self.Host = src.Host
            self.Database = src.Database
        elif isinstance(src, dict):
            self.User = src["User"]
            self.Password = src["Password"]
            self.Host = src["Host"]
            self.Database = src["Database"]
            
    def toDictionary(self):
        return { "User": self.User, "Password" : self.Password, "Host": self.Host, "Database": self.Database}        


class Config(Settings):
    def __init__(self, configFileName='config.json') -> None:
        configDict = Config.getConfigDictionary(configFileName)
        super().update(configDict["Settings"])
        self.ConnectionStrings: dict = {item:  ConnectionString(configDict["ConnectionStrings"][item]) for item in configDict["ConnectionStrings"]}
        self.LogLevel = configDict["Logging"]["LogLevel"]

    def getSettings(self) -> Settings:
        settings = Settings()
        settings.update(self)

        return settings

    def toDictionary(self):
        settings = dict()
        settings["LowerTempSensor"] = self.LowerTempSensor
        settings["HigherTempSensor"] = self.HigherTempSensor
        settings["AmbientTempSensor"] = self.AmbientTempSensor
        settings["MinimumTempDiff"] = self.MinimumTempDiff
        settings["IsAuto"] = self.IsAuto
        settings["DayStart"] = self.DayStart
        settings["DayStop"] = self.DayStop
        settings["DecisionDelay"] = self.DecisionDelay
        settings["MeasurementSamplesCount"] = self.MeasurementSamplesCount
        settings["MaxStateTime"] = self.MaxStateTime
        settings["ControlInterval"] = self.ControlInterval
        settings["DataSaveInterval"] = self.DataSaveInterval
        settings["MinimumAmbientTemp"] = self.MinimumAmbientTemp
        settings["LowerTempSensorOffset"] = self.LowerTempSensorOffset
        settings["HigherTempSensorOffset"] = self.HigherTempSensorOffset
        settings["AmbientTempSensorOffset"] = self.AmbientTempSensorOffset

        return {"Settings": settings, "ConnectionStrings": {item: self.ConnectionStrings[item].toDictionary()  for item in  self.ConnectionStrings}, "Logging": {"LogLevel": self.LogLevel}}

    def getConfig(configFileName: str = 'config.json'):
        return Config(configFileName)

    def getConfigDictionary(configFileName: str = 'config.json') -> dict:
        fileName = configFileName
        if Config.isDebug():
            fileName = 'local.' + configFileName
        with open(fileName, 'r') as jsonFile:
            return json.load(jsonFile)

    def isDebug():
        gettrace = getattr(sys, 'gettrace', None)
        if gettrace is None:
            return False
        elif gettrace():
            return True
        else:
            return False
