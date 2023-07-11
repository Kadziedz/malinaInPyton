import datetime
import time
import logging
from flask import Flask
from flask_restful import Api, Resource, reqparse
from threading import Lock, Thread
from Automation.Gauge import Gauge


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

def onNewCommandReceived(command:str)->None:
    print("****************<COMMAND>*******************")
    print(f"*                  {command: >5}                   *")
    print("********************************************")

def onNewStatus(newStatus:ObjectState)->None:
    print("****************<STATUS>*******************")
    print(newStatus.toJson().replace(",",",\n"))
    print("********************************************")

def onNewSettings(newStatus:Settings)->None:
    print("***************<SETTINGS>*******************")
    print(newStatus.toJson().replace(",",",\n"))
    print("********************************************")

cfg = Config()
handler = logging.StreamHandler()
formatter = OneLineExceptionFormatter(logging.BASIC_FORMAT)
handler.setFormatter(formatter)
root = logging.getLogger()
root.setLevel(os.environ.get("LOGLEVEL", cfg.LogLevel))
root.addHandler(handler)
# logging.basicConfig(level=os.environ.get("LOGLEVEL", cfg.LogLevel))

# filter = MeasurementFilter()
# print(filter.Get("a"))
# filter.updateMeasurements("a", 1, 10)
# print(filter.Get("a"))


messageBusSingleton = MessageBus()
db = DatabaseContext(cfg.getSettings(), cfg.ConnectionStrings["ControlDB"])
##initial setup
actualSettings = db.getSettings()
messageBusSingleton.updateSettings(actualSettings)

physicalDeviceNamesList = Gauge.getDevices()
devices = db.getDevices(physicalDeviceNamesList)

actualState = messageBusSingleton.getStatus()

actualState.Device = [Thermometer(devices[key].Name, None ) for key in devices]
actualState.AmbientTempSensor = actualSettings.AmbientTempSensor
actualState.LowerTempSensor= actualSettings.LowerTempSensor
actualState.HigherTempSensor = actualSettings.HigherTempSensor
actualState.AmbientSensorTemp= None
actualState.LowerSensorTemp= None
actualState.HigherSensorTemp=None
messageBusSingleton.updateStatus(actualState)

#events registration
messageBusSingleton.register(MessageBus.EVENT_NEW_COMMAND, onNewCommandReceived)
messageBusSingleton.register(MessageBus.EVENT_NEW_STATUS, onNewStatus)
messageBusSingleton.register(MessageBus.EVENT_SETTINGS_UPDATE, onNewSettings)

# ts = time.time()
# print(ts)
# ct = datetime.datetime.now()
# print("current time:-", ct)
# ts = ct.timestamp()
# print("timestamp:-", ts)
# create app
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


