from abc import ABC, abstractmethod
import json

class Serializable(ABC):
    
    def __init__(self) -> None:
        super().__init__()
    
    def toJson(self) -> str:
        return json.dumps(self.toDictionary())
        
    def __repr__(self) -> str:
        return self.toJson()
    
    def __str__(self) -> str:
        return self.toJson()
    
    @abstractmethod
    def toDictionary(self):
        pass