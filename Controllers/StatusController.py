from Interfaces.IMessageBus import IMessageBus
from Controllers.ControllerRoot import ControllerRoot


class StatusController(ControllerRoot):

    def __init__(self, messageBus: IMessageBus) -> None:
        super().__init__(messageBus)

    def get(self):
        response = self._messageBus.getStatus().toDictionary()
        self._logger.debug(f"invoke get method, response: " + str(response))

        return response, 200
