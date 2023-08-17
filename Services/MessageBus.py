from threading import Lock
from Interfaces.IMessageBus import IMessageBus
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

    def __init__(self) -> None:
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self._lock: Lock = Lock()
        self._events: dict = {}
        
    def register(self, eventType: str, handler) -> bool:
        eventTypeLabel = eventType
        if not isinstance(eventTypeLabel, str):
            eventTypeLabel = str(type(eventTypeLabel))
            
        if eventTypeLabel not in self._events:
            self._events[eventTypeLabel] = Event()
            
        if not callable(handler):
            return False
        self._events[eventTypeLabel] += handler
        return True

    def unregister(self, eventType: str, handler) -> bool:
        eventTypeLabel = eventType
        if not isinstance(eventTypeLabel, str):
            eventTypeLabel = str(type(eventTypeLabel))
            
        if eventTypeLabel not in self._events or not callable(handler):
            return False
        self._events[eventTypeLabel] -= handler
        return True

    def _onEvent(self, eventType: str, eventArg):
        if isinstance(eventType, str):
            with self._lock:
                if eventType in self._events:
                    return self._events[eventType](eventArg)
        else:
            self._logger.critical(f"dropping unknown event type {eventType}")

    def sendEvent(self, eventArg: object) -> None:
        eventType: str = str(type(eventArg))
        self._onEvent(eventType, eventArg)
        
    def sendNamedEvent(self, eventType: str, eventArg: object) -> None:
        self._onEvent(eventType, eventArg)


