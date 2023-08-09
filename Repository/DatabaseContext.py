from collections import defaultdict
from Models.Config import ConnectionString
from Models.Settings import Settings
import mysql.connector
from Models.DTO.dtos import Device, DataPoint
import logging


class DatabaseContext:
    QueryGetSettings = "SELECT `ID`,\
    `LowerTempSensor`,\
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
    `DataSaveInterval`\
    FROM `AppSettings` LIMIT 0,1"
    QueryUpdateSettings = "UPDATE AppSettings SET \
    `LowerTempSensor` = %(LowerTempSensor)s,\
    `HigherTempSensor`= %(HigherTempSensor)s,\
    `AmbientTempSensor`= %(AmbientTempSensor)s,\
    `LowerTempSensorOffset`= %(LowerTempSensorOffset)s,\
    `HigherTempSensorOffset`= %(HigherTempSensorOffset)s,\
    `AmbientTempSensorOffset`= %(AmbientTempSensorOffset)s,\
    `MinimumTempDiff`= %(MinimumTempDiff)s,\
    `MinimumAmbientTemp`= %(MinimumAmbientTemp)s,\
    `IsAuto`= %(IsAuto)s,\
    `DayStart`= %(DayStart)s,\
    `DayStop`= %(DayStop)s,\
    `DecisionDelay`= %(DecisionDelay)s,\
    `MeasurementSamplesCount`= %(MeasurementSamplesCount)s,\
    `MaxStateTime`= %(MaxStateTime)s,\
    `ControlInterval`= %(ControlInterval)s,\
    `DataSaveInterval`= %(DataSaveInterval)s\
    WHERE 1=1"
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
    QueryGetDevices = "SELECT D.`ID`, D.`Name` FROM `Devices` as D "
    QueryGetDevice = "SELECT D.`ID`, D.`Name` FROM `Devices` as D WHERE D.Name=%(Name)s"
    QueryInsertDevice = "INSERT INTO `Devices`(`Name`) VALUES (%(Name)s)"
    QueryInsertPoint = "INSERT INTO `DataPoints`(`EventTimeStamp`, `Value`, `DeviceID`, `DayIndx`, `IsWorking`)\
     VALUES (%(EventTimeStamp)s, %(Value)s,  %(DeviceID)s, %(DayIndx)s, %(IsWorking)s)"

    def __init__(self, connectionString: ConnectionString) -> None:
        self._connectionString: ConnectionString = connectionString
        self._logger = logging.getLogger(__name__)
        self._initialSettings: Settings = Settings()
        
    def getSettings(self, defaultSettings: Settings = None) -> Settings:
        cnx = None
        try:
            cnx = mysql.connector.connect(user=self._connectionString.User,
                                          password=self._connectionString.Password,
                                          host=self._connectionString.Host,
                                          database=self._connectionString.Database)
            cursor = cnx.cursor(dictionary=True)
            cursor.execute(DatabaseContext.QueryGetSettings)
            row = cursor.fetchone()
              
            if row is None or cursor.rowcount <= 0 and defaultSettings != NotImplemented:
                params = defaultSettings.toDictionary()
                cursor.execute(DatabaseContext.QueryInsertSettings, params)
                cnx.commit()
                cursor.execute(DatabaseContext.QueryGetSettings)
                self._initialSettings.update(defaultSettings)
            cursor.close()  
            if row is not None and isinstance(row, dict):
                self._initialSettings.update(row)
                return self._initialSettings
        except Exception as e:
            self._logger.critical(e, exc_info=True)
        finally:
            if cnx is not None:
                cnx.close()
        return None
    
    def getPoints(self, dayIndx: int, deviceId: int, maxTateTime: int) -> dict:
        cnx = None
        try:
            cnx = mysql.connector.connect(user=self._connectionString.User,
                                          password=self._connectionString.Password,
                                          host=self._connectionString.Host,
                                          database=self._connectionString.Database)
            query: str = "SELECT ID, EventTimeStamp, Value, DeviceID, DayIndx, IsWorking\
            FROM DataPoints \
            WHERE DayIndx = %(dayIndx)s and \
            IsWorking and \
            DeviceID=%(deviceID)s and \
            EventTimeStamp >= date_add(now(), INTERVAL  -%(maxTime)s minute) \
            order by EventTimeStamp desc limit 0, 30"
            cursor = cnx.cursor(dictionary=True)
            cursor.execute(query, {"dayIndx": dayIndx, "deviceID": deviceId, "maxTime": maxTateTime})
            rows = cursor.fetchall()
            result = {row["EventTimeStamp"]: DataPoint(row["EventTimeStamp"],
                                                       row["Value"],
                                                       row["DayIndx"],
                                                       row["IsWorking"],
                                                       deviceId) for row in rows}
            return result
        except Exception as e:
            self._logger.critical(e, exc_info=True)
        finally:
            if cnx is not None:
                cnx.close()
        return None
    
    def updateSettings(self, settings: Settings) -> None:
        self.__execute(DatabaseContext.QueryUpdateSettings, settings)        
    
    def createSettings(self, settings: Settings):
        self.__execute(DatabaseContext.QueryInsertSettings, settings)        
        
    def __execute(self, query: str, settings: Settings) -> None:
        cnx = None
        try:
            cnx = mysql.connector.connect(user=self._connectionString.User,
                                          password=self._connectionString.Password,
                                          host=self._connectionString.Host,
                                          database=self._connectionString.Database)
            cursor = cnx.cursor()
            cursor.execute(query, settings.toDictionary())
            cnx.commit()
            cursor.close()
        except Exception as e:
            self._logger.critical(e, exc_info=True)
            raise e
        finally:
            if cnx is not None:
                cnx.close()

    def getDevices(self) -> list:
        result: list
        cnx = None
        try:
            cnx = mysql.connector.connect(user=self._connectionString.User,
                                          password=self._connectionString.Password,
                                          host=self._connectionString.Host,
                                          database=self._connectionString.Database)
            cursor = cnx.cursor(dictionary=True)
            cursor.execute(DatabaseContext.QueryGetDevices)
            rows = cursor.fetchall()
            result = [Device(int(row["ID"]), str(row["Name"]), None) for row in rows]
        finally:
            if cnx is not None:
                cnx.close()

        return result

    def deleteOldMeasurements(self, dayIndex: int) -> None:
        cnx = None
        try:
            cnx = mysql.connector.connect(user=self._connectionString.User,
                                          password=self._connectionString.Password,
                                          host=self._connectionString.Host,
                                          database=self._connectionString.Database)
            cursor = cnx.cursor()
            cursor.execute("delete from DataPoints where DayIndx <=  %(DayIndx)s", {"DayIndx": dayIndex})
            cnx.commit()
            cursor.close()
        finally:
            if cnx is not None:
                cnx.close()
           
    def getPointsQuantity(self, dayIndx: int, deviceId: int) -> int:
        cnx = None
        try:
            cnx = mysql.connector.connect(user=self._connectionString.User,
                                          password=self._connectionString.Password,
                                          host=self._connectionString.Host,
                                          database=self._connectionString.Database)
            cursor = cnx.cursor(dictionary=False)
            cursor.execute("SELECT count(*) \
            FROM DataPoints \
            WHERE DeviceID=%(deviceID)s and DayIndx= %(dayIndx)s and IsWorking=1",
                           {"dayIndx": dayIndx, "deviceID": deviceId})
            row = cursor.fetchone()
            cursor.close()
            return row[0]
        except Exception as e:
            self._logger.critical(e, exc_info=True)
            raise e
        finally:
            if cnx is not None:
                cnx.close()
     
    def synchronizeDevices(self, physicalDeviceNamesList: list) -> dict:
        result = defaultdict()
        cnx = None
        try:
            cnx = mysql.connector.connect(user=self._connectionString.User,
                                          password=self._connectionString.Password,
                                          host=self._connectionString.Host,
                                          database=self._connectionString.Database)
            cursor = cnx.cursor(dictionary=True)
            for name in physicalDeviceNamesList:
                cursor.execute(DatabaseContext.QueryGetDevice, {"Name": name})
                rows = cursor.fetchall()
                idDevice: int
                points = list()
                if len(rows) == 0:
                    cursor.execute(DatabaseContext.QueryInsertDevice, {"Name": name})
                    idDevice = cursor._last_insert_id
                    cnx.commit()
                else:
                    idDevice = int(rows[0]["ID"])
                    points = None
                newDevice = Device(idDevice, name, points)
                result[name] = newDevice
            cursor.close()
        finally:
            if cnx is not None:
                cnx.close()

        return result

    def storeDataPoints(self, points: list) -> None:
        try:
            cnx = mysql.connector.connect(user=self._connectionString.User,
                                          password=self._connectionString.Password,
                                          host=self._connectionString.Host,
                                          database=self._connectionString.Database)
            rows = [{"EventTimeStamp": point.EventTimeStamp,
                     "Value": point.Value,
                     "DeviceID": point.DeviceID,
                     "DayIndx": (int(point.EventTimeStamp.year)*10000 +
                                 int(point.EventTimeStamp.month)*100 +
                                 point.EventTimeStamp.day),
                     "IsWorking": point.IsWorking} for point in points]
            
            cursor = cnx.cursor()
            cursor.executemany(DatabaseContext.QueryInsertPoint, rows)
            cnx.commit()
            cursor.close()
        except Exception as e:
            self._logger.critical(e, exc_info=True)
            raise e
        finally:
            cnx.close()
