import logging
import logging.handlers
import os


from flask import Flask
from flask_restful import Api
from Interfaces.IMessageBus import IMessageBus
from Controllers.CommandsController import CommandsController
from Controllers.SettingsController import SettingsController
from Controllers.StatusController import StatusController
from Helpers.OneLineExceptionFormatter import OneLineExceptionFormatter
from Models.Config import Config
from Services.AutomationController import AutomationController
from Services.DataWriter import DataWriter
from Startup import Startup
# https://www.imaginarycloud.com/blog/flask-python/
# https://towardsdatascience.com/the-right-way-to-build-an-api-with-python-cd08ab285f8f
# https://able.bio/rhett/how-to-set-and-get-environment-variables-in-python--274rgt5
# https://www.loggly.com/ultimate-guide/python-logging-basics/
cfg= Config()

handler = logging.StreamHandler()
formatter = OneLineExceptionFormatter(logging.BASIC_FORMAT)
handler.setFormatter(formatter)
root = logging.getLogger()
root.setLevel(os.environ.get("LOGLEVEL", cfg.LogLevel))
root.addHandler(handler)
logging.basicConfig(level=os.environ.get("LOGLEVEL", cfg.LogLevel))

ioc = Startup(cfg)
plc = AutomationController(ioc)
plc.start()
writer = DataWriter(ioc)

app = Flask(__name__)
api = Api(app)
api.add_resource(StatusController, '/api',
                 resource_class_kwargs={"messageBus": ioc.getInstance(IMessageBus)})
api.add_resource(SettingsController, '/api/cfg',
                 resource_class_kwargs={"messageBus": ioc.getInstance(IMessageBus)})
api.add_resource(CommandsController, '/api/cmd/<string:command>',
                 resource_class_kwargs={"messageBus": ioc.getInstance(IMessageBus)})

if __name__ == '__main__':
    app.run(debug=False, port=5000)  # run our Flask app

plc.requestStop()
plc.join()
print("done")
