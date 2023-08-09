from Models.Serializable import Serializable


class Settings(Serializable): 
    def __init__(self) -> None: 
        super().__init__()
        self.Id: int = 0
        self.LowerTempSensor:  str = "28-011936392d0d"
        self.HigherTempSensor:  str = "28-011935a9c96f"
        self.AmbientTempSensor:  str = "28-00000c05b380"
        self.MinimumTempDiff: int = 0
        self.IsAuto:  bool = False
        self.DayStart:  int = 0
        self.DayStop:  int = 0
        self.DecisionDelay:  int = 0
        self.MeasurementSamplesCount:  int = 0
        self.MaxStateTime:  int = 0
        self.ControlInterval:  int = 0
        self.DataSaveInterval:  int = 0
        self.MinimumAmbientTemp:  int = 0
        self.LowerTempSensorOffset:  int = 0
        self.HigherTempSensorOffset:  int = 0
        self.AmbientTempSensorOffset:  int = 0
     
    def update(self, src): 
        if isinstance(src, Settings): 
            self.LowerTempSensor = src.LowerTempSensor
            self.HigherTempSensor = src.HigherTempSensor
            self.AmbientTempSensor = src.AmbientTempSensor
            self.MinimumTempDiff = src.MinimumTempDiff 
            self.IsAuto = src.IsAuto 
            self.DayStart = src.DayStart
            self.DayStop = src.DayStop
            self.DecisionDelay = src.DecisionDelay
            self.MeasurementSamplesCount = src.MeasurementSamplesCount
            self.MaxStateTime = src.MaxStateTime
            self.ControlInterval = src.ControlInterval
            self.DataSaveInterval = src.DataSaveInterval
            self.MinimumAmbientTemp = src.MinimumAmbientTemp
            self.LowerTempSensorOffset = src.LowerTempSensorOffset
            self.HigherTempSensorOffset = src.HigherTempSensorOffset
            self.AmbientTempSensorOffset = src.AmbientTempSensorOffset
        elif isinstance(src, dict): 
            self.LowerTempSensor: str = src["LowerTempSensor"]
            self.HigherTempSensor: str = src["HigherTempSensor"]
            self.AmbientTempSensor: str = src["AmbientTempSensor"]
            self.MinimumTempDiff: int = src["MinimumTempDiff"]
            self.IsAuto: bool = bool(src["IsAuto"])
            self.DayStart: int = int(src["DayStart"])
            self.DayStop: int = int(src["DayStop"])
            self.DecisionDelay: int = int(src["DecisionDelay"])
            self.MeasurementSamplesCount: int = int(src["MeasurementSamplesCount"])
            self.MaxStateTime: int = int(src["MaxStateTime"])
            self.ControlInterval: int = src["ControlInterval"]
            self.DataSaveInterval: int = src["DataSaveInterval"]
            self.MinimumAmbientTemp: int = src["MinimumAmbientTemp"]
            self.LowerTempSensorOffset: int = src["LowerTempSensorOffset"]
            self.HigherTempSensorOffset: int = src["HigherTempSensorOffset"]
            self.AmbientTempSensorOffset: int = src["AmbientTempSensorOffset"]
        
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
        
        return settings
