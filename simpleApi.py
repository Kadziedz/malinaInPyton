import logging
from flask import Flask
from flask_restful import Api
from Automation.Gauge import Gauge
from Services.DataWriter import DataWriter
from Services.AutomationController import AutomationController


from Repository.DatabaseContext import DatabaseContext
# import concurrent.futures
# import threading
from Services.MessageBus import MessageBus
from Controllers.SettingsController import SettingsController
from Controllers.StatusController import StatusController
from Controllers.CommandsController import CommandsController
from Helpers.OneLineExceptionFormatter import OneLineExceptionFormatter
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

dbContextSingleton = DatabaseContext(cfg.ConnectionStrings["ControlDB"])
# initial setup
actualSettings = dbContextSingleton.getSettings()
if actualSettings==None:
    actualSettings=cfg.getSettings()
    dbContextSingleton.createSettings(actualSettings)  


messageBusSingleton = MessageBus()
messageBusSingleton.updateSettings(actualSettings)

thermometer = Gauge()
# ts = time.time()
# print(ts)
# ct = datetime.datetime.now()
# print("current time:-", ct)
# ts = ct.timestamp()
# print("timestamp:-", ts)
# create app

plc = AutomationController(messageBusSingleton, thermometer, MeasurementFilter(), dbContextSingleton )
plc.start()

writer = DataWriter(dbContextSingleton, messageBusSingleton)
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
