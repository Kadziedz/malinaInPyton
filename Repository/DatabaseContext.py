from collections import defaultdict
from Interfaces.IGauge import IGauge
from Models.Config import ConnectionString
from Models.Settings import Settings
import mysql.connector
from Models.DTO.mysql import Device, DataPoint
import logging
from datetime import datetime


class DatabaseContext:
    QueryGetSettings = "SELECT `ID`, `LowerTempSensor`, `HigherTempSensor`, `AmbientTempSensor`, `LowerTempSensorOffset`, `HigherTempSensorOffset`, `AmbientTempSensorOffset`, `MinimumTempDiff`, `MinimumAmbientTemp`, `IsAuto`, `DayStart`, `DayStop`, `DecisionDelay`, `MeasurementSamplesCount`, `MaxStateTime`, `ControlInterval`, `DataSaveInterval` FROM `AppSettings` LIMIT 0,1"
    QueryInsertSettings = "INSERT INTO AppSettings(\
        `LowerTempSensor`, \
        `HigherTempSensor`,\
        `AmbientTempSensor`,\
        `LowerTempSensorOffset`,\
        `HigherTempSensorOffset`,\
        `AmbientTempSensorOffset`,\
        `MinimumTempDiff`,\
        `MinimumAmbientTemp`,\
        `IsAuto`,\
        `DayStart`,\
        `DayStop`,\
        `DecisionDelay`,\
        `MeasurementSamplesCount`,\
        `MaxStateTime`,\
        `ControlInterval`,\
        `DataSaveInterval`) \
        VALUES\
        (%(LowerTempSensor)s,\
        %(HigherTempSensor)s,\
        %(AmbientTempSensor)s,\
        %(LowerTempSensorOffset)s,\
        %(HigherTempSensorOffset)s,\
        %(AmbientTempSensorOffset)s,\
        %(MinimumTempDiff)s,\
        %(MinimumAmbientTemp)s,\
        %(IsAuto)s,\
        %(DayStart)s,\
        %(DayStop)s,\
        %(DecisionDelay)s,\
        %(MeasurementSamplesCount)s,\
        %(MaxStateTime)s,\
        %(ControlInterval)s,\
        %(DataSaveInterval)s)"
    QueryGetDeviceAndMeasurements = "SELECT D.`ID`, D.`Name`, P.EventTimeStamp, P.Value, P.DayIndx, P.IsWorking FROM `Devices` as D left join DataPoints as P on D.ID=P.ID WHERE D.Name=%(Name)s order by P.EventTimeStamp desc"
    QueryInsertDevice = "INSERT INTO `Devices`(`Name`) VALUES (%(Name)s)"

    def __init__(self, connectionString: ConnectionString) -> None:
        self._connectionString: ConnectionString = connectionString
        self._logger = logging.getLogger(__name__)
        self._initialSettings:Settings = Settings()
        
    def getSettings(self, defaultSettings: Settings=None) -> Settings:
        try:
            cnx = mysql.connector.connect(user=self._connectionString.User,
                                          password=self._connectionString.Password,
                                          host=self._connectionString.Host,
                                          database=self._connectionString.Database)
            cursor = cnx.cursor(dictionary=True)
            cursor.execute(DatabaseContext.QueryGetSettings)
            row = cursor.fetchone()
            if row == None or cursor.rowcount <= 0 and defaultSettings!= NotImplemented:
                params = defaultSettings.toDictionary()
                cursor.execute(DatabaseContext.QueryInsertSettings, params)
                cnx.commit()
                cursor.execute(DatabaseContext.QueryGetSettings)
                self._initialSettings.update(defaultSettings)
                
            if row!=None and isinstance(row, dict):
                self._initialSettings.update(row)
            cursor.close()
        except Exception as e:
            self._logger.critical(e, exc_info=True)
            raise e
        finally:
            cnx.close()
            return self._initialSettings

    def setSettings(self, settings: Settings) -> bool:
        try:
            cnx = mysql.connector.connect(user=self._connectionString.User,
                                          password=self._connectionString.Password,
                                          host=self._connectionString.Host,
                                          database=self._connectionString.Database)
            cursor = cnx.cursor()
            cursor.execute(DatabaseContext.QueryInsertSettings,
                           settings.toDictionary())
            cursor.close()
        finally:
            cnx.close()

    def getDevices(self, physicalDeviceNamesList:list) -> dict:
        result = defaultdict()
        try:
            cnx = mysql.connector.connect(user=self._connectionString.User,
                                          password=self._connectionString.Password,
                                          host=self._connectionString.Host,
                                          database=self._connectionString.Database)
            cursor = cnx.cursor(dictionary=True)
            for name in physicalDeviceNamesList:
                cursor.execute(
                    DatabaseContext.QueryGetDeviceAndMeasurements, {"Name": name})
                rows = cursor.fetchall()
                idDevice = 0
                points = list()
                if len(rows) == 0:
                    cursor.execute(DatabaseContext.QueryInsertDevice, {"Name": name})
                    idDevice = cursor._last_insert_id
                    cnx.commit()
                else:
                    idDevice = int(rows[0]["ID"])
                    points = [DataPoint(item["EventTimeStamp"],  float(item["Value"]), int(item['DayIndx']), bool(item['IsWorking'])) for item in rows if item["Value"]!= None]
                newDevice = Device(idDevice, name, points)
                result[name]= newDevice
            cursor.close()
        finally:
            cnx.close()

        return result
