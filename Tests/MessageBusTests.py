import unittest
from Interfaces.IMessageBus import IMessageBus
from Services.MessageBus import MessageBus
from parameterized import parameterized


class CustomEvent:
    
    def __init__(self, identifier: int) -> None:
        self.identifier: int = identifier
        
    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, CustomEvent) and self.identifier == __value.identifier


class MessageBusTests(unittest.TestCase):

    @parameterized.expand([ 
        ("aaaa", "foo"),
        ("aaaa", 1),
        ("aaaa", (1, 2, 3)),
        ("aaaa", [1, 2, 3]),
        ("aaaa", {1: "aaa", 2: "bbb", "foo": "bar"}),
        ("aaa", CustomEvent(1))
    ])
    def test_RegisterHanlerUsingString_HandlerCalledOnEvent(self, eventType: str, eventObject):
        # arrange
        localEventArg = None
        
        def handler(receivedEvent):
            nonlocal localEventArg 
            localEventArg = receivedEvent
            
        mb: MessageBus = MessageBus()
        mb.register(eventType, handler)
        
        # act
        mb.sendNamedEvent(eventType, eventObject)
        
        # assert
        self.assertIsNotNone(localEventArg)
        if isinstance(eventObject, list):
            self.assertListEqual(eventObject, localEventArg)
        if isinstance(eventObject, dict):
            self.assertDictEqual(eventObject, localEventArg)
        if isinstance(eventObject, tuple):
            self.assertTupleEqual(eventObject, localEventArg)
        else:
            self.assertEqual(eventObject, localEventArg)
    
    @parameterized.expand([ 
        ("aaaa", "foo"),
        ("aaaa", 1),
        ("aaaa", (1, 2, 3)),
        ("aaaa", [1, 2, 3]),
        ("aaaa", {1: "aaa", 2: "bbb", "foo": "bar"}),
        ("aaa", CustomEvent(1))
    ])
    def test_RegisterHanlerUsingString_NoHandlerCalledAfterUnregister(self, eventType: str, eventObject):
        # arrange
        localEventArg = None
        secondEventArg = "dummy object"
        
        def handler(receivedEvent):
            nonlocal localEventArg 
            localEventArg = receivedEvent
            
        mb: MessageBus = MessageBus()
        mb.register(eventType, handler)
        
        # act
        mb.sendNamedEvent(eventType, eventObject)
        mb.unregister(eventType, handler)
        mb.sendNamedEvent(eventType, secondEventArg)
        
        # assert
        self.assertIsNotNone(localEventArg)
        self.assertIsNotNone(secondEventArg)
        if isinstance(eventObject, list):
            self.assertListEqual(eventObject, localEventArg)
        if isinstance(eventObject, dict):
            self.assertDictEqual(eventObject, localEventArg)
        if isinstance(eventObject, tuple):
            self.assertTupleEqual(eventObject, localEventArg)
        else:
            self.assertEqual(eventObject, localEventArg)  
        
    @parameterized.expand([ 
        ("aaaa", "foo"),
        ("aaaa", 1),
        ("aaaa", (1, 2, 3)),
        ("aaaa", [1, 2, 3]),
        ("aaaa", {1: "aaa", 2: "bbb", "foo": "bar"}),
        ("aaa", CustomEvent(1))
    ]) 
    def test_RegisterMultipleHandlersUsingString_MultipleHandlerCalledOnEvent(self, eventType: str, eventObject):
        # arrange
        localEventArg1 = None
        localEventArg2 = None
        
        def handler1(receivedEvent):
            nonlocal localEventArg1 
            localEventArg1 = receivedEvent
        
        def handler2(receivedEvent):
            nonlocal localEventArg2 
            localEventArg2 = receivedEvent
            
        mb: MessageBus = MessageBus()
        mb.register(eventType, handler1)
        mb.register(eventType, handler2)
        
        # act
        mb.sendNamedEvent(eventType, eventObject)
        
        # assert
        self.assertIsNotNone(localEventArg1)
        self.assertIsNotNone(localEventArg2)
        if isinstance(eventObject, list):
            self.assertListEqual(eventObject, localEventArg1)
            self.assertListEqual(eventObject, localEventArg2)
        if isinstance(eventObject, dict):
            self.assertDictEqual(eventObject, localEventArg1)
            self.assertDictEqual(eventObject, localEventArg2)
        if isinstance(eventObject, tuple):
            self.assertTupleEqual(eventObject, localEventArg1)
            self.assertTupleEqual(eventObject, localEventArg2)
        else:
            self.assertEqual(eventObject, localEventArg1)
            self.assertEqual(eventObject, localEventArg2)    
        
    @parameterized.expand([ 
        ("aaaa", "foo"),
        ("aaaa", 1),
        ("aaaa", (1, 2, 3)),
        ("aaaa", [1, 2, 3]),
        ("aaaa", {1: "aaa", 2: "bbb", "foo": "bar"}),
        ("aaa", CustomEvent(1))
    ]) 
    def test_RegisterMultipleHandlersUsingString_SecondHanlerNotCalledAfterUnregister(self, eventType: str, eventObject):
        # arrange
        localEventArg1 = None
        localEventArg2 = None
        firstEventArg = "first Event argument"
       
        def handler1(receivedEvent):
            nonlocal localEventArg1 
            localEventArg1 = receivedEvent
        
        def handler2(receivedEvent):
            nonlocal localEventArg2 
            localEventArg2 = receivedEvent
            
        mb: MessageBus = MessageBus()
        mb.register(eventType, handler1)
        mb.register(eventType, handler2)
        
        # act
        mb.sendNamedEvent(eventType, firstEventArg)
        mb.unregister(eventType, handler2)
        mb.sendNamedEvent(eventType, eventObject)
        
        # assert
        self.assertIsNotNone(localEventArg1)
        self.assertIsNotNone(localEventArg2)
        self.assertIsNot(localEventArg1, firstEventArg)
        self.assertIs(localEventArg2, firstEventArg) 
         
        if isinstance(eventObject, list):
            self.assertListEqual(eventObject, localEventArg1)
        if isinstance(eventObject, dict):
            self.assertDictEqual(eventObject, localEventArg1)
        if isinstance(eventObject, tuple):
            self.assertTupleEqual(eventObject, localEventArg1)
        else:
            self.assertEqual(eventObject, localEventArg1)
  
        
    @parameterized.expand([ 
        (CustomEvent(10)),
        (CustomEvent(11)),
        (CustomEvent(12))
    ])
    def test_RegisterHandlerUsingObject_HandlerCalledOnEvent(self, eventObject):
        # arrange
        localEventArg = None
        
        def handler(receivedEvent):
            nonlocal localEventArg 
            localEventArg = receivedEvent
            
        mb: MessageBus = MessageBus()
        mb.register(eventObject, handler)
        
        # act
        mb.sendEvent(eventObject)
        
        # assert
        self.assertIsNotNone(localEventArg)
        if isinstance(eventObject, list):
            self.assertListEqual(eventObject, localEventArg)
        if isinstance(eventObject, dict):
            self.assertDictEqual(eventObject, localEventArg)
        if isinstance(eventObject, tuple):
            self.assertTupleEqual(eventObject, localEventArg)
        else:
            self.assertEqual(eventObject, localEventArg)
            
    @parameterized.expand([ 
        ("aaaa", "foo", CustomEvent(21)),
        ("aaaa", 1, CustomEvent(22)),
        ("aaaa", (1, 2, 3), CustomEvent(23)),
        ("aaaa", [1, 2, 3], CustomEvent(24)),
        ("aaaa", {1: "aaa", 2: "bbb", "foo": "bar"}, CustomEvent(25)),
        ("aaa", CustomEvent(1), CustomEvent(26) )
    ])
    
    def test_RegisterHandlersForTwoEwents_EachHandlerCalledForValidEvent(self, event1Type: str, event1Object, event2Object):
        # arrange
        localEventArg1 = None
        localEventArg2 = None
        
        def handler1(receivedEvent):
            nonlocal localEventArg1 
            localEventArg1 = receivedEvent
        
        def handler2(receivedEvent):
            nonlocal localEventArg2 
            localEventArg2 = receivedEvent
            
        mb: MessageBus = MessageBus()
        mb.register(event1Type, handler1)
        mb.register(event2Object, handler2)
        
        # act
        mb.sendNamedEvent(event1Type, event1Object)
        mb.sendEvent(event2Object)
        
        # assert
        self.assertIsNotNone(localEventArg1)
        if isinstance(event1Object, list):
            self.assertListEqual(event1Object, localEventArg1)
        if isinstance(event1Object, dict):
            self.assertDictEqual(event1Object, localEventArg1)
        if isinstance(event1Object, tuple):
            self.assertTupleEqual(event1Object, localEventArg1)
        else:
            self.assertEqual(event1Object, localEventArg1)

        self.assertIsNotNone(localEventArg2)
        if isinstance(event2Object, list):
            self.assertListEqual(event2Object, localEventArg2)
        if isinstance(event2Object, dict):
            self.assertDictEqual(event2Object, localEventArg2)
        if isinstance(event2Object, tuple):
            self.assertTupleEqual(event2Object, localEventArg2)
        else:
            self.assertEqual(event2Object, localEventArg2)       
        