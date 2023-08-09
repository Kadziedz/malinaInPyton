from Models.Serializable import Serializable


class Thermometer(Serializable):
    def __init__(self, name: str, temperature: float) -> None:
        super().__init__()
        self.Name: str = name
        self.Temperature: float = -999 if temperature is None else temperature

    def toDictionary(self):
        document = dict()
        document["Name"] = self.Name
        document["Temperature"] = -999 if self.Temperature is None else self.Temperature

        return document

    def copy(self):
        return Thermometer(self.Name, self.Temperature)
    
    def __eq__(self, __value) -> bool:
        return self.Name == __value.Name and self.Temperature == __value.Temperature

          
