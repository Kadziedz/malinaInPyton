from Interfaces.IMessageBus import IMessageBus
from Controllers.ControllerRoot import ControllerRoot

class CommandsController(ControllerRoot):
      
      def get(self, command:str):
            return self.post(command)
      
      def post(self, command:str):
            self._logger.debug(f"command {command} received")
            return self._messageBus.executeCommand(command), 200