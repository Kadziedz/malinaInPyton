from Interfaces.IGauge import IGauge
from Interfaces.IMeasurementFilter import IMeasurementFilter
from Interfaces.IMessageBus import IMessageBus
from Models.ObjectState import ObjectState
from Models.Settings import Settings
from Models.Thermometer import Thermometer
from Repository.DatabaseContext import DatabaseContext
from Services.MessageBus import MessageBus
from Models.Measurements import Measurements


import datetime
import logging
import time
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping
from threading import Lock, Thread
from typing import Any


class AutomationController(Thread):
    def __init__(self, messageBus: IMessageBus, gauge: IGauge, filter: IMeasurementFilter,  databaseContext:DatabaseContext,group: None = None, target: Callable[..., object] | None = None, name: str | None = None, args: Iterable[Any] = ..., kwargs: Mapping[str, Any] | None = None, *, daemon: bool | None = None) -> None:
        super().__init__(group, target, name, args, kwargs, daemon=daemon)
        self._databaseContext:DatabaseContext = databaseContext
        self._messageBus: IMessageBus = messageBus
        self._meter:IGauge = gauge
        self._filter: IMeasurementFilter = filter
        self._lock: Lock = Lock()
        self.__isStopRequested: bool = False
        self._actualSettings:Settings = self._messageBus.getSettings()
        self._cmdAuto:bool= self._actualSettings.IsAuto
        self._cmdRun:bool= False
        self._actualState:ObjectState = AutomationController.__initializeDataStructures(self._actualSettings, self._meter, self._messageBus, self._databaseContext)
        self._messageBus.updateStatus(self._actualState)
        self._logger:logging= logging.getLogger(__name__)

        messageBus.register(MessageBus.EVENT_NEW_COMMAND, self.onNewCommandReceived)
        messageBus.register(MessageBus.EVENT_SETTINGS_UPDATE, self.onNewSettings)
        # messageBusSingleton.register(MessageBus.EVENT_NEW_STATUS, self.onNewStatus)

    def __del__(self):
            self._messageBus.unregister(MessageBus.EVENT_NEW_COMMAND, self.onNewCommandReceived)
            self._messageBus.unregister(MessageBus.EVENT_SETTINGS_UPDATE, self.onNewSettings)

    def __initializeDataStructures(config:Settings, gauge:IGauge, sb:IMessageBus, db:DatabaseContext)->ObjectState:
        locState=sb.getStatus()
        physicalDeviceNamesList = gauge.getDevices()
        devices = db.synchronizeDevices(physicalDeviceNamesList)
        locState.Device = [Thermometer(devices[key].Name, None) for key in devices]
        locState.AmbientSensorTemp = None
        locState.LowerSensorTemp = None
        locState.HigherSensorTemp = None
        return AutomationController.__updateState(config, locState)

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
        while not self.isStopRequested():

            actualTime = datetime.datetime.now()
            delta:datetime.timedelta = actualTime - lastIteration
            with self._lock:
                localSettings.update(self._actualSettings)
                localStatus.update(self._actualState)

            if delta.total_seconds() >= min([15, (localSettings.DataSaveInterval >> 1)]) :
                lastIteration = actualTime
                AutomationController.__measureTemperatures(localStatus, self._meter, self._filter, measurements, localSettings, self._logger)
                with self._lock:
                    self._actualState.update(localStatus)
                self._messageBus.updateStatus(localStatus)

                delta = actualTime - lastDbWrite
                if delta.total_seconds()> localSettings.DataSaveInterval and  len(measurements)>0 :
                    lastDbWrite = actualTime
                    #update if required 
                    self._messageBus.sendEvent(Measurements(measurements))
                    self._logger.warning(f"store to db requested {str(measurements)}")
                    measurements.clear()
            time.sleep(0)

    def __measureTemperatures(localStatus:ObjectState, gauge:IGauge, filter:IMeasurementFilter, measurements:dict, localSettings:Settings, logger:logging)->ObjectState:
        thermometers:dict = {device.Name: device for device in localStatus.Device }
        deviceNames:list = gauge.getDevices()
        for label in deviceNames:
            temperature:float = gauge.measure(label)
            temperature = AutomationController.__addOffsets(temperature, label, localSettings)
            filteredTemp:float =-999
            if temperature == None:
                logger.warning(f"failed to get temperature for {label}")
                temperature = -999
            else:
                filter.updateMeasurements(label, temperature, localSettings.MeasurementSamplesCount)
                filteredTemp:float = filter.Get(label)
            logger.debug(f"filtered temperature [{label}] = {filteredTemp}")
            if filteredTemp != 999 :
                measurements[label] = filteredTemp

            if label in thermometers:
                thermometers[label].Temperature = filteredTemp
            else:
                localStatus.Device.append(Thermometer(label, filteredTemp))
        localStatus.AmbientSensorTemp = thermometers[localStatus.AmbientTempSensor].Temperature
        localStatus.HigherSensorTemp = thermometers[localStatus.HigherTempSensor].Temperature
        localStatus.LowerSensorTemp = thermometers[localStatus.LowerTempSensor].Temperature

        return localStatus


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