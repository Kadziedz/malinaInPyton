from Automation.Gauge import Gauge
from Automation.Relay import Relay
from Interfaces.IActualDateProvider import IActualDateProvider
from Interfaces.IMeasurementFilter import IMeasurementFilter
from Interfaces.IMessageBus import IMessageBus
from Models.Config import Config
from Repository.DatabaseContext import DatabaseContext
from Services.ActualDateProvider import ActualDateProvider
from Services.AutomationStatusBroker import AutomationStatusBroker
from Services.MeasurementFilter import MeasurementFilter
from Services.SimpleIoc import SimpleIoC


def startup(config: Config) -> SimpleIoC:
    # initial setup
    dbContextSingleton = DatabaseContext(config.ConnectionStrings["ControlDB"])
    actualSettings = dbContextSingleton.getSettings()
    if actualSettings is None:
        actualSettings = config.getSettings()
        dbContextSingleton.createSettings(actualSettings)

    messageBusSingleton = AutomationStatusBroker()
    messageBusSingleton.updateSettings(actualSettings)
    LEDs = {label: Relay(config.GPIO[label]) for label in config.GPIO}

    ioc = SimpleIoC()
    ioc.registerSingleton(AutomationStatusBroker, messageBusSingleton)
    ioc.registerSingleton(IMessageBus, messageBusSingleton)
    ioc.registerSingleton(DatabaseContext, dbContextSingleton)
    ioc.registerSingleton("coils", LEDs)
    thermometers = Gauge.getDevices()
    ioc.registerSingleton("thermometers", thermometers)
    ioc.registerSingleton("config", config)
    ioc.registerSingleton(IActualDateProvider, ActualDateProvider())
    ioc.registerSingleton(IMeasurementFilter, MeasurementFilter(ioc))
    
    return ioc
