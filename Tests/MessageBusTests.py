import unittest
from Interfaces.IMessageBus import IMessageBus
from Services.MessageBus import MessageBus

class MessageBusTests(unittest.TestCase):
    def test_registerEventAsString_HandlerCalledOnEvent(self):
        # arrange
        localEventArg = None
        
        def handler(receivedEvent):
            localEventArg = receivedEvent
            
        mb: MessageBus = MessageBus()
        eventType:str ="foo"
        mb.register(eventType, handler)
        eventObject = "aaaa"
        
        # act
        mb.sendNamedEvent(eventType, eventObject)
        
        # assert
        self.assertIsNotNone(localEventArg)
        self.assertEqual(eventObject)
        