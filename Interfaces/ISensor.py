from abc import ABC, abstractmethod


class ISensor(ABC):
    """ sensor interface, used to measure temperatures

    """
    # @abstractmethod
    # def getDevices(self) -> list:
    #     pass

    @abstractmethod
    def measure(self):
        """
            provides temperature obtained from the sensor
        Args:
            key (_type_, optional): _description_. Defaults to None.
        """
