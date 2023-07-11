from Models.Serializable import Serializable


class Thermometer(Serializable):
    def __init__(self, name: str, temperature: float) -> None:
        super().__init__()
        self.Name: str = name
        self.Temperature: float = temperature

    def toDictionary(self):
        document = dict()
        document["Name"] = self.Name
        document["Temperature"] = self.Temperature

        return document

    def copy(self):
        return Thermometer(self.Name, self.Temperature)

          
