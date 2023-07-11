from Interfaces.IRelay import IRelay


class Relay(IRelay):
    def __init__(self, pin: int) -> None:
        super().__init__()
        self._pin = pin
        self._actualState = None

    def setup(self, pin: int) -> None:
        self._pin = pin

    def get(self) -> bool:
        return self._actualState

    def set(self, value: bool) -> None:
        self._actualState = value
