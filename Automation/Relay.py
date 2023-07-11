
import logging
from Interfaces.IRelay import IRelay


class Relay(IRelay):
    def __init__(self, pin: int) -> None:
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self._pin = pin
        self._actualState = None

    def setup(self, pin: int) -> None:
        self._pin = pin

    def get(self) -> bool:
        self._logger.warning(f"returned [{self._pin} = {self._actualState}")
        return self._actualState

    def set(self, value: bool) -> None:
        self._actualState = value
        self._logger.warning(f"set [{self._pin} = {self._actualState}")
