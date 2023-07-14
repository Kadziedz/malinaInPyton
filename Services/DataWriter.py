from Interfaces.IMessageBus import IMessageBus
from Models.Settings import Settings
from Repository.DatabaseContext import DatabaseContext
from Services.MessageBus import MessageBus
from Models.Measurements import Measurements


import logging
from threading import Lock, Thread


class DataWriter(object):
    def __init__(self, databaseContext:DatabaseContext, sb:IMessageBus) -> None:
        self._databaseContext = databaseContext
        rawData = databaseContext.getDevices()
        self._devicesByName = {item.Name:item for item in rawData }
        self._devicesById = {item.Id:item for item in rawData }
        self._logger:logging = logging.getLogger(__name__)
        self._messageBus = sb
        self.__eventType = str(Measurements)
        self._lock: Lock = Lock()
        self._messageBus.register(self.__eventType, self.onStoreData)
        self._messageBus.register(MessageBus.EVENT_SETTINGS_UPDATE, self.onNewSettings)

    def __del__(self):
        self._messageBus.unregister(self.__eventType, self.onStoreData)
        self._messageBus.unregister(MessageBus.EVENT_SETTINGS_UPDATE, self.onNewSettings)

    def onStoreData(self, measurements:Measurements)->None:
            Thread(target=self.__storeMeasurements, kwargs={'measurements':measurements}).start()


    def onNewSettings(self, measurements:Measurements)->None:
            Thread(target=self.__storeSettings, kwargs={'newSettings':measurements}).start()

    def __storeSettings(self, newSettings: Settings) -> None:
        with self._lock:
            self._logger.info(f"settings update to {newSettings.toJson()}")

    def __storeMeasurements(self, measurements:Measurements)->None:
        with self._lock:
            self._logger.info("new write task received")