from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping
import datetime
import time
import logging
from typing import Any
from flask import Flask
from flask_restful import Api, Resource, reqparse
from threading import Lock, Thread
from Automation.Gauge import Gauge
from Interfaces.IGauge import IGauge
from Interfaces.IMeasurementFilter import IMeasurementFilter
from Interfaces.IMessageBus import IMessageBus


from Models.Thermometer import Thermometer
from Models.ObjectState import ObjectState
from Repository.DatabaseContext import DatabaseContext
# import concurrent.futures
# import threading
from Services.MessageBus import MessageBus
from Controllers.SettingsController import SettingsController
from Controllers.StatusController import StatusController
from Controllers.CommandsController import CommandsController
from Helpers.OneLineExceptionFormatter import OneLineExceptionFormatter
from Helpers.LogInitializer import LogInitializer
from Models.Serializable import Serializable
from Models.Settings import Settings
from Models.Config import Config


# https://www.imaginarycloud.com/blog/flask-python/
# https://towardsdatascience.com/the-right-way-to-build-an-api-with-python-cd08ab285f8f
# https://able.bio/rhett/how-to-set-and-get-environment-variables-in-python--274rgt5
# https://www.loggly.com/ultimate-guide/python-logging-basics/

import logging.handlers
import os
from Services.MeasurementFilter import MeasurementFilter


cfg = Config()
handler = logging.StreamHandler()
formatter = OneLineExceptionFormatter(logging.BASIC_FORMAT)
handler.setFormatter(formatter)
root = logging.getLogger()
root.setLevel(os.environ.get("LOGLEVEL", cfg.LogLevel))
root.addHandler(handler)
# logging.basicConfig(level=os.environ.get("LOGLEVEL", cfg.LogLevel))

dbContext = DatabaseContext(cfg.ConnectionStrings["ControlDB"])
# initial setup
actualSettings = dbContext.getSettings()
if actualSettings==None:
    actualSettings=cfg.getSettings()
    dbContext.setSettings(actualSettings)  


messageBusSingleton = MessageBus()
messageBusSingleton.updateSettings(actualSettings)

thermometer = Gauge()

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
        self._actualState:ObjectState = AutomationController.__initializeDataStructures(self._actualSettings, self._meter, self._messageBus, self._databaseContext)
        self._messageBus.updateStatus(self._actualState)
        self._logger:logging= logging.getLogger(__name__)
        messageBus.register(MessageBus.EVENT_NEW_COMMAND, self.onNewCommandReceived)
        messageBus.register(MessageBus.EVENT_SETTINGS_UPDATE, self.onNewSettings)
        # messageBusSingleton.register(MessageBus.EVENT_NEW_STATUS, self.onNewStatus)
            
    def __initializeDataStructures(config:Settings, gauge:IGauge, sb:IMessageBus, db:DatabaseContext)->ObjectState:
        locState=sb.getStatus()
        physicalDeviceNamesList = gauge.getDevices()
        devices = db.getDevices(physicalDeviceNamesList)
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


    def onNewCommandReceived(self, command: str) -> None:
        print("****************<COMMAND>*******************")
        print(f"*                  {command: >5}                   *")
        print("********************************************")

    # def onNewStatus(newStatus:ObjectState)->None:
    #     print("****************<STATUS>*******************")
    #     print(newStatus.toJson().replace(",",",\n"))
    #     print("********************************************")

    def onNewSettings(self, newSettings: Settings) -> None:
        with self._lock:
            self._actualSettings.update(newSettings)
            AutomationController.__updateState(self._actualSettings, self._actualState)
            self._databaseContext.setSettings(self._actualSettings)
        self._logger.debug(f"settings update to {self._actualSettings.toJson()}")


# ts = time.time()
# print(ts)
# ct = datetime.datetime.now()
# print("current time:-", ct)
# ts = ct.timestamp()
# print("timestamp:-", ts)
# create app

plc = AutomationController(messageBusSingleton, thermometer, MeasurementFilter(), dbContext )
plc.start()

app = Flask(__name__)
api = Api(app)
api.add_resource(StatusController, '/api',
                 resource_class_kwargs={"messageBus": messageBusSingleton})
api.add_resource(SettingsController, '/api/cfg',
                 resource_class_kwargs={"messageBus": messageBusSingleton})
api.add_resource(CommandsController, '/api/cmd/<string:command>',
                 resource_class_kwargs={"messageBus": messageBusSingleton})

if __name__ == '__main__':
    app.run(debug=False, port=5000)  # run our Flask app

plc.requestStop()
plc.join()
print("done")
