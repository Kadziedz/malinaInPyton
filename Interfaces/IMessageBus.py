from abc import ABC, abstractmethod
from Models.Settings import Settings
from Models.ObjectState import ObjectState

class IMessageBus(ABC):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def getSettings(self) -> Settings:
        pass

    @abstractmethod
    def updateSettings(self, src: Settings) -> None:
        pass

    @abstractmethod
    def getStatus(self) -> ObjectState:
        pass

    @abstractmethod
    def updateStatus(self, src: ObjectState) -> None:
        pass

    @abstractmethod
    def executeCommand(self, command: str) -> bool:
        pass

    @abstractmethod
    def register(self, eventType: str, handler) -> bool:
        pass

    @abstractmethod
    def unregister(self, eventType: str, handler) -> bool:
        pass
    
    @abstractmethod
    def sendEvent(self, eventArg:object)->None:
        pass
    
    @abstractmethod
    def sendNamedEvent(self, eventType:str, eventArg:object)->None:
        pass
