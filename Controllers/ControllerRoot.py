from flask_restful import Resource
from flask import request
import logging
from Interfaces.IMessageBus import IMessageBus

class ControllerRoot(Resource):
      def __init__(self, messageBus: IMessageBus) -> None:
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self._messageBus: IMessageBus = messageBus