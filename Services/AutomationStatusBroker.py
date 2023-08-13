from Models.ObjectState import ObjectState
from Models.Settings import Settings
from Services.MessageBus import Event, MessageBus


class AutomationStatusBroker(MessageBus):
    EVENT_SETTINGS_UPDATE: str = __name__ + ".onSettingsUpdate"
    EVENT_NEW_COMMAND: str = __name__ + ".onNewCommand"
    EVENT_NEW_STATUS: str = __name__ + ".onNewStatus"
    EVENT_DELETE_OLD_DATA: str = __name__ + ".onDeleteOldData"

    def __init__(self) -> None:
        super().__init__()
        self._settings = Settings()
        self._status = ObjectState()
        self._events[AutomationStatusBroker.EVENT_NEW_COMMAND] = Event()
        self._events[AutomationStatusBroker.EVENT_NEW_STATUS] = Event()
        self._events[AutomationStatusBroker.EVENT_SETTINGS_UPDATE] = Event()

    def getSettings(self) -> Settings:
        self._logger.debug("get settings invoke, ")
        result = Settings()
        with self._lock:
            result.update(self._settings)
        return result

    def updateSettings(self, src: Settings) -> None:
        self._logger.debug("update settings invoke ")
        with self._lock:
            self._settings.update(src)
        self._onEvent(AutomationStatusBroker.EVENT_SETTINGS_UPDATE, self._settings)

    def getStatus(self) -> ObjectState:
        self._logger.debug("get status invoke, ")
        result = ObjectState()
        with self._lock:
            result.update(self._status)
        return result

    def updateStatus(self, src: ObjectState) -> None:
        self._logger.debug("update status invoke ")

        with self._lock:
            self._status.update(src)
        self._onEvent(AutomationStatusBroker.EVENT_NEW_STATUS, self._status)

    def executeCommand(self, command: str) -> bool:
        if isinstance(command, str):
            self._logger.debug(str(command)+" command received")
            return self._onEvent(AutomationStatusBroker.EVENT_NEW_COMMAND, command)
        return False