import RPi.GPIO as GPIO
import os
import logging
from Interfaces.IRelay import IRelay


class Coil(IRelay):
    def __init__(self, pin: int) -> None:
        # super().__init__()
        os.system('modprobe w1-gpio')
        GPIO.setmode(GPIO.BCM)
        self._logger = logging.getLogger(__name__)
        self._pin = pin
        self._actualState = False
        GPIO.setup(self._pin, GPIO.OUT)

    def setup(self, pin: int, isOut: bool):
        self._pin = pin
        if isOut is True:
            GPIO.setup(self._pin, GPIO.OUT)
        else:
            GPIO.setup(self._pin, GPIO.IN)
         
    def get(self) -> bool:
        self._logger.debug(f"returned [{self._pin}] = {self._actualState}")
        return self._actualState

    def set(self, value: bool) -> None:
        self._actualState = value
        self._logger.debug(f"set [{self._pin}] = {self._actualState}")
        if self._actualState is True:
            GPIO.output(self._pin, GPIO.HIGH)
        else:
            GPIO.output(self._pin, GPIO.LOW)
