from abc import ABC, abstractmethod


class IContainer(ABC):
    
    @abstractmethod
    def getInstance(self, itemType: type) -> object:
        pass
