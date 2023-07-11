from flask import request
from Interfaces.IMessageBus import IMessageBus
from Controllers.ControllerRoot import ControllerRoot

class SettingsController(ControllerRoot):

    def __init__(self, messageBus: IMessageBus) -> None:
        super().__init__(messageBus)

    def get(self):
        response = self._messageBus.getSettings().toDictionary()
        self._logger.debug(f"invoke get method, result: "+str(response))

        return response, 200

    def post(self):
        jsonData = request.get_json(cache=False)
        self._messageBus.updateSettings(jsonData)
        self._logger.info("post request: "+str(jsonData) +
                          ", settings after update: " + self._messageBus.getSettings().toJson())

        return True, 200
