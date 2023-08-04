#!/usr/bin/env python
from parameterized import parameterized, parameterized_class
import unittest
import random
from Services.MeasurementFilter import MeasurementFilter
from Interfaces.IMeasurementFilter import IMeasurementFilter
#https://realpython.com/python-testing/
#https://stackoverflow.com/questions/32899/how-do-you-generate-dynamic-parameterized-unit-tests-in-python

class TestMeasurementFilterTest(unittest.TestCase):

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
        filter:MeasurementFilter = MeasurementFilter()
        
        #act
        for number in sequence:
            filter.updateMeasurements(label, number, 5)
        filteredOne:float = filter.Get(label)    
        
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
        test filtering for one sensor
        """            
        #arrange
        filter:MeasurementFilter = MeasurementFilter()
        
        #act
        for number in sequence:
            filter.updateMeasurements(label, number, 5)
        filteredOne:float = filter.Get("bar")    
        
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
        test filtering for one sensor
        """            
        #arrange
        filter:MeasurementFilter = MeasurementFilter()
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
        
        filteredFoo:float = filter.Get(fooLabel)    
        filteredBar:float = filter.Get(barLabel)    
        
        #assert
        self.assertEqual(filteredFoo, expectedFoo, "filteredFoo value should have expected value")
        self.assertEqual(filteredBar, expectedBar, "filteredBar value should have expected value")