import sqlite3, datetime
import sys
datConn = None
tmpConn = None

try:
    datConn = sqlite3.connect('sci_data.db', isolation_level=None, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    # importing the 'datetime' module declares some new SQLite field types: 'date' and 'timestamp'
    # 'PARSE_DECLTYPES' acivates them
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
    # assure the Equation of Time table exists and is filled
    curD.execute(""" SELECT COUNT(*) FROM sqlite_master WHERE name = ?  """, ('EqnOfTime', ))
    ck = curD.fetchone()
    if not bool(ck[0]): # assume if EqnOfTime table exists it is filled
        print "about to create EqnOfTime table"
        curD.execute("""
            CREATE TABLE "EqnOfTime"
            ("DayOfYear" INTEGER NOT NULL PRIMARY KEY UNIQUE,
            "MinutesCorrection" FLOAT)
            """)
        print "about to fill EqnOfTime table"
        lTimes = [ (1, -3.20), (2, -3.67), (3, -4.13), (4, -4.60), (5, -5.05), (6, -5.50), (7, -5.95), (8, -6.38), (9, -6.82), (10, -7.23), 
            (11, -7.63), (12, -8.03), (13, -8.42), (14, -8.80), (15, -9.17), (16, -9.53), (17, -9.87), (18, -10.20), (19, -10.53), (20, -10.83), 
            (21, -11.13), (22, -11.42), (23, -11.68), (24, -11.95), (25, -12.20), (26, -12.43), (27, -12.65), (28, -12.85), (29, -13.05), (30, -13.23), 
            (31, -13.40), (32, -13.55), (33, -13.68), (34, -13.80), (35, -13.92), (36, -14.02), (37, -14.10), (38, -14.17), (39, -14.23), (40, -14.27), 
            (41, -14.30), (42, -14.32), (43, -14.33), (44, -14.32), (45, -14.30), (46, -14.27), (47, -14.22), (48, -14.17), (49, -14.10), (50, -14.02), 
            (51, -13.92), (52, -13.82), (53, -13.70), (54, -13.58), (55, -13.45), (56, -13.30), (57, -13.15), (58, -12.98), (59, -12.80), (60, -12.70), 
            (61, -12.57), (62, -12.38), (63, -12.18), (64, -11.97), (65, -11.75), (66, -11.30), (67, -11.28), (68, -11.05), (69, -10.80), (70, -10.55), 
            (71, -10.30), (72, -10.03), (73, -9.77), (74, -9.50), (75, -9.22), (76, -8.93), (77, -8.65), (78, -8.37), (79, -8.07), (80, -7.77), 
            (81, -7.47), (82, -7.17), (83, -6.87), (84, -6.57), (85, -6.27), (86, -5.97), (87, -5.67), (88, -5.35), (89, -5.03), (90, -4.73), 
            (91, -4.43), (92, -4.13), (93, -3.83), (94, -3.53), (95, -3.23), (96, -2.95), (97, -2.67), (98, -2.38), (99, -2.10), (100, -1.82), 
            (101, -1.53), (102, -1.27), (103, -1.00), (104, -0.73), (105, -0.48), (106, -0.23), (107, 0.02), (108, 0.25), (109, 0.48), (110, 0.72), 
            (111, 0.93), (112, 1.00), (113, 1.35), (114, 1.55), (115, 1.75), (116, 1.93), (117, 2.10), (118, 2.27), (119, 2.43), (120, 2.58), 
            (121, 2.72), (122, 2.85), (123, 2.98), (124, 3.10), (125, 3.20), (126, 3.30), (127, 3.38), (128, 3.45), (129, 3.52), (130, 3.58), 
            (131, 3.63), (132, 3.67), (133, 3.70), (134, 3.73), (135, 3.73), (136, 3.73), (137, 3.73), (138, 3.72), (139, 3.68), (140, 3.65), 
            (141, 3.62), (142, 3.57), (143, 3.50), (144, 3.40), (145, 3.35), (146, 3.27), (147, 3.17), (148, 3.05), (149, 2.93), (150, 2.82), 
            (151, 2.68), (152, 2.55), (153, 2.42), (154, 2.27), (155, 2.10), (156, 1.93), (157, 1.77), (158, 1.60), (159, 1.42), (160, 1.23), 
            (161, 1.05), (162, 0.85), (163, 0.65), (164, 0.45), (165, 0.25), (166, 0.05), (167, -0.17), (168, -0.38), (169, -0.60), (170, -0.82), 
            (171, -1.03), (172, -1.25), (173, -1.47), (174, -1.68), (175, -1.90), (176, -2.12), (177, -2.33), (178, -2.55), (179, -2.75), (180, -2.95), 
            (181, -3.15), (182, -3.35), (183, -3.55), (184, -3.75), (185, -3.95), (186, -4.13), (187, -4.32), (188, -4.48), (189, -4.65), (190, -4.82), 
            (191, -4.97), (192, -5.12), (193, -5.27), (194, -5.40), (195, -5.53), (196, -5.65), (197, -5.77), (198, -5.87), (199, -5.97), (200, -6.05), 
            (201, -6.13), (202, -6.20), (203, -6.25), (204, -6.30), (205, -6.33), (206, -6.37), (207, -6.40), (208, -6.42), (209, -6.42), (210, -6.40), 
            (211, -6.38), (212, -6.35), (213, -6.32), (214, -6.27), (215, -6.22), (216, -6.15), (217, -6.07), (218, -5.98), (219, -5.88), (220, -5.77), 
            (221, -5.65), (222, -5.52), (223, -5.38), (224, -5.23), (225, -5.08), (226, -4.92), (227, -4.73), (228, -4.55), (229, -4.35), (230, -4.15), 
            (231, -3.95), (232, -3.73), (233, -3.50), (234, -3.27), (235, -3.02), (236, -2.77), (237, -2.50), (238, -2.23), (239, -1.97), (240, -1.68), 
            (241, -1.40), (242, -1.12), (243, -0.82), (244, -0.52), (245, -0.20), (246, 0.12), (247, 0.43), (248, 0.75), (249, 1.08), (250, 1.42), 
            (251, 1.75), (252, 2.08), (253, 2.43), (254, 2.78), (255, 3.13), (256, 3.48), (257, 3.83), (258, 4.18), (259, 4.53), (260, 4.88), 
            (261, 5.23), (262, 5.58), (263, 5.93), (264, 6.30), (265, 6.67), (266, 7.02), (267, 7.37), (268, 7.72), (269, 8.07), (270, 8.42), 
            (271, 8.77), (272, 9.10), (273, 9.43), (274, 9.77), (275, 10.08), (276, 10.40), (277, 10.72), (278, 11.03), (279, 11.33), (280, 11.63), 
            (281, 11.93), (282, 12.22), (283, 12.50), (284, 12.77), (285, 13.03), (286, 13.30), (287, 13.55), (288, 13.78), (289, 14.02), (290, 14.23), 
            (291, 14.45), (292, 14.65), (293, 14.85), (294, 15.03), (295, 15.20), (296, 15.37), (297, 15.52), (298, 15.67), (299, 15.78), (300, 15.90), 
            (301, 16.02), (302, 16.10), (303, 16.18), (304, 16.25), (305, 16.30), (306, 16.33), (307, 16.37), (308, 16.38), (309, 16.38), (310, 16.37), 
            (311, 16.33), (312, 16.30), (313, 16.25), (314, 16.18), (315, 16.10), (316, 16.00), (317, 15.88), (318, 15.77), (319, 15.62), (320, 15.47), 
            (321, 15.30), (322, 15.12), (323, 14.93), (324, 14.72), (325, 14.50), (326, 14.27), (327, 14.02), (328, 13.75), (329, 13.47), (330, 13.18), 
            (331, 12.88), (332, 12.57), (333, 12.23), (334, 11.90), (335, 11.55), (336, 11.18), (337, 10.82), (338, 10.43), (339, 10.03), (340, 9.63), 
            (341, 9.22), (342, 8.80), (343, 8.37), (344, 7.93), (345, 7.48), (346, 7.03), (347, 6.57), (348, 6.10), (349, 5.63), (350, 5.15), 
            (351, 4.67), (352, 4.18), (353, 3.70), (354, 3.22), (355, 2.72), (356, 2.22), (357, 1.72), (358, 1.22), (359, 0.72), (360, 0.22), 
            (361, -0.28), (362, -0.78), (363, -1.27), (364, -1.75), (365, -2.23), (366, -2.72)]
        datConn.execute("BEGIN DEFERRED TRANSACTION") # makes executemany much faster, when isolation_level=None
        curD.executemany('INSERT INTO EqnOfTime(DayOfYear, MinutesCorrection) VALUES(?, ?)', lTimes)
        datConn.execute("COMMIT TRANSACTION") # when isolation_level=None, don't routinely need to commit
        print "EqnOfTime table created and filled"
        
    curD.executescript("""
        CREATE TABLE IF NOT EXISTS "Loggers"
        ("ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
        "LoggerSerialNumber" VARCHAR(32) NOT NULL UNIQUE);

        CREATE TABLE IF NOT EXISTS "Sensors"
        ("ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
        "SensorSerialNumber" VARCHAR(32) NOT NULL UNIQUE);
        
        CREATE TABLE IF NOT EXISTS "DataTypes"
        ("ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
        "TypeText" VARCHAR(50) NOT NULL UNIQUE);
        
        CREATE TABLE IF NOT EXISTS "DataUnits"
        ("ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
        "UnitsText" VARCHAR(50) NOT NULL  UNIQUE );
        
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
        
        CREATE UNIQUE INDEX IF NOT EXISTS "DataChannels_NoDup_ColLogSenTypUntTZ"
        ON "DataChannels"
        ("Column" ASC, "LoggerID" ASC, "SensorID" ASC,
        "DataTypeID" ASC, "DataUnitsID" ASC, "UTC_Offset" ASC);
        
        CREATE TABLE IF NOT EXISTS "Data" (
        "ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
        "UTTimestamp" timestamp NOT NULL ,
        "ChannelID" INTEGER NOT NULL ,
        "Value" FLOAT NOT NULL ,
        "Use" BOOL NOT NULL  DEFAULT 1,
        FOREIGN KEY("ChannelID") REFERENCES DataChannels("ID")
        );
        
        CREATE UNIQUE INDEX IF NOT EXISTS "Data_NoDup_TimeChan"
        ON "Data"
        ("UTTimestamp" ASC, "ChannelID" ASC);
        
        CREATE TABLE IF NOT EXISTS "DataDates" 
        ("Date" date PRIMARY KEY  NOT NULL  UNIQUE );
        
        CREATE TABLE IF NOT EXISTS "FieldSites" (
        "ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
        "SiteName" VARCHAR(50) NOT NULL UNIQUE,
        "LatitudeDecDegrees" FLOAT,
        "LongitudeDecDegrees" FLOAT,
        "UTC_Offset" INTEGER
        );
        
        CREATE TABLE IF NOT EXISTS "StationSpecs"
        ("ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
        "InstrumentSpec" VARCHAR(255) NOT NULL UNIQUE);
        
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
        
        CREATE TABLE IF NOT EXISTS "DataSeriesSpecs"
        ("ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
        "DeviceSpec" VARCHAR(255) NOT NULL UNIQUE);
        
        CREATE TABLE IF NOT EXISTS "DataSeries" (
        "ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
        "DataSeriesDescription" VARCHAR(30) NOT NULL UNIQUE,
        "DeviceSpecID" INTEGER,
        FOREIGN KEY("DeviceSpecID") REFERENCES DataSeriesSpecs("ID")
        );
        
        CREATE TABLE IF NOT EXISTS "ChannelSegments" (
        "ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
        "ChannelID" INTEGER NOT NULL ,
        "SegmentBegin" timestamp NOT NULL ,
        "SegmentEnd" timestamp,
        "StationID" INTEGER,
        "SeriesID" INTEGER,
        CHECK ("SegmentEnd" IS NULL or ("SegmentEnd" > "SegmentBegin"))
        FOREIGN KEY("ChannelID") REFERENCES DataChannels("ID")
        FOREIGN KEY("StationID") REFERENCES Stations("ID")
        FOREIGN KEY("SeriesID") REFERENCES DataSeries("ID")
        );
        
        CREATE VIEW IF NOT EXISTS "ChannelsWithMultipleSegments"
        AS SELECT ChannelSegments.ChannelID
        FROM ChannelSegments
        GROUP BY ChannelSegments.ChannelID
        HAVING (((Count(ChannelSegments.ID))>1));

        CREATE VIEW IF NOT EXISTS "ChannelsWithOneSegment"
        AS SELECT ChannelSegments.ChannelID
        FROM ChannelSegments
        GROUP BY ChannelSegments.ChannelID
        HAVING (((Count(ChannelSegments.ID))=1));

        CREATE VIEW IF NOT EXISTS "ChannelsWithZeroSegments"
        AS SELECT DataChannels.ID AS ChannelID
        FROM DataChannels LEFT JOIN ChannelSegments ON DataChannels.ID = ChannelSegments.ChannelID
        WHERE (((ChannelSegments.ChannelID) Is Null));

        CREATE VIEW IF NOT EXISTS "OpenEndedSegments"
        AS SELECT ChannelSegments.ID, ChannelSegments.SegmentBegin,
        Min(FollowingSegments.SegmentBegin) AS NextSegBegin
        FROM ChannelSegments LEFT JOIN ChannelSegments AS FollowingSegments
        ON ChannelSegments.ChannelID = FollowingSegments.ChannelID
        WHERE (((ChannelSegments.SegmentEnd) Is Null)
        AND (ChannelSegments.SegmentBegin < FollowingSegments.SegmentBegin))
        GROUP BY ChannelSegments.ID, ChannelSegments.SegmentBegin;

        CREATE VIEW IF NOT EXISTS "OverlappingSegments"
        AS SELECT ChannelSegments.ID,
        ChannelSegments.SegmentBegin AS CurSegBegin,
        ChannelSegments.SegmentEnd AS CurSegEnd,
        PreviousSegments.SegmentBegin AS PrevSegBegin,
        PreviousSegments.SegmentEnd AS PrevSegEnd
        FROM ChannelSegments LEFT JOIN ChannelSegments AS PreviousSegments
        ON ChannelSegments.ChannelID = PreviousSegments.ChannelID
        WHERE (((PreviousSegments.SegmentEnd) NOT NULL)
        AND ([PreviousSegments].[SegmentBegin]<[ChannelSegments].[SegmentBegin])
        AND ([PreviousSegments].[SegmentEnd]>[ChannelSegments].[SegmentBegin]));

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
    curT.execute("create table if not exists testDates(note varchar[50], d date, ts timestamp)")

    today = datetime.date.today()
    now = datetime.datetime.now()

    curT.execute("insert into testDates(note, d, ts) values (?, ?, ?)", ('ck', today, now))
    curT.execute("select note, d, ts from testDates")
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

def autofixChannelSegments():
    """
    A channel segment must have a start time, but end time can be null
    End time null means "from start time on"
    Queries are written to replace null end time with Now
    A channel segment can have a start time that is the same as the stop time of the previous segment
    Query logic should be written >= startTime and < stopTime
    Similar to days' data, which are >= midnight and < next day's midnight
    Still, automatic fixes try to set a one second gap between segments.
    Actions for channels in these states:
    Multiple segments
        If a segment does not have an explicit stop time and there is(are) a later segment(s)
        (which of course have start times, becaue that field is required):
            Assign explicit stop time to earlier segment, at the start time of first later.
        [Maybe allow overlaps, as long as user understands they occur]
        [Maybe reserve checking for inconsistencies to segments the user has tagged with
        Station and Series]
        If start time is earlier than explicit stop time of previous (overlap):
            If one segment (A) completely encompasses another (B), such that A.Start < B.Start and
            A.End > B.End:
                Delete the larger segment (A) [maybe change this rule]
            Adjust start time of later segment to be stop time of earlier
        If data exist for a channel after the latest explicit stop time, create a new segment
    One segment:
        If the segment has an explicit end: # assume user entered, do not adjust the segment
            If there is data after the end:
                Create a new segment with start time the previous segment's end time
        Else the segment has no explicit end: # assume auto generated, and possibly still
        being built, possibly with records being parsed out of chronological order
            If there are data points earlier than start time, adjust start time to earliest
    Zero segments:
        Create one segment with Start as the earliest time in the channel
    """
    # Check for open-ended segments; use a temporary table to avoid any problems with aggregates in query
    # Each record (if there are any) will have the ID of a current open ended segment, with the
    # the start time of the next following segment, which will be used to generate the end
    # Make table, which may be empty; just as quick to make the table as to test the source query
    curD.execute("DROP TABLE IF EXISTS tmpOpenEndedSegments;")
    curD.execute("CREATE TABLE tmpOpenEndedSegments AS SELECT * FROM OpenEndedSegments;")
    # then, this test for presence will be quick because the temp table is never large
    curD.execute("SELECT COUNT(*) AS 'recCt' FROM tmpOpenEndedSegments;")
    t = curD.fetchone() # a tuple with one value
    if t[0] > 0: # there is at least one open ended segment
        stSQL = """
        UPDATE ChannelSegments 
        SET 
         SegmentEnd = (SELECT datetime(NextSegBegin, '-1 second')
          FROM tmpOpenEndedSegments 
          WHERE ChannelSegments.ID = tmpOpenEndedSegments.ID)
        WHERE
         EXISTS (
          SELECT *
          FROM tmpOpenEndedSegments
          WHERE ChannelSegments.ID = tmpOpenEndedSegments.ID
         );
         """
        curD.execute(stSQL)
    # more validity checking here
    # create a channel segment for any channel data after the latest explicit end time
    
    # finally, create a channel segment for any data that has none
    stSQL = """
    INSERT INTO ChannelSegments ( ChannelID, SegmentBegin )
    SELECT Data.ChannelID, MIN(Data.UTTimestamp) AS MinOfUTTimestamp
    FROM Data LEFT JOIN ChannelSegments ON Data.ChannelID = ChannelSegments.ChannelID
    WHERE (((ChannelSegments.ChannelID) Is Null))
    GROUP BY Data.ChannelID;    
    """
    curD.execute(stSQL) # can be rather slow, but necessary
    

if __name__ == "__main__":
    pass # nothing yet
