import os
import glob
from collections import defaultdict
from os.path import exists
from Interfaces.ISensor import ISensor


class Sensor(ISensor):
    BASE_DIR = '/sys/bus/w1/devices/'
    
    def __init__(self, sensorLocation) -> None:
        self.__sensorLocation = sensorLocation + '/w1_slave'
        nameFile = sensorLocation+'/name'
        f = open(nameFile, 'r')
        self.SensorName = f.readline().strip()
        f.close()
      
    @staticmethod
    def getDevices() -> dict:
        os.system('modprobe w1-therm')
        result = defaultdict()
        files = glob.glob(Sensor.BASE_DIR + '28*')
        if len(files) > 0:
            for candidate in files:
                newGauge = Sensor(candidate)
                result[newGauge.SensorName] = newGauge
                
        return result
            
    def measure(self) -> float:
        if not exists(self.__sensorLocation):
            return -1
        lines = self.__readRawTemperature()
        if len(lines) == 2 and lines[0].strip().lower().endswith("yes"):
            tempPosition = lines[1].find('t=')
            if tempPosition != -1:
                tempString = lines[1][tempPosition+2:]
                return float(tempString) / 1000.0
        return -1
        
    def __readRawTemperature(self):
        f = open(self.__sensorLocation, 'r')
        lines = f.readlines()
        f.close()
        return lines
