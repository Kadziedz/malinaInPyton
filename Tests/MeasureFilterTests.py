#!/usr/bin/env python
from datetime import datetime
from Interfaces.IActualDateProvider import IActualDateProvider
from Interfaces.IContainer import IContainer
from Services.SimpleIoc import SimpleIoC
from parameterized import parameterized
import unittest
import random
from Services.MeasurementFilter import MeasurementFilter
from Interfaces.IMeasurementFilter import IMeasurementFilter
#https://realpython.com/python-testing/
#https://stackoverflow.com/questions/32899/how-do-you-generate-dynamic-parameterized-unit-tests-in-python

class FakeDateProvider(IActualDateProvider):
    
    def __init__(self) -> None:
        super().__init__()
        self.__date = datetime(2023, 1,1,13,0,0,0)
    
    def getActualDate(self) -> datetime:
        return self.__date
    
    def setDate(self, actualDate:datetime)->None:
        self.__date = actualDate

# def setUpModule():
    # print('Running setUpModule')


# def tearDownModule():
    # print('Running tearDownModule')

class TestMeasurementFilterTest(unittest.TestCase):
    # @classmethod
    # def setUpClass(cls):
        # print('Running setUpClass')

    # @classmethod
    # def tearDownClass(cls):
        # print('Running tearDownClass')
    
    def setUp(self):
        self._dateProvider.setDate(datetime(2023, 1,1,13,0,0,0))

    # def tearDown(self):
        # print('Running tearDown')
    
    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        self._ioc = SimpleIoC()
        self._dateProvider = FakeDateProvider()
        self._ioc.registerSingleton(IActualDateProvider, self._dateProvider)
        
    @parameterized.expand([
        ("foo", list(),  None),
        ("foo", list([1.0]),  1.0),
        ("foo", (2.0, 4.0), 3.0),
        ("foo", (2.0, 4.0, 6.0), 4.0),
        ("foo", (2.0, 4.0, 6.0, 8.0), 5.0),
        ("foo", (2.0, 4.0, 6.0, 8.0, 10.0), 6.0),
        ("foo", (2.0, 4.0, 6.0, 8.0, 10.0, 12.0), 8.0),
        ("foo", (2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0), 10.0),
        ("foo", (2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0), 12.0),
        ("foo", (2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0), 14.0)
    ])
    def test_RequestExistingSensorValue_ValidResultReceived(self, label:str, sequence:list, expectedValue:float):
        """
        test filtering for one sensor
        """            
        #arrange
        filter:MeasurementFilter = MeasurementFilter(self._ioc)
        
        #act
        for number in sequence:
            filter.updateMeasurements(label, number, 5)
        filteredOne:float = filter.get(label)    
        
        #assert
        self.assertEqual(filteredOne, expectedValue, "filtered value should have expected value")

    @parameterized.expand([
        ("foo", list(),  None),
        ("foo", list([1.0]),   None),
        ("foo", (2.0, 4.0),  None),
        ("foo", (2.0, 4.0, 6.0),  None),
        ("foo", (2.0, 4.0, 6.0, 8.0),  None),
        ("foo", (2.0, 4.0, 6.0, 8.0, 10.0),  None),
        ("foo", (2.0, 4.0, 6.0, 8.0, 10.0, 12.0),  None),
        ("foo", (2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0),  None),
        ("foo", (2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0),  None),
        ("foo", (2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0),  None)
    ])
    def test_RequestNonExistingSensorValue_NoneReceived(self, label:str, sequence:list, expectedValue:float):
        """
        test filtering for one sensor but querying non existing one
        """            
        #arrange
        filter:MeasurementFilter = MeasurementFilter(self._ioc)
        
        #act
        for number in sequence:
            filter.updateMeasurements(label, number, 5)
        filteredOne:float = filter.get("bar")    
        
        #assert
        self.assertEqual(filteredOne, expectedValue, "filtered value should have expected value")
        
        
    @parameterized.expand([
        (1,1),
        (3,3),
        (5,5),
        (10,10),
        (1,20),
        (3,20),
        (5,20),
        (10,20),
        (20,1),
        (20,3),
        (20,5),
        (20,10),
    ])
    def test_RequestNonExistingSensorValue_NoneReceived(self, fooLen:int, barLen:int):
        """
        test filtering for two sensors
        """            
        #arrange
        filter:MeasurementFilter = MeasurementFilter(self._ioc)
        fooLabel:str= "fooLabel"
        barLabel:str= "barLabel"
        generator:random.Random = random.Random()
        fooElements:list = list()
        barElements:list = list()
        
        #act
        for number in range(fooLen):
            num:float = generator.random()
            filter.updateMeasurements(fooLabel, num, 5)
            fooElements.append(num)
            
        for number in range(barLen):
            num:float = generator.random()
            filter.updateMeasurements(barLabel, num, 5)
            barElements.append(num)
            
        expectedFoo = sum(fooElements)/len(fooElements) if len(fooElements)<5 else sum(fooElements[-5:])/5
        expectedBar = sum(barElements)/len(barElements) if len(barElements)<5 else sum(barElements[-5:])/5
        
        filteredFoo:float = filter.get(fooLabel)    
        filteredBar:float = filter.get(barLabel)    
        
        #assert
        self.assertEqual(filteredFoo, expectedFoo, "filteredFoo value should have expected value")
        self.assertEqual(filteredBar, expectedBar, "filteredBar value should have expected value")
        
    def test_MakeTailLenShorter_ValidResultReceived(self):
        """make tail length shorter during work
        """
        #arrange
        sequence:list = (2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0)
        filter:MeasurementFilter = MeasurementFilter(self._ioc)
        label:str ="foo"
        expectedValue1 = 10
        expectedValue2 = 16
        
        #act
        for number in sequence:
            filter.updateMeasurements(label, number, 10)
        
        filtered1 = filter.get(label)
        filter.updateMeasurements(label, 20.0, 5)    
        filtered2 = filter.get(label)
        
        #assert
        self.assertEqual(filtered1, expectedValue1, "filtered value should have expected value")
        self.assertEqual(filtered2, expectedValue2, "filtered value should have expected value")
        
    def test_ReadAfterLongTime_OldDataRemoved(self):
        """read date after time boundary 
        """
        #arrange
        self._dateProvider.setDate(datetime(2023, 1,1,13,0,0,0))

        sequence:list = (2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0)
        filter:MeasurementFilter = MeasurementFilter(self._ioc)
        label:str ="foo"
        expectedValue1 = None
        #act
        for number in sequence:
            filter.updateMeasurements(label, number, 5)
        self._dateProvider.setDate(datetime(2023, 1,1,13,MeasurementFilter.HISTORY_VALID_BOUNDARY+1,0,0))
        filtered1 = filter.get(label)

        #assert
        self.assertEqual(filtered1, expectedValue1, "filtered value should have expected value")
        
    def test_ReadAfterLongTime_OldDataRemovedAndNewUsed(self):
        """ store data after time boundary,m only new data should be used
        """
        #arrange
        self._dateProvider.setDate(datetime(2023, 1,1,13,0,0,0))

        sequence:list = (2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0)
        filter:MeasurementFilter = MeasurementFilter(self._ioc)
        label:str ="foo"
        expectedValue1 = None
        expectedValue2 = 12
        #act
        for number in sequence:
            filter.updateMeasurements(label, number, 5)
        self._dateProvider.setDate(datetime(2023, 1,1,13,MeasurementFilter.HISTORY_VALID_BOUNDARY+1,0,0))
        filtered1 = filter.get(label)
        filter.updateMeasurements(label, 10, 5)
        filter.updateMeasurements(label, 12, 5)
        filter.updateMeasurements(label, 14, 5)
        filtered2 = filter.get(label)

        #assert
        self.assertEqual(filtered1, expectedValue1, "filtered value should have expected value")
        self.assertEqual(filtered2, expectedValue2, "filtered value should have expected value")