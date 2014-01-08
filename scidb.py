import sqlite3
import sys
datConn = None
tmpConn = None

try:
    datConn = sqlite3.connect('sci_data.db')
    datConn.execute('pragma foreign_keys=ON') # enforce foreign keys
    # check that foreign keys constraint was correctly set
    rslt = datConn.execute('pragma foreign_keys')
    # if foreign_keys is supported, should have one item that is either (1,) or (0,)
    rl = [r for r in rslt] # comprehend it as a list
    if len(rl) == 0:
        print 'Foreign keys not supported in this version of sqlite. Not used in "sci_data.db".'
    if rl[0] != (1,):
        print 'Foreign keys supported, but not set in this connection to "sci_data.db"'
    datConn.execute('pragma auto_vacuum=ON')
    datConn.text_factory = str

    curD = datConn.cursor()

    curD.executescript("""
        CREATE TABLE IF NOT EXISTS "Loggers"
        ("ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
        "LoggerSerialNumber" VARCHAR(32) NOT NULL UNIQUE);
        """)

    curD.executescript("""
        CREATE TABLE IF NOT EXISTS "Sensors"
        ("ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
        "SensorSerialNumber" VARCHAR(32) NOT NULL UNIQUE);
        """)

    curD.executescript("""
        CREATE TABLE IF NOT EXISTS "DataTypes"
        ("ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
        "TypeText" VARCHAR(50) NOT NULL UNIQUE);
        """)

    curD.executescript("""
        CREATE TABLE IF NOT EXISTS "DataUnits"
        ("ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
        "UnitsText" VARCHAR(50) NOT NULL  UNIQUE );
        """)

    curD.executescript("""
        CREATE TABLE IF NOT EXISTS "DataChannels" 
        ("ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
        "Column" INTEGER NOT NULL ,
        "LoggerID" INTEGER NOT NULL ,
        "SensorID" INTEGER NOT NULL  DEFAULT 0,
        "DataTypeID" INTEGER NOT NULL ,
        "DataUnitsID" INTEGER NOT NULL ,
        "UTC_Offset" INTEGER NOT NULL  DEFAULT 0,
        FOREIGN KEY("LoggerID") REFERENCES Loggers("ID"),
        FOREIGN KEY("SensorID") REFERENCES Sensors("ID"),
        FOREIGN KEY("DataTypeID") REFERENCES DataTypes("ID"),
        FOREIGN KEY("DataUnitsID") REFERENCES DataUnits("ID")
        );
        """)

    curD.executescript("""
        CREATE TABLE IF NOT EXISTS "Data" (
        "ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
        "UTTimestamp" DATETIME NOT NULL ,
        "ChannelID" INTEGER NOT NULL ,
        "Value" FLOAT NOT NULL ,
        "Use" BOOL NOT NULL  DEFAULT 1,
        FOREIGN KEY("ChannelID") REFERENCES DataChannels("ID")
        );
        """)

    curD.executescript("""
        CREATE UNIQUE INDEX IF NOT EXISTS "Data_NoDup_TimeChan"
        ON "Data"
        ("UTTimestamp" ASC, "ChannelID" ASC);
        """)

    curD.executescript("""
        CREATE TABLE IF NOT EXISTS "DataDates" 
        ("Date" DATETIME PRIMARY KEY  NOT NULL  UNIQUE );
        """)

    curD.executescript("""
        CREATE TABLE IF NOT EXISTS "FieldSites" (
        "ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
        "SiteName" VARCHAR(50) NOT NULL UNIQUE,
        "LatitudeDecDegrees" FLOAT,
        "LongitudeDecDegrees" FLOAT,
        "UTC_Offset" INTEGER
        );
        """)

    curD.executescript("""
        CREATE TABLE IF NOT EXISTS "StationSpecs"
        ("ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
        "InstrumentSpec" VARCHAR(255) NOT NULL UNIQUE);
        """)

    curD.executescript("""
        CREATE TABLE IF NOT EXISTS "Stations" (
        "ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
        "StationName" VARCHAR(25) NOT NULL UNIQUE,
        "SiteID" INTEGER,
        "LatitudeDecDegrees" FLOAT,
        "LongitudeDecDegrees" FLOAT,
        "InstrumentSpecID" INTEGER,
        FOREIGN KEY("SiteID") REFERENCES FieldSites("ID"),
        FOREIGN KEY("InstrumentSpecID") REFERENCES StationSpecs("ID")
        );
        """)

    curD.executescript("""
        CREATE TABLE IF NOT EXISTS "DataSeriesSpecs"
        ("ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
        "DeviceSpec" VARCHAR(255) NOT NULL UNIQUE);
        """)

    curD.executescript("""
        CREATE TABLE IF NOT EXISTS "DataSeries" (
        "ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
        "DataSeriesDescription" VARCHAR(30) NOT NULL UNIQUE,
        "DeviceSpecID" INTEGER,
        FOREIGN KEY("DeviceSpecID") REFERENCES DataSeriesSpecs("ID")
        );
        """)

    curD.executescript("""
        CREATE TABLE IF NOT EXISTS "ChannelSegments" (
        "ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
        "ChannelID" INTEGER NOT NULL ,
        "SegmentBegin" DATETIME NOT NULL ,
        "SegmentEnd" DATETIME,
        "StationID" INTEGER,
        "SeriesID" INTEGER,
        FOREIGN KEY("ChannelID") REFERENCES DataChannels("ID")
        FOREIGN KEY("StationID") REFERENCES Stations("ID")
        FOREIGN KEY("SeriesID") REFERENCES DataSeries("ID")
        );
        """)

except sqlite3.Error, e:
    print 'Error in "sci_data.db": %s' % e.args[0]
    sys.exit(1)

try:
    tmpConn = sqlite3.connect('tmp.db')
    tmpConn.execute('pragma foreign_keys=ON')
    # check that foreign keys constraint was correctly set
    rslt = tmpConn.execute('pragma foreign_keys')
    # if foreign_keys is supported, should have one item that is either (1,) or (0,)
    rl = [r for r in rslt] # comprehend it as a list
    if len(rl) == 0:
        print 'Foreign keys not supported in this version of sqlite. Not used in "tmp.db".'
    if rl[0] != (1,):
        print 'Foreign keys supported, but not set in this connection to "tmp.db"'
        
    tmpConn.execute('pragma auto_vacuum=ON')
    tmpConn.text_factory = str

    curT = tmpConn.cursor()

    curT.executescript("""
        CREATE TABLE IF NOT EXISTS "Text"
        ("ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
        "Line" VARCHAR(50) NOT NULL UNIQUE);
        """)
except sqlite3.Error, e:
    print 'Error in "tmp.db": %s' % e.args[0]
    sys.exit(1)

if __name__ == "__main__":
    pass # nothing yet
