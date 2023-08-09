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
from Models.ObjectState import ObjectState
from Services.AutomationController import AutomationController
from Services.DataWriter import DataWriter
import Startup 
from Services.SocketServer import SocketServer

# https://www.imaginarycloud.com/blog/flask-python/
# https://towardsdatascience.com/the-right-way-to-build-an-api-with-python-cd08ab285f8f
# https://able.bio/rhett/how-to-set-and-get-environment-variables-in-python--274rgt5
# https://www.loggly.com/ultimate-guide/python-logging-basics/
# https://www.tutorialspoint.com/concurrency_in_python/concurrency_in_python_pool_of_threads.htm
cfg = Config()

handler = logging.StreamHandler()
formatter = OneLineExceptionFormatter(logging.BASIC_FORMAT)
handler.setFormatter(formatter)
root = logging.getLogger()
root.setLevel(os.environ.get("LOGLEVEL", cfg.LogLevel))
root.addHandler(handler)
logging.basicConfig(level=os.environ.get("LOGLEVEL", cfg.LogLevel))

if cfg.isPi:
    import StartupPi
    ioc = StartupPi.startup(cfg)
else:
    ioc = Startup.startup(cfg)
    
plc = AutomationController(ioc)
plc.start()
socketServer = SocketServer(ioc, cfg.WebSocketServerHost, cfg.WebSocketServerPort)
socketServer.start()
mb: IMessageBus = ioc.getInstance(IMessageBus)


def sendStatusNotification(status: ObjectState):
    if isinstance(status, ObjectState):
        socketServer.sendMessage(status.toDictionary())  
    if isinstance(status, dict):
        socketServer.sendMessage(status)


mb.register(AutomationController.EVENT_STATUS_UPDATE, sendStatusNotification)

writer = DataWriter(ioc)
app = Flask(__name__)
app.logger.setLevel(level=os.environ.get("LOGLEVEL", cfg.LogLevel))

api = Api(app)
api.add_resource(StatusController, '/api',
                 resource_class_kwargs={"messageBus": ioc.getInstance(IMessageBus)})
api.add_resource(SettingsController, '/api/cfg',
                 resource_class_kwargs={"messageBus": ioc.getInstance(IMessageBus)})
api.add_resource(CommandsController, '/api/cmd/<string:command>',
                 resource_class_kwargs={"messageBus": ioc.getInstance(IMessageBus)})

if __name__ == '__main__':
    app.run(debug=False, port=5000)  # run our Flask app
    
mb.unregister(AutomationController.EVENT_STATUS_UPDATE, sendStatusNotification)
plc.requestStop()
plc.join()
socketServer.requestStop()
socketServer.join()
print("done")
