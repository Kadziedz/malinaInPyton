from collections import defaultdict
from Interfaces.IContainer import IContainer


class SimpleIoC(IContainer):
    def __init__(self) -> None:
        self.__registrations:dict= defaultdict()

    def registerSingleton(self, itemType:type, instance:object)->None:
        key:str=None
        if isinstance(itemType, type) and isinstance(instance, itemType):
            key = str(itemType)
        if isinstance(itemType, str):
            key = itemType
        if callable(instance):
            raise TypeError()
        if not key is None:
            self.__registrations[key]= instance
            
    def getInstance(self, itemType:type)->object:
        key:str=""
        if isinstance(itemType, type):
            key = str(itemType)
        if isinstance(itemType, str):
            key = itemType
        if not key in self.__registrations:
            raise KeyError()
        instance =self.__registrations[key]
        if callable(instance):
            return instance()
        return instance