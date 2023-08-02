import logging
from threading import Lock, Thread

from Interfaces.IMessageBus import IMessageBus
from Models.DTO.dtos import DataPoint
from Models.Settings import Settings
from Repository.DatabaseContext import DatabaseContext
from Services.MessageBus import MessageBus
from Models.Measurements import Measurements
from Services.SimpleIoc import SimpleIoC


class DataWriter(object):
    def __init__(self, ioc:SimpleIoC) -> None:
        self._databaseContext:DatabaseContext = ioc.getInstance(DatabaseContext)
        self._messageBus = ioc.getInstance(IMessageBus)
        rawData = self._databaseContext.getDevices()
        self._devicesByName = {item.Name:item for item in rawData }
        self._devicesById = {item.Id:item for item in rawData }
        self._logger:logging = logging.getLogger(__name__)
        
        self.__eventType = str(Measurements)
        self._lock: Lock = Lock()
        self._messageBus.register(self.__eventType, self.onStoreData)
        self._messageBus.register(MessageBus.EVENT_SETTINGS_UPDATE, self.onNewSettings)
        self._messageBus.register(MessageBus.EVENT_DELETE_OLD_DATA, self.onDeleteOldData)
    
    def __del__(self):
        self._messageBus.unregister(self.__eventType, self.onStoreData)
        self._messageBus.unregister(MessageBus.EVENT_SETTINGS_UPDATE, self.onNewSettings)
        self._messageBus.unregister(MessageBus.EVENT_DELETE_OLD_DATA, self.onDeleteOldData)


    def onStoreData(self, measurements:Measurements)->None:
            Thread(target=self.__storeMeasurements, kwargs={'measurements':measurements}).start()

    def onNewSettings(self, settings:Settings)->None:
            Thread(target=self.__storeSettings, kwargs={'newSettings':settings}).start()

    def onDeleteOldData(self, dayIndex:int)->None:
            Thread(target=self.__deleteOldData, kwargs={'dayIndex':dayIndex}).start()

    def __deleteOldData(self, dayIndex: int) -> None:
        with self._lock:
            self._logger.info(f"removing data points older than {dayIndex}")
            self._databaseContext.deleteOldMeasurements(dayIndex)


    def __storeSettings(self, newSettings: Settings) -> None:
        with self._lock:
            self._logger.info(f"settings update to {newSettings.toJson()}")
            self._databaseContext.updateSettings(newSettings)

    def __storeMeasurements(self, measurements:Measurements)->None:
        with self._lock:
            self._logger.info("new write task received")
            rows = [DataPoint(measurements.eventTimestamp, float(measurements.data[deviceName]), 0, measurements.isWorking,  int(self._devicesByName[deviceName].Id) ) for deviceName in measurements.data]
            self._databaseContext.storeDataPoints(rows)
            
            