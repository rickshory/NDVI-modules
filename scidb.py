import sqlite3, datetime
import sys
datConn = None
tmpConn = None

try:
    datConn = sqlite3.connect('sci_data.db', isolation_level=None, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    datConn.execute('pragma foreign_keys=ON') # enforce foreign keys
    # check that foreign keys constraint was correctly set
    rslt = datConn.execute('pragma foreign_keys')
    # if foreign_keys is supported, should have one item that is either (1,) or (0,)
    rl = [r for r in rslt] # comprehend it as a list
    if len(rl) == 0:
        print 'Foreign keys not supported in this version (' + sqlite3.sqlite_version + ') of sqlite. Not used in "sci_data.db".'
    if rl[0] != (1,):
        print 'Foreign keys supported, but not set in this connection to "sci_data.db"'
    datConn.execute('pragma auto_vacuum=ON')
    datConn.text_factory = str
    datConn.row_factory = sqlite3.Row

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
        CREATE UNIQUE INDEX IF NOT EXISTS "DataChannels_NoDup_ColLogSenTypUntTZ"
        ON "DataChannels"
        ("Column" ASC, "LoggerID" ASC, "SensorID" ASC,
        "DataTypeID" ASC, "DataUnitsID" ASC, "UTC_Offset" ASC);
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
    tmpConn = sqlite3.connect('tmp.db', isolation_level=None, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    tmpConn.execute('pragma foreign_keys=ON')
    # check that foreign keys constraint was correctly set
    rslt = tmpConn.execute('pragma foreign_keys')
    # if foreign_keys is supported, should have one item that is either (1,) or (0,)
    rl = [r for r in rslt] # comprehend it as a list
    if len(rl) == 0:
        print 'Foreign keys not supported in this version (' + sqlite3.sqlite_version + ') of sqlite. Not used in "tmp.db".'
    if rl[0] != (1,):
        print 'Foreign keys supported, but not set in this connection to "tmp.db"'
        
    tmpConn.execute('pragma auto_vacuum=ON')
    tmpConn.text_factory = str
    tmpConn.row_factory = sqlite3.Row

    curT = tmpConn.cursor()

    curT.executescript("""
        CREATE TABLE IF NOT EXISTS "Text"
        ("ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
        "Line" VARCHAR(50) NOT NULL UNIQUE);
        """)

    curT.execute("drop table if exists testDates")
    curT.execute("create table if not exists testDates(d date, ts timestamp)")

    today = datetime.date.today()
    now = datetime.datetime.now()

    curT.execute("insert into testDates(d, ts) values (?, ?)", (today, now))
    curT.execute("select d, ts from testDates")
    rec = curT.fetchone()
    print today, "=>", rec['d'], type(rec['d'])
    print now, "=>", rec['ts'], type(rec['ts'])

    curT.execute('select current_date as "d [date]", current_timestamp as "ts [timestamp]"')
    rec = curT.fetchone()
    print "current_date", rec['d'], type(rec['d'])
    print "current_timestamp", rec['ts'], type(rec['ts'])

except sqlite3.Error, e:
    print 'Error in "tmp.db": %s' % e.args[0]
    sys.exit(1)

def assureItemIsInTableField(stItem, stTable, stField):
    """
    This is intended for use on tables that contain only two fields, a
     text field of unique values, and an autonumber ID field which is the primary key
    If the given text value is not in the table, this function inserts it and returns the ID.
    If the value is already in the table, the function returns the existing ID.
    Input is three strings:
    stItem is the string value to test or insert
    stTable is the table
    stField is the field in that table
    """
    
    try:
        stSQL = 'INSERT INTO ' + stTable + '(' + stField + ') VALUES (?);'
        curD.execute(stSQL, (stItem,))
        datConn.commit()
        return curD.lastrowid
    except sqlite3.IntegrityError: # item is already in the table, get its ID
        stSQL = 'SELECT ID FROM ' + stTable + ' WHERE (' + stField + ') = (?);'
        curD.execute(stSQL, (stItem,))
        t = curD.fetchone() # a tuple with one value
        return t[0]
#    except: # some other error
#        return None
    

def assureChannelIsInDB(lChanList):
    """
    Given a 7-membered list
    The first item in each list will be the primary key in the Channels table.
    The list is first created with this = 0.
    The rest of the list is built up, then the list is sent to this function
     that looks in the database.
    If the function finds an existing channel, it fills in the primary key.
    If it does not find an existing channel, it creates a new one and fills in the pk.
    List item 7 will be "new" if the record is new, otherwise "existing"
    The list contains the text values of (2)logger serial number, (3)sensor serial number,
     (4)data type, and (5)data units, and the integer values of(1) column number, and (6)hour offset.
    The function takes care of filling in all these in their respective tables.
    When returned, the calling procedure can quickly insert data values
     into the data table by using list item [0] for the channel pk.
    """   
    # set up dependent fields
    lgrID = assureItemIsInTableField(lChanList[2], 'Loggers', 'LoggerSerialNumber')
    senID = assureItemIsInTableField(lChanList[3], 'Sensors', 'SensorSerialNumber')
    dtyID = assureItemIsInTableField(lChanList[4], 'DataTypes', 'TypeText')
    dunID = assureItemIsInTableField(lChanList[5], 'DataUnits', 'UnitsText')
    # set up channel
    try:
        stSQL = """
            INSERT INTO DataChannels
            (Column, LoggerID, SensorID, DataTypeID, DataUnitsID, UTC_Offset)
            VALUES (?,?,?,?,?,?);
            """
        curD.execute(stSQL, (lChanList[1], lgrID, senID, dtyID, dunID, lChanList[6]))
        datConn.commit()
        lChanList[0] = curD.lastrowid
        lChanList[7] = 'new'
    except sqlite3.IntegrityError: # this Channel is already there, get its ID
        stSQL = """
            SELECT ID FROM DataChannels
            WHERE Column = ? AND LoggerID = ? AND SensorID = ? AND
            DataTypeID = ? AND DataUnitsID = ? AND UTC_Offset = ?;
        """
        curD.execute(stSQL, (lChanList[1], lgrID, senID, dtyID, dunID, lChanList[6]))
        t = curD.fetchone() # a tuple with one value
        lChanList[0] = t[0]
        lChanList[7] = 'existing'
    return lChanList


if __name__ == "__main__":
    pass # nothing yet
