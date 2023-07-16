from abc import ABC, abstractmethod


class IRelay(ABC):
    """ COIL/LED control interface

    """
    @abstractmethod
    def get(self) -> bool:
        """ get GPIO pin status

        Returns:
            bool: GPIO pin state
        """
        pass

    @abstractmethod
    def set(self, value: bool) -> None:
        """ set GPIO pin status

        Args:
            value (bool): GPIO pin state to set
        """
        pass
