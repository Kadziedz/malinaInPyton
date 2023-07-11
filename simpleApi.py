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

db = DatabaseContext(cfg.ConnectionStrings["ControlDB"])
# initial setup
actualSettings = db.getSettings()
if actualSettings==None:
    actualSettings=cfg.getSettings()
    db.setSettings(actualSettings)  


messageBusSingleton = MessageBus()
messageBusSingleton.updateSettings(actualSettings)

thermometer = Gauge()

physicalDeviceNamesList = thermometer.getDevices()
devices = db.getDevices(physicalDeviceNamesList)
actualState = messageBusSingleton.getStatus()
actualState.Device = [Thermometer(devices[key].Name, None) for key in devices]
actualState.AmbientTempSensor = actualSettings.AmbientTempSensor
actualState.LowerTempSensor = actualSettings.LowerTempSensor
actualState.HigherTempSensor = actualSettings.HigherTempSensor
actualState.AmbientSensorTemp = None
actualState.LowerSensorTemp = None
actualState.HigherSensorTemp = None
messageBusSingleton.updateStatus(actualState)


class AutomationController(Thread):
    def __init__(self, messageBus: IMessageBus, gauge: IGauge, filter: IMeasurementFilter, group: None = None, target: Callable[..., object] | None = None, name: str | None = None, args: Iterable[Any] = ..., kwargs: Mapping[str, Any] | None = None, *, daemon: bool | None = None) -> None:
        super().__init__(group, target, name, args, kwargs, daemon=daemon)
        self._actualSettings:Settings = messageBus.getSettings()
        messageBus.register(MessageBus.EVENT_NEW_COMMAND, self.onNewCommandReceived)
       # messageBusSingleton.register(MessageBus.EVENT_NEW_STATUS, self.onNewStatus)
        messageBus.register(MessageBus.EVENT_SETTINGS_UPDATE, self.onNewSettings)
        self._messageBus: IMessageBus = messageBus
        self._meter: IGauge = gauge

        self._filter: IMeasurementFilter = filter
        self._lock: Lock = Lock()
        with self._lock:
            self.__isStopRequested: bool = False

    def requestStop(self):
        with self._lock:
            self.__isStopRequested = True

    def isStopRequested(self) -> bool:
        result: bool = False
        with self._lock:
            result = self.__isStopRequested
        return result

    def run(self) -> None:
        lastIteration = datetime.datetime.now()
        actualTime = datetime.datetime.now()
        localSettings:Settings = Settings()
        while not self.isStopRequested():

            with self._lock:
                localSettings.update(self._actualSettings)
                
            actualTime = datetime.datetime.now()
            delta = actualTime - lastIteration
            
            if delta.total_seconds() >= 15:
                lastIteration = datetime.datetime.now()
                deviceNames = self._meter.getDevices()
                for label in deviceNames:
                    temperature = self._meter.measure(label)
                    self._filter.updateMeasurements(label, temperature, localSettings.MeasurementSamplesCount)
            time.sleep(0)

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
        print("***************<SETTINGS>*******************")
        print(newSettings.toJson().replace(",", ",\n"))
        print("********************************************")


# ts = time.time()
# print(ts)
# ct = datetime.datetime.now()
# print("current time:-", ct)
# ts = ct.timestamp()
# print("timestamp:-", ts)
# create app

plc = AutomationController(messageBusSingleton, thermometer, MeasurementFilter() )
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
