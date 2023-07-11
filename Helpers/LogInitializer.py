import logging

class LogInitializer:
    def __init__(self) -> None:
        self._logger = logging.getLogger(__name__)