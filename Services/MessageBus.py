from threading import Lock
from Interfaces.IMessageBus import IMessageBus
from Models.Settings import Settings
from Models.ObjectState import ObjectState
import logging


class Event(object):

    def __init__(self):
        self.__eventHandlers = []

    def __iadd__(self, handler):
        self.__eventHandlers.append(handler)
        return self

    def __isub__(self, handler):
        self.__eventHandlers.remove(handler)
        return self

    def __call__(self, *args, **keywargs):
        result = None
        for eventHandler in self.__eventHandlers:
            result = eventHandler(*args, **keywargs)
        return result


class MessageBus(IMessageBus):
    
    EVENT_SETTINGS_UPDATE: str = __name__ + ".onSettingsUpdate"
    EVENT_NEW_COMMAND: str = __name__ + ".onNewCommand"
    EVENT_NEW_STATUS: str = __name__ + ".onNewStatus"
    EVENT_DELETE_OLD_DATA: str = __name__ + ".onDeleteOldData"

    def __init__(self) -> None:
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self._settings = Settings()
        self._status = ObjectState()
        self._events = {MessageBus.EVENT_NEW_COMMAND: Event(),
                        MessageBus.EVENT_NEW_STATUS: Event(),
                        MessageBus.EVENT_SETTINGS_UPDATE: Event()}
        self._lock = Lock()
        
    def register(self, eventType: str, handler) -> bool:
        if eventType not in self._events:
            self._events[eventType] = Event()
        if not callable(handler):
            return False
        self._events[eventType] += handler
        return True

    def unregister(self, eventType: str, handler) -> bool:
        if eventType not in self._events or not callable(handler):
            return False
        self._events[eventType] -= handler
        return True

    def __onEvent(self, eventType: str, eventArg):
        if isinstance(eventType, str):
            with self._lock:
                if eventType in self._events:
                    return self._events[eventType](eventArg)
        else:
            self._logger.critical(f"dropping unknown event type {eventType}")
             
    def getSettings(self) -> Settings:
        self._logger.debug("get settings invoke, ")
        result = Settings()
        with self._lock:
            result.update(self._settings)
        return result

    def updateSettings(self, src: Settings) -> None:
        self._logger.debug("update settings invoke ")
        with self._lock:
            self._settings.update(src)
        self.__onEvent(MessageBus.EVENT_SETTINGS_UPDATE, self._settings)

    def getStatus(self) -> ObjectState:
        self._logger.debug("get status invoke, ")
        result = ObjectState()
        with self._lock:
            result.update(self._status)
        return result

    def updateStatus(self, src: ObjectState) -> None:
        self._logger.debug("update status invoke ")

        with self._lock:
            self._status.update(src)
        self.__onEvent(MessageBus.EVENT_NEW_STATUS, self._status)   

    def executeCommand(self, command: str) -> bool:
        if isinstance(command, str):
            self._logger.debug(str(command)+" command received")
            return self.__onEvent(MessageBus.EVENT_NEW_COMMAND, command)
        return False
    
    def sendEvent(self, eventArg: object) -> None:
        eventType: str = str(type(eventArg))
        self.__onEvent(eventType, eventArg)
        
    def sendNamedEvent(self, eventType: str, eventArg: object) -> None:
        self.__onEvent(eventType, eventArg)
