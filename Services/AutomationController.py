import datetime
import logging
import time
from typing import Any
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping
from threading import Lock, Thread
from Interfaces.IRelay import IRelay
from Interfaces.ISensor import ISensor
from Interfaces.IMeasurementFilter import IMeasurementFilter
from Interfaces.IMessageBus import IMessageBus
from Models.ObjectState import ObjectState
from Models.Settings import Settings
from Models.Thermometer import Thermometer
from Repository.DatabaseContext import DatabaseContext
from Services.MeasurementFilter import MeasurementFilter
from Services.MessageBus import MessageBus
from Models.Measurements import Measurements
from Services.SimpleIoc import SimpleIoC
from concurrent.futures import ThreadPoolExecutor

class AutomationController(Thread):
    LED_RED:str="RedLED"
    LED_GREEN:str="GreenLED"
    LED_YELLOW:str="YellowLED"
    LED_BLINKER:str="BlinkingLED"
    RELAY:str="Relay"
    
    def __init__(self, ioc:SimpleIoC) -> None:
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
        self._actualState:ObjectState = AutomationController.__initializeDataStructures(self._actualSettings, [key for key in self._meters], self._messageBus, self._databaseContext)
        self._messageBus.updateStatus(self._actualState)
        self._logger:logging= logging.getLogger(__name__)
        
        self._messageBus.register(MessageBus.EVENT_NEW_COMMAND, self.onNewCommandReceived)
        self._messageBus.register(MessageBus.EVENT_SETTINGS_UPDATE, self.onNewSettings)
        # messageBusSingleton.register(MessageBus.EVENT_NEW_STATUS, self.onNewStatus)

    def __del__(self):
            self._messageBus.unregister(MessageBus.EVENT_NEW_COMMAND, self.onNewCommandReceived)
            self._messageBus.unregister(MessageBus.EVENT_SETTINGS_UPDATE, self.onNewSettings)
    
    @staticmethod
    def __initializeDataStructures(config:Settings, physicalDeviceNamesList:list, sb:IMessageBus, db:DatabaseContext)->ObjectState:
        locState=sb.getStatus()
        devices = db.synchronizeDevices(physicalDeviceNamesList)
        locState.Device = [Thermometer(devices[key].Name, None) for key in devices]
        locState.AmbientSensorTemp = None
        locState.LowerSensorTemp = None
        locState.HigherSensorTemp = None
        return AutomationController.__updateState(config, locState)

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
        localSettings:Settings = Settings()
        localStatus:ObjectState= ObjectState()
        lastDbWrite:datetime.datetime = datetime.datetime.now()
        measurements:dict = defaultdict()
        ledBlinker:IRelay= self._coils[AutomationController.LED_BLINKER]
        ledPumpActive:IRelay = self._coils[AutomationController.LED_RED]
        ledManualMode:IRelay = self._coils[AutomationController.LED_YELLOW]
        ledAutoMode:IRelay = self._coils[AutomationController.LED_GREEN]
        relay:IRelay= self._coils[AutomationController.RELAY]
        # lastBlink:datetime= actualTime
        # flipFlop:bool=False
        workStart:datetime= actualTime
        workStop:datetime= actualTime
        lasControlTime:datetime = actualTime
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
            
            #read temperatures
            if delta.total_seconds() >= min([4, (localSettings.DataSaveInterval >> 1)]) and future == None :
                #self._logger.warning(f"\nAUTO: {ledAutoMode.get()}\tMAN: {ledManualMode.get()}\trelay: {relay.get()}\tled: {ledPumpActive.get()}\n")
                lastIteration = actualTime
                measurements.clear()
                future = self._executor.submit(AutomationController.__dirtyTemperaturesRead, (self._meters))
                
            if future != None and future.done():
                localMeasurements:dict = future.result()
                localMeasurements = AutomationController.__filterTemperaturesAndAddOffsets(localMeasurements, self._filter, localSettings, self._logger)
                measurements.update(localMeasurements)
                AutomationController.__updateLocalStatusTemperatures(measurements, localStatus, self._logger)
                future = None
                #with self._lock:
                #    self._actualState.update(localStatus)
                #self._messageBus.updateStatus(localStatus)

            delta = actualTime - lastDbWrite
            if delta.total_seconds()> localSettings.DataSaveInterval and  len(measurements)>0 :
                lastDbWrite = actualTime
                #update if required 
                self._messageBus.sendEvent(Measurements(measurements, self._isRun, actualTime))
                self._logger.info(f"store to db requested {str(measurements)}")
                measurements.clear()
                    
            # delta:datetime.timedelta =  actualTime - lastBlink
            # # toggle diode on board
            # if delta.total_seconds()>0.5:
            #     flipFlop= not flipFlop
            #     lastBlink= actualTime
            #     ledBlinker.set(flipFlop)
              
            #automatic control iteration
            delta= actualTime - lasControlTime
            if self._isAutoMode and(delta.total_seconds() >= localSettings.ControlInterval and (actualTime.hour >= localSettings.DayStart and actualTime.hour <= localSettings.DayStop)):
                #TO DO 
                lasControlTime = actualTime
                lowerTemp = self._filter.Get(localSettings.LowerTempSensor)
                higherTemp = self._filter.Get(localSettings.HigherTempSensor)
                ambientTemp = self._filter.Get(localSettings.AmbientTempSensor)
                
                maxInactivityTime = localSettings.MaxStateTime
                pass
            
            # ignore command, out of working hours
            if (self._isRun or locCmdRun) and (self._isAutoMode or locCmdAuto) and (actualTime.hour < localSettings.DayStart or actualTime.hour> localSettings.DayStop):
                # locCmdRun= False
                # with self._lock:
                #     self._cmdRun = False
                pass
            
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
                ledPumpActive.set(self._isRun)
                if self._isRun :
                    workStart= actualTime
                else:
                    workStop= actualTime
                self._messageBus.sendEvent(Measurements(measurements, self._isRun, actualTime))
            
            with self._lock:
                if self._actualState != localStatus:
                    self._actualState.update(localStatus)
                    self._messageBus.updateStatus(localStatus)
                
            time.sleep(0.3)
            
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
                filteredTemp = filter.Get(label)
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
                self._cmdRun=True
                return True
            elif capitalizedCommand == "OFF":
                self._cmdRun=False
                return True
        return False

    def onNewSettings(self, newSettings: Settings) -> None:
        with self._lock:
            self._actualSettings.update(newSettings)
            AutomationController.__updateState(self._actualSettings, self._actualState)
        self._logger.info(f"settings update to {self._actualSettings.toJson()}")