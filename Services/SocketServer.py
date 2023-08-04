#!/usr/bin/env python
#from collections.abc import Callable, Iterable, Mapping
import json
from typing import Any
import websockets
import logging
from collections import defaultdict
from threading import Lock, Thread
from Interfaces.IContainer import IContainer
from Interfaces.IMessageBus import IMessageBus
from websockets.sync.server import WebSocketServer, ServerConnection

#https://docs.python.org/3/library/asyncio-eventloop.html#running-and-stopping-the-loop
#https://websockets.readthedocs.io/en/stable/reference/sync/server.html#

class SocketServer(Thread):
    EVENT_NEW_SOCKET_MESSAGE:str= "onNewSocketMessage"
    
    def __init__(self, ioc:IContainer, ip:str="127.0.0.1", port:int=8351) -> None:
        super().__init__()
        self._logger = logging.getLogger(__class__.__name__)
        self._lock: Lock = Lock()
        self.__isTerminateRequested:bool = False
        self.__port = port
        self._messageBus:IMessageBus = ioc.getInstance(IMessageBus)
        self._socketServer:WebSocketServer = websockets.sync.server.serve(self.handler, ip, self.__port) #websockets.serve(self.handler, ip, self.__port)
        self._clients:dict = defaultdict()
         
    def handler(self, websocket:ServerConnection):
        clientID = str(websocket.id)
        clientIP = str(websocket.remote_address)
        with self._lock:
            self._clients[clientID]= websocket
        self._logger.info(f"handling connection from {clientIP} is started")
        try:
            while not self.isTerminateRequested():
                try:
                    message = websocket.recv()
                    rawJson = json.loads(message)
                    self._logger.warn(f"message received from {clientIP}: {rawJson}")
                    self._messageBus.sendNamedEvent(SocketServer.EVENT_NEW_SOCKET_MESSAGE, rawJson)
                except websockets.ConnectionClosedOK:
                    break
                except Exception as e:
                    self._logger.error(e, exc_info=True)
        finally:
            with self._lock:
                self._clients.pop(clientID)
        self._logger.info(f"connection from {clientIP} is closed")
    
    def __del__(self):
        self.__disposeAsyncLoop()
        self._logger.info("websocket server destructor")
        
    def isTerminateRequested(self)->bool:
        result:bool= False
        with self._lock :
            result = self.__isTerminateRequested
        return result
    
    def sendMessage(self, message:dict)->None:
       # self._logger.info(f"sending message to the  {len(self._clients)} clients {message}")
        with self._lock :
            for key in self._clients:
                connection:ServerConnection = self._clients[key]
                connection.send(json.dumps(message))

    def requestStop(self)->None:
        self._logger.info("stop request...")
        with self._lock:
            self.__isTerminateRequested = True
            for key in self._clients:
                connection:ServerConnection = self._clients[key]
                #connection.close_socket()
                connection.close()
            self._clients.clear()
        self.__disposeAsyncLoop()        
    
    def __disposeAsyncLoop(self)->None:
        self._socketServer.shutdown()
        self._logger.info("websocket server loop is stopped")
    
    def run(self) -> None:
        self._socketServer.serve_forever()
