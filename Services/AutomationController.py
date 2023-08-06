import datetime
import logging
import statistics
import math
import time
from typing import Any
from collections import defaultdict
from threading import Lock, Thread
from Interfaces.IContainer import IContainer
from Interfaces.IRelay import IRelay
from Interfaces.ISensor import ISensor
from Interfaces.IMeasurementFilter import IMeasurementFilter
from Interfaces.IMessageBus import IMessageBus
from Models.ObjectState import ObjectState
from Models.Settings import Settings
from Models.Thermometer import Thermometer
from Repository.DatabaseContext import DatabaseContext
from Services.MessageBus import MessageBus
from Models.Measurements import Measurements
from concurrent.futures import ThreadPoolExecutor

class AutomationController(Thread):
    LED_RED:str="RedLED"
    LED_GREEN:str="GreenLED"
    LED_YELLOW:str="YellowLED"
    LED_BLINKER:str="BlinkingLED"
    RELAY:str="Relay"
    EVENT_STATUS_UPDATE= __name__ + ".onStatusUpdate"
    
    def __init__(self, ioc:IContainer) -> None:
        super().__init__()
        self._executor = ThreadPoolExecutor(1)
        self._databaseContext:DatabaseContext = ioc.getInstance(DatabaseContext)
        self._messageBus: IMessageBus = ioc.getInstance(IMessageBus)
        self._meters:dict = ioc.getInstance("thermometers")
        self._coils:dict = ioc.getInstance("coils")
        self._filter: IMeasurementFilter = ioc.getInstance(IMeasurementFilter)
        self._lock: Lock = Lock()
        self.__isStopRequested: bool = False
        self._actualSettings:Settings = self._messageBus.getSettings()
        self._cmdAuto:bool= self._actualSettings.IsAuto
        self._cmdRun:bool= False
        self._isRun = False
        self._isAutoMode = False
        self._actualState:ObjectState
        self._devices: dict
        (self._devices, self._actualState) = AutomationController.__initializeDataStructures(self._actualSettings, [key for key in self._meters], self._messageBus, self._databaseContext)
        self._messageBus.updateStatus(self._actualState)
        self._logger:logging= logging.getLogger(__name__)
        self._messageBus.register(MessageBus.EVENT_NEW_COMMAND, self.onNewCommandReceived)
        self._messageBus.register(MessageBus.EVENT_SETTINGS_UPDATE, self.onNewSettings)
        # messageBusSingleton.register(MessageBus.EVENT_NEW_STATUS, self.onNewStatus)

    def __del__(self):
            self._messageBus.unregister(MessageBus.EVENT_NEW_COMMAND, self.onNewCommandReceived)
            self._messageBus.unregister(MessageBus.EVENT_SETTINGS_UPDATE, self.onNewSettings)
    
    @staticmethod
    def __initializeDataStructures(config:Settings, physicalDeviceNamesList:list, sb:IMessageBus, db:DatabaseContext)->tuple:
        locState=sb.getStatus()
        devices = db.synchronizeDevices(physicalDeviceNamesList)
        locState.Device = [Thermometer(devices[key].Name, None) for key in devices]
        locState.AmbientSensorTemp = None
        locState.LowerSensorTemp = None
        locState.HigherSensorTemp = None
        return (devices, AutomationController.__updateState(config, locState))

    @staticmethod
    def __updateState(config:Settings, status:ObjectState) ->ObjectState:
        status.AmbientTempSensor = config.AmbientTempSensor
        status.LowerTempSensor = config.LowerTempSensor
        status.HigherTempSensor = config.HigherTempSensor
        return status

    def requestStop(self):
        with self._lock:
            self.__isStopRequested = True

    def isStopRequested(self) -> bool:
        result: bool = False
        with self._lock:
            result = self.__isStopRequested
        return result

    def run(self) -> None:
        lastIteration:datetime.datetime = datetime.datetime.now()
        actualTime:datetime.datetime = datetime.datetime.now()
        lastUpdateSent:datetime.datetime = datetime.datetime.now() 
        localSettings:Settings = Settings()
        localStatus:ObjectState= ObjectState()
        lastDbWrite:datetime.datetime = datetime.datetime.now()
        measurements:dict = defaultdict()
        ledBlinker:IRelay= self._coils[AutomationController.LED_BLINKER]
        ledPumpActive:IRelay = self._coils[AutomationController.LED_RED]
        ledManualMode:IRelay = self._coils[AutomationController.LED_YELLOW]
        ledAutoMode:IRelay = self._coils[AutomationController.LED_GREEN]
        relay:IRelay= self._coils[AutomationController.RELAY]
        workStart:datetime= actualTime
        workStop:datetime= actualTime
        lasControlTime:datetime = actualTime
        lowerTemp = self._filter.get(localSettings.LowerTempSensor)
        higherTemp = self._filter.get(localSettings.HigherTempSensor)
        ambientTemp = self._filter.get(localSettings.AmbientTempSensor)
        
        future = None
        relay.set(self._isRun)
        if self._isAutoMode:
            ledAutoMode.set(True)
            ledManualMode.set(False)
        else:
            ledAutoMode.set(False)
            ledManualMode.set(True)
        relay.set(self._isRun)
        ledPumpActive.set(self._isRun)
        oldDayIndx:int=0
        flipFlop:bool= False
        while not self.isStopRequested():

            actualTime = datetime.datetime.now()
            delta:datetime.timedelta = actualTime - lastIteration
            locCmdRun:bool=False
            locCmdAuto:bool=False
            
            with self._lock:
                localSettings.update(self._actualSettings)
                localStatus.update(self._actualState)
                locCmdRun = self._cmdRun
                locCmdAuto= self._cmdAuto
                
            #read temperatures in parallel
            if delta.total_seconds() >= min([4, (localSettings.DataSaveInterval >> 1)]) and future == None :
                self._logger.info(f"\nAUTO: {ledAutoMode.get()}\tMAN: {ledManualMode.get()}\trelay: {relay.get()}\tled: {ledPumpActive.get()}\n")
                lastIteration = actualTime
                future = self._executor.submit(AutomationController.__dirtyTemperaturesRead, (self._meters))
            
            delta = actualTime - lastUpdateSent
            if delta.total_seconds()>0.5:
                lastUpdateSent = actualTime
                flipFlop = not flipFlop
                ledBlinker.set(flipFlop)
                #self._logger.warn(f"lowerTemp = {lowerTemp},\thigherTemp = {higherTemp},\tambientTemp = {ambientTemp}")
                self._messageBus.sendNamedEvent(AutomationController.EVENT_STATUS_UPDATE, localStatus.toDictionary())
                
            #consume new temperatures
            if future != None and future.done():
                measurements.clear()
                localMeasurements = AutomationController.__filterTemperaturesAndAddOffsets(future.result(), self._filter, localSettings, self._logger)
                AutomationController.__updateLocalStatusTemperatures(localMeasurements, localStatus, self._logger)
                measurements.update(localMeasurements)
                self._logger.info(str(measurements))
                future = None
                    
            #store measurements in the database
            delta = actualTime - lastDbWrite
            if  len(measurements)>0  and \
                ( delta.total_seconds()> localSettings.DataSaveInterval and actualTime.hour >= localSettings.DayStart and actualTime.hour< localSettings.DayStop) \
                or \
                ( delta.total_seconds()> localSettings.DataSaveInterval * 5 and (actualTime.hour < localSettings.DayStart or actualTime.hour>= localSettings.DayStop)):
                oldDayIndx = self.__storeDataPoints(oldDayIndx, actualTime, measurements.copy())
                lastDbWrite = actualTime
              
            #automatic control iteration
            delta= actualTime - lasControlTime
            lowerTemp = self._filter.get(localSettings.LowerTempSensor)
            higherTemp = self._filter.get(localSettings.HigherTempSensor)
            ambientTemp = self._filter.get(localSettings.AmbientTempSensor)
            
            if self._isAutoMode and delta.total_seconds() >= localSettings.ControlInterval and actualTime.hour >= localSettings.DayStart and actualTime.hour < localSettings.DayStop and not (lowerTemp is None or higherTemp is None or ambientTemp is None):
                lasControlTime = actualTime
                    
                if self._isRun:
                    activityTime:datetime.timedelta = actualTime  - workStart
                    if activityTime.total_seconds() > localSettings.DecisionDelay * 60 and lowerTemp + localSettings.MinimumTempDiff > higherTemp:
                        self._logger.warning(f"{lowerTemp} + {localSettings.MinimumTempDiff} > {higherTemp} temperature too low, decision: turn off")
                        locCmdRun = False 
                        
                maxInactivityTime = localSettings.MaxStateTime
                
                
                if localSettings.HigherTempSensor in self._devices and localSettings.LowerTempSensor in self._devices:
                    dayIndx:int = actualTime.year * 10000 + actualTime.month * 100 + actualTime.day
                    idHigher:int = self._devices[localSettings.HigherTempSensor].Id
                    idLower:int = self._devices[localSettings.LowerTempSensor].Id
                    samplesCount:int = self._databaseContext.getPointsQuantity(dayIndx, idHigher)
                    if samplesCount>0:
                        pts1:int = self._databaseContext.getPoints(dayIndx, idHigher, localSettings.MaxStateTime * 2)
                        pts2:int = self._databaseContext.getPoints(dayIndx, idLower, localSettings.MaxStateTime * 2)
                        data:list= list()
                        for key in pts1:
                            if key in pts2:
                                data.append(pts1[key].Value - pts2[key].Value)
                        medianT:float = 0
                        if len(data)>1:
                            medianT = statistics.median(data)
                        if localSettings.MinimumTempDiff <medianT:
                            maxInactivityTime = localSettings.DecisionDelay + (localSettings.MaxStateTime -  localSettings.DecisionDelay) * math.exp( - (medianT -  localSettings.MinimumTempDiff) / 2.0 )
                
                delta = actualTime - workStop
                if not self._isRun and ambientTemp > localSettings.MinimumAmbientTemp  and delta.total_seconds() > maxInactivityTime * 60:
                    if maxInactivityTime != localSettings.MaxStateTime:
                        self._logger.warning(f"avg temp diff {medianT}, waiting time was reduced to {maxInactivityTime}, measure temp request: decision turn on")
                    else:
                        self._logger.warning(f"avg temp diff {medianT}, waiting time is {maxInactivityTime}, measure temp request: decision turn on")
                    locCmdRun = True
                
                delta = actualTime - workStart    
                if self._isRun and delta.total_seconds() > localSettings.MaxStateTime * 60:
                    self._logger.warning("working too long, decision: turn off")
                    locCmdRun= False
            #end if self._isAutoMode and delta.total_seconds() >= localSettings.ControlInterval and actualTime.hour >= localSettings.DayStart and actualTime.hour <= localSettings.DayStop:         
            
            # ignore command, out of working hours in auto mode 
            if (self._isRun or locCmdRun) and (self._isAutoMode or locCmdAuto) and (actualTime.hour < localSettings.DayStart or actualTime.hour>= localSettings.DayStop):
                locCmdRun= False
                
            
            with self._lock:
                if self._isAutoMode :
                    self._cmdRun = locCmdRun
            
            #act
            # change work mode
            if locCmdAuto != self._isAutoMode :
                self._isAutoMode = locCmdAuto
                if self._isAutoMode:
                    self._logger.warning("work mode AUTO")
                    ledManualMode.set(False)
                    ledAutoMode.set(True)
                else:
                    self._logger.warning("work mode MAN")
                    ledManualMode.set(True)
                    ledAutoMode.set(False)
                localSettings.IsAuto = locCmdAuto
                localStatus.IsAutoMode = self._isAutoMode
                localStatus.IsRelayOn = self._isRun
                self._messageBus.updateSettings(localSettings)
                
            # start/stop pump
            if locCmdRun != self._isRun :
                self._isRun= locCmdRun
                relay.set(self._isRun)
                if self._isRun :
                    workStart= actualTime
                else:
                    workStop= actualTime
                localStatus.IsRelayOn = locCmdRun
                self._messageBus.sendEvent(Measurements(measurements, self._isRun, actualTime))
                ledPumpActive.set(self._isRun)
                
            with self._lock:
                if self._actualState != localStatus:
                    self._actualState.update(localStatus)
                    self._messageBus.updateStatus(localStatus)

            time.sleep(0.3)
          
    def __storeDataPoints(self, oldDayIndx:int, actualTime:datetime.datetime, measurements:dict)->int:
        self._messageBus.sendEvent(Measurements(measurements.copy(), self._isRun, actualTime))
        self._logger.info(f"store to db requested {actualTime}\t{self._isRun}\t{str(measurements)}")
        twoDaysPast:datetime.datetime = actualTime - datetime.timedelta(days=2)
        dayIndx = twoDaysPast.year * 10000 + twoDaysPast.month * 100 + twoDaysPast.day
        if oldDayIndx!= dayIndx:
            oldDayIndx = dayIndx
            self._logger.info(f"delete old data request")
            self._messageBus.sendNamedEvent(MessageBus.EVENT_DELETE_OLD_DATA, oldDayIndx)
        return oldDayIndx

    @staticmethod
    def __dirtyTemperaturesRead(devices:dict)->dict:
        measurements:dict = defaultdict()
        for label in devices:
            sensor:ISensor = devices[label]
            temperature:float = sensor.measure()
            measurements[label] = temperature
        return measurements
    
    @staticmethod 
    def __filterTemperaturesAndAddOffsets(measurements:dict, filter:IMeasurementFilter, localSettings:Settings, logger:logging)->dict:
        for label in measurements:
            temperature:float = measurements[label]
            filteredTemp:float = 999
            if temperature == None:
                logger.warning(f"failed to get temperature for {label}")
            else:
                temperature = AutomationController.__addOffsets(temperature, label, localSettings)
                filter.updateMeasurements(label, temperature, localSettings.MeasurementSamplesCount)
                filteredTemp = filter.get(label)
                logger.debug(f"filtered temperature [{label}] = {filteredTemp}")
            measurements[label] = filteredTemp
                
        return measurements
     
    @staticmethod 
    def __updateLocalStatusTemperatures(measurements:dict, localStatus:ObjectState,logger:logging)->ObjectState:
        thermometers:dict = {device.Name: device for device in localStatus.Device }
        for label in measurements:
            filteredTemp:float = measurements[label]
            if filteredTemp != 999 and filteredTemp!= None:
                if label in thermometers:
                    thermometers[label].Temperature = filteredTemp
                else:
                    localStatus.Device.append(Thermometer(label, filteredTemp))
        if localStatus.AmbientTempSensor in thermometers:
            localStatus.AmbientSensorTemp = thermometers[localStatus.AmbientTempSensor].Temperature
            logger.info(f"Ambient temperature sensor [{localStatus.AmbientTempSensor}] = {localStatus.AmbientSensorTemp}")
        if localStatus.HigherTempSensor in thermometers:
            localStatus.HigherSensorTemp = thermometers[localStatus.HigherTempSensor].Temperature
            logger.info(f"High temperature sensor [{localStatus.HigherTempSensor}] = {localStatus.HigherSensorTemp }")
        if localStatus.LowerTempSensor in thermometers:
            localStatus.LowerSensorTemp = thermometers[localStatus.LowerTempSensor].Temperature
            logger.info(f"Low temperature sensor [{localStatus.LowerTempSensor}] = {localStatus.LowerSensorTemp }")

        return localStatus
                
    @staticmethod
    def __addOffsets(value:float, deviceName:str,  config:Settings)->None:
        if value == None:
            return None
        if deviceName == config.AmbientTempSensor:
            return value + config.AmbientTempSensorOffset
        if deviceName == config.LowerTempSensor:
            return value + config.LowerTempSensorOffset
        if deviceName == config.HigherTempSensor:
            return value+ config.HigherTempSensorOffset
        return value


    def onNewCommandReceived(self, command: str) -> bool:
        capitalizedCommand = command.upper()
        self._logger.info(capitalizedCommand+" command received")
        with self._lock:
            if capitalizedCommand == "AUTO":
                self._cmdAuto=True
                return True
            elif capitalizedCommand == "MAN":
                self._cmdAuto=False
                return True
            elif capitalizedCommand == "ON":
                if not self._isAutoMode:
                    self._cmdRun=True
                    return True
            elif capitalizedCommand == "OFF":
                if not self._isAutoMode:
                    self._cmdRun=False
                    return True
        return False

    def onNewSettings(self, newSettings: Settings) -> None:
        with self._lock:
            self._actualSettings.update(newSettings)
            AutomationController.__updateState(self._actualSettings, self._actualState)
            self._cmdAuto = self._actualSettings.IsAuto
        self._logger.info(f"settings update to {self._actualSettings.toJson()}")