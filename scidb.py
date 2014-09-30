import wx, sqlite3, datetime, copy
import sys, re
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

        CREATE TABLE IF NOT EXISTS "InstrumentSpecs"
        ("ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
        "InstrumentSpec" VARCHAR(255) NOT NULL UNIQUE);

        CREATE TABLE IF NOT EXISTS "Loggers"
        ("ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
        "LoggerSerialNumber" VARCHAR(32) NOT NULL UNIQUE,
        "InstrumentSpecID" INTEGER,
        FOREIGN KEY("InstrumentSpecID") REFERENCES InstrumentSpecs("ID")
        );
        
        CREATE TABLE IF NOT EXISTS "DeviceSpecs"
        ("ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
        "DeviceSpec" VARCHAR(255) NOT NULL UNIQUE);
        
        CREATE TABLE IF NOT EXISTS "Sensors"
        ("ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
        "SensorSerialNumber" VARCHAR(32) UNIQUE,
        "DeviceSpecID" INTEGER,
        FOREIGN KEY("DeviceSpecID") REFERENCES DeviceSpecs("ID")
        );
        
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
        "SensorID" INTEGER NOT NULL,
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
        "Use" BOOL NOT NULL DEFAULT 1,
        CHECK (CAST(Value AS FLOAT) == Value),
        FOREIGN KEY("ChannelID") REFERENCES DataChannels("ID")
        );
        
        CREATE UNIQUE INDEX IF NOT EXISTS "Data_NoDup_TimeChan"
        ON "Data"
        ("UTTimestamp" ASC, "ChannelID" ASC);
        
        CREATE TABLE IF NOT EXISTS "FieldSites" (
        "ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL UNIQUE ,
        "SiteName" VARCHAR(50) NOT NULL UNIQUE,
        "LatitudeDecDegrees" FLOAT NOT NULL,
        "LongitudeDecDegrees" FLOAT NOT NULL,
        "UTC_Offset" INTEGER,
        CHECK (CAST(LatitudeDecDegrees AS FLOAT) == LatitudeDecDegrees)
        CHECK (CAST(LongitudeDecDegrees AS FLOAT) == LongitudeDecDegrees)
        );
                
        CREATE TABLE IF NOT EXISTS "Stations" (
        "ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
        "StationName" VARCHAR(25) NOT NULL UNIQUE,
        "SiteID" INTEGER,
        "LatitudeDecDegrees" FLOAT,
        "LongitudeDecDegrees" FLOAT,
        FOREIGN KEY("SiteID") REFERENCES FieldSites("ID")
        );
        
        CREATE TABLE IF NOT EXISTS "DataSeries" (
        "ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
        "DataSeriesDescription" VARCHAR(30) NOT NULL UNIQUE
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
        
        CREATE VIEW IF NOT EXISTS "ChannelsWithOneSegment"
        AS SELECT ChannelSegments.ChannelID
        FROM ChannelSegments
        GROUP BY ChannelSegments.ChannelID
        HAVING (((Count(ChannelSegments.ID))=1));

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
        
        CREATE VIEW IF NOT EXISTS "MaxSegmentEnds"
        AS SELECT ChannelSegments.ChannelID,
        Max(ChannelSegments.SegmentEnd) AS MaxSegmEnd
        FROM ChannelSegments
        WHERE (((ChannelSegments.SegmentEnd) NOT NULL))
        GROUP BY ChannelSegments.ChannelID;
        
        CREATE VIEW IF NOT EXISTS "FirstDataTimeAfterSegmentEnds"
        AS SELECT MaxSegmentEnds.ChannelID,
        MaxSegmentEnds.MaxSegmEnd,
        Min(Data.UTTimestamp) AS FirstAfterMaxEnd
        FROM MaxSegmentEnds LEFT JOIN Data
        ON MaxSegmentEnds.ChannelID = Data.ChannelID
        WHERE (((Data.UTTimestamp)>(MaxSegmentEnds.MaxSegmEnd)))
        GROUP BY MaxSegmentEnds.ChannelID, MaxSegmentEnds.MaxSegmEnd;

        CREATE TABLE IF NOT EXISTS "OutputBooks" (
        "ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL UNIQUE ,
        "BookName" VARCHAR(30) NOT NULL UNIQUE,
        "Longitude" FLOAT NOT NULL,
        "HourOffset" INT NOT NULL,
        "NumberOfTimeSlicesPerDay" INTEGER NOT NULL DEFAULT 1,
        "OutputDataStart" date,
        "OutputDataEnd" date,
        "PutAllOutputRowsInOneSheet" BOOL NOT NULL DEFAULT 0,
        "BlankRowBetweenDataBlocks" BOOL NOT NULL DEFAULT 0,
        CHECK ("Longitude" >= -180)
        CHECK ("Longitude" <= 180)
        CHECK ("HourOffset" >= -12)
        CHECK ("HourOffset" <= 12)
        CHECK ("NumberOfTimeSlicesPerDay" >= 1)
        CHECK (("OutputDataStart" is NULL) or ("OutputDataEnd" is NULL)
        or ("OutputDataStart" <= "OutputDataEnd"))
        );
        
        CREATE TABLE IF NOT EXISTS "OutputSheets" (
        "ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL UNIQUE ,
        "BookID" INTEGER NOT NULL,
        "WorksheetName" VARCHAR(20) NOT NULL,
        "DataSetNickname" VARCHAR(50),
        "ListingOrder" INTEGER NOT NULL,
        FOREIGN KEY("BookID") REFERENCES OutputBooks("ID")
        );

        CREATE TABLE IF NOT EXISTS "OutputColumns" (
        "ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL UNIQUE ,
        "WorksheetID" INTEGER NOT NULL ,
        "ColumnHeading" VARCHAR(20) NOT NULL,
        "ColType" VARCHAR(10) NOT NULL,
        "TimeSystem"  VARCHAR(10) DEFAULT 'Clock Time',
        "TimeIsInterval" BOOL NOT NULL DEFAULT 0,
        "IntervalIsFrom" DATETIME,
        "Constant" VARCHAR(10),
        "Formula" VARCHAR(1000),
        "AggType" VARCHAR(5),
        "AggStationID" INTEGER,
        "AggDataSeriesID" INTEGER,
        "Format_Python" VARCHAR(20),
        "Format_Excel" VARCHAR(20),
        "ListingOrder" INTEGER NOT NULL,
        CHECK ("ColType" IN ('Timestamp', 'Constant', 'Aggregate', 'Formula'))
        CHECK ("TimeSystem" IN ('Clock Time', 'Solar Time'))
        CHECK ("AggType" IN ('Avg', 'Min', 'Max', 'Count', 'Sum', 'StDev'))
        CHECK (NOT (("ColType" = 'Timestamp') AND ("TimeSystem" IS NULL)))
        CHECK (NOT (("TimeIsInterval" = 1) AND ("IntervalIsFrom" IS NULL)))
        CHECK (NOT (("ColType" = 'Constant') AND ("Constant" IS NULL)))
        CHECK (NOT (("ColType" = 'Aggregate') AND (("AggType" IS NULL)
        OR ("AggStationID" IS NULL) OR ("AggDataSeriesID" IS NULL))))
        CHECK (NOT (("ColType" = 'Formula') AND ("Formula" IS NULL)))
        FOREIGN KEY("WorksheetID") REFERENCES OutputSheets("ID")
        FOREIGN KEY("AggStationID") REFERENCES Stations ("ID")
        FOREIGN KEY("AggDataSeriesID") REFERENCES DataSeries ("ID")
        );

        CREATE VIEW IF NOT EXISTS "DupOutputColumnsOnSheetCol"
        AS SELECT OutputColumns.WorksheetID, OutputColumns.ListingOrder,
        OutputColumns.ID, OutputColumns.ColumnHeading, OutputColumns.ColType,
        OutputColumns.Constant, OutputColumns.AggStationID, OutputColumns.AggDataSeriesID,
        OutputColumns.AggType, OutputColumns.Format_Python, OutputColumns.Format_Excel 
        FROM OutputColumns
        WHERE (((OutputColumns.WorksheetID) In
        (SELECT WorksheetID FROM OutputColumns As Tmp
        GROUP BY WorksheetID, ListingOrder
        HAVING Count(*)>1  And ListingOrder = OutputColumns.ListingOrder)))
        ORDER BY OutputColumns.WorksheetID, OutputColumns.ListingOrder;
        
        CREATE VIEW IF NOT EXISTS "DupOutputColumnsNotAggregate"
        AS SELECT OutputBooks.BookName, OutputSheets.WorksheetName,
        DupOutputColumnsOnSheetCol.ListingOrder
        FROM (DupOutputColumnsOnSheetCol
        LEFT JOIN OutputSheets ON DupOutputColumnsOnSheetCol.WorksheetID = OutputSheets.ID)
        LEFT JOIN OutputBooks ON OutputSheets.BookID = OutputBooks.ID
        WHERE (((DupOutputColumnsOnSheetCol.ColType)<>"Aggregate"))
        GROUP BY OutputBooks.BookName, OutputSheets.WorksheetName,
        DupOutputColumnsOnSheetCol.ListingOrder;

        CREATE VIEW IF NOT EXISTS "GrpOutputColumnsOnSheetCol"
        AS SELECT Count(OutputColumns.ID) AS CountOfID, OutputColumns.WorksheetID, OutputColumns.ListingOrder
        FROM OutputColumns
        GROUP BY OutputColumns.WorksheetID, OutputColumns.ListingOrder
        HAVING (((Count(OutputColumns.ID))>1))
        ORDER BY Count(OutputColumns.ID) DESC;

        CREATE VIEW IF NOT EXISTS "GrpDupOutputColumns"
        AS SELECT Count(DupOutputColumnsOnSheetCol.ID) AS ReCountOfID,
        DupOutputColumnsOnSheetCol.WorksheetID, DupOutputColumnsOnSheetCol.ListingOrder,
        DupOutputColumnsOnSheetCol.ColumnHeading, DupOutputColumnsOnSheetCol.ColType,
        DupOutputColumnsOnSheetCol.AggType,
        DupOutputColumnsOnSheetCol.Format_Python, DupOutputColumnsOnSheetCol.Format_Excel
        FROM DupOutputColumnsOnSheetCol
        GROUP BY DupOutputColumnsOnSheetCol.WorksheetID, DupOutputColumnsOnSheetCol.ListingOrder,
        DupOutputColumnsOnSheetCol.ColumnHeading, DupOutputColumnsOnSheetCol.ColType,
        DupOutputColumnsOnSheetCol.AggType,
        DupOutputColumnsOnSheetCol.Format_Python, DupOutputColumnsOnSheetCol.Format_Excel;

        CREATE VIEW IF NOT EXISTS "DupOutputColumnsMismatch"
        AS SELECT OutputBooks.BookName, OutputSheets.WorksheetName,
        GrpDupOutputColumns.ListingOrder
        FROM ((GrpOutputColumnsOnSheetCol
        LEFT JOIN GrpDupOutputColumns
        ON (GrpOutputColumnsOnSheetCol.ListingOrder = GrpDupOutputColumns.ListingOrder)
        AND (GrpOutputColumnsOnSheetCol.WorksheetID = GrpDupOutputColumns.WorksheetID))
        LEFT JOIN OutputSheets ON GrpDupOutputColumns.WorksheetID = OutputSheets.ID)
        LEFT JOIN OutputBooks ON OutputSheets.BookID = OutputBooks.ID
        WHERE (((GrpOutputColumnsOnSheetCol.CountOfID)<>[ReCountOfID]));

        CREATE TABLE IF NOT EXISTS "NDVIcalc" (
        "ID" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE ,
        "CalcName" VARCHAR(50) NOT NULL  UNIQUE ,
        "ChartFromRefDay" BOOL NOT NULL  DEFAULT 0 ,
        "RefDay" date ,
        "RefStationID" INTEGER ,
        "IRRefSeriesID" INTEGER ,
        "VISRefSeriesID" INTEGER ,
        "UseRef" BOOL NOT NULL DEFAULT 1,
        "IRDataSeriesID" INTEGER ,
        "VisDataSeriesID" INTEGER ,
        "IRFunction" VARCHAR(250) DEFAULT "=i" ,
        "VISFunction" VARCHAR(250) DEFAULT "=v" ,
        "PlusMinusCutoffHours" FLOAT NOT NULL DEFAULT 2 ,
        "Opt1ClrDayVsSetTholds" BOOL NOT NULL DEFAULT 1 ,
        "ClearDay" date ,
        "ThresholdPctLow" INTEGER NOT NULL DEFAULT 75 ,
        "ThresholdPctHigh" INTEGER NOT NULL DEFAULT 125 ,
        "IRRefCutoff" FLOAT ,
        "VISRefCutoff" FLOAT ,
        "IRDatCutoff" FLOAT ,
        "VISDatCutoff" FLOAT,
        "UseOnlyValidNDVI" BOOL NOT NULL DEFAULT 0 ,
        "NDVIvalidMin" FLOAT DEFAULT -1 ,
        "NDVIvalidMax" FLOAT DEFAULT 1  ,
        "CreateSummaries" BOOL NOT NULL DEFAULT 0,
        "OutputSAS" BOOL NOT NULL DEFAULT 0,
        "Normalize" BOOL NOT NULL DEFAULT 0,
        "OutputFormat" INTEGER NOT NULL DEFAULT 2,
        "OutputBaseName" VARCHAR(30) NOT NULL DEFAULT "NDVI" ,
        "OutputFolder" VARCHAR(250),
        CHECK ("PlusMinusCutoffHours" >= 0)
        CHECK ("PlusMinusCutoffHours" <= 12)
        CHECK (CAST(PlusMinusCutoffHours AS FLOAT) == PlusMinusCutoffHours)
        CHECK ((PlusMinusCutoffHours is NULL) OR (CAST(PlusMinusCutoffHours AS FLOAT) == PlusMinusCutoffHours))
        CHECK ("ThresholdPctLow" > 0)
        CHECK ("ThresholdPctLow" < 100)
        CHECK (CAST(ThresholdPctLow AS INTEGER) == ThresholdPctLow)
        CHECK ("ThresholdPctHigh" > 100)
        CHECK (CAST(ThresholdPctHigh AS INTEGER) == ThresholdPctHigh)
        CHECK ((IRRefCutoff is NULL) OR (CAST(IRRefCutoff AS FLOAT) == IRRefCutoff))
        CHECK ((VISRefCutoff is NULL) OR (CAST(VISRefCutoff AS FLOAT) == VISRefCutoff))
        CHECK ((IRDatCutoff is NULL) OR (CAST(IRDatCutoff AS FLOAT) == IRDatCutoff))
        CHECK ((VISDatCutoff is NULL) OR (CAST(VISDatCutoff AS FLOAT) == VISDatCutoff))
        CHECK ((NDVIvalidMin is NULL) OR (CAST(NDVIvalidMin AS FLOAT) == NDVIvalidMin))
        CHECK ((NDVIvalidMax is NULL) OR (CAST(NDVIvalidMax AS FLOAT) == NDVIvalidMax))
        CHECK ("OutputFormat" >= 1)
        CHECK ("OutputFormat" <= 3)
        );

        CREATE TABLE IF NOT EXISTS "NDVIcalcDates" (
        "ID" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE ,
        "CalcID" INTEGER NOT NULL ,
        "CalcDate" date NOT NULL ,
        FOREIGN KEY("CalcID") REFERENCES NDVIcalc("ID")
        );

        CREATE TABLE IF NOT EXISTS "NDVIcalcStations" (
        "ID" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE ,
        "CalcID" INTEGER NOT NULL ,
        "StationID" INTEGER NOT NULL ,
        FOREIGN KEY("CalcID") REFERENCES NDVIcalc("ID")
        FOREIGN KEY("StationID") REFERENCES Stations("ID")
        );

        CREATE TABLE IF NOT EXISTS "tmpChanSegSeries" (
        "ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
        "ChannelID" INTEGER NOT NULL,
        "SeriesID" INTEGER NOT NULL
        );

        CREATE UNIQUE INDEX IF NOT EXISTS "tmpChanSegSeries_NoDup"
        ON "tmpChanSegSeries"
        ("ChannelID" ASC, "SeriesID" ASC);

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
        "Line" VARCHAR(50) NOT NULL UNIQUE
        );
        
        CREATE TABLE IF NOT EXISTS "tmpLines" (
        "ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
        "Line" VARCHAR(200)
        );

        CREATE TABLE IF NOT EXISTS "tmpParseLog"
        ("ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
        "LogItem" VARCHAR(200));


        """)

    curT.execute("drop table if exists testDates")
    curT.execute("create table if not exists testDates(note varchar[50], d date, ts timestamp)")

    today = datetime.date.today()
    now = datetime.datetime.now()

#    curT.execute("insert into testDates(note, d, ts) values (?, ?, ?)", ('ck', today, now))
#    curT.execute("select note, d, ts from testDates")
#    rec = curT.fetchone()
#    print today, "=>", rec['d'], type(rec['d'])
#    print now, "=>", rec['ts'], type(rec['ts'])

#    curT.execute('select current_date as "d [date]", current_timestamp as "ts [timestamp]"')
#    rec = curT.fetchone()
#    print "current_date", rec['d'], type(rec['d'])
#    print "current_timestamp", rec['ts'], type(rec['ts'])

except sqlite3.Error, e:
    print 'Error in "tmp.db": %s' % e.args[0]
    sys.exit(1)

def getSciDataCursor():
    """
    Utility for deliving a separate sci_data database cursor, for example when
    using threads, which cannot share a connection. Assumes all tables have been
    set up correctly.
    """
    try:
        connection = sqlite3.connect('sci_data.db', isolation_level=None, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        # importing the 'datetime' module declares some new SQLite field types: 'date' and 'timestamp'
        # 'PARSE_DECLTYPES' acivates them
        connection.execute('pragma foreign_keys=ON') # enforce foreign keys
        # check that foreign keys constraint was correctly set
        rslt = connection.execute('pragma foreign_keys')
        # if foreign_keys is supported, should have one item that is either (1,) or (0,)
        rl = [r for r in rslt] # comprehend it as a list
        if len(rl) == 0:
            print 'Foreign keys not supported in this version (' + sqlite3.sqlite_version + ') of sqlite. Not used in "sci_data.db".'
        if rl[0] != (1,):
            print 'Foreign keys supported, but not set in this connection to "sci_data.db"'
        connection.execute('pragma auto_vacuum=ON')
        connection.text_factory = str
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        return cursor
        
    except sqlite3.Error, e:
        print 'Error in "sci_data.db": %s' % e.args[0]
        sys.exit(1)
        return None

def refreshDataDates(): # make externally callable
    curD.executescript("""
        DROP TABLE IF EXISTS "DataDates";
        
        CREATE TABLE IF NOT EXISTS "DataDates"
        AS SELECT date(Data.UTTimestamp) AS Date FROM Data
        GROUP BY Date;
    """)

refreshDataDates() # call it now

def getDatesList():
    """
    Gets the list of dates that have records in the Data table.
    Used for filling combo boxes, to select from dates that have existing data.
    Returns a Python list of the dates.
    """
    lstDates = []
    curD.execute("SELECT Date FROM DataDates ORDER BY Date;")
    recs = curD.fetchall()
    for rec in recs:
        lstDates.append(rec["Date"])
    return lstDates

def lenOfVarcharTableField(stTable, stField):
    """
    Returns the stated size of the given VARCHAR field of a given table
    Returns -1 if not a VARCHAR field, -2 if a nonexistent field, -3 if a nonexistent table, -4 if multiple matches
    SQLite does not enforce length limits, so this is a way to programmatically test.
    Input is two strings:
    stTable is the table
    stField is the field in that table
    """
    stSQL = "SELECT sql FROM sqlite_master WHERE type='table' and name=?"
    curD.execute(stSQL, (stTable,))
    rec = curD.fetchone()
    if rec is None:
        return -3
    else:
        stSQL = rec['sql']
        # example of regular expression where field is 'BookName'
        # ["']??BookName["']??\s+?VARCHAR\s*?[(]\s*?(?P<stRecLen>\d+)\s*?[)]
#        stRE = r"""["']??""" + stField + r"""["']??\s+?VARCHAR\s*?[(]\s*?(?P<stRecLen>\d+)\s*?[)]"""
        reRecLen = re.compile(r"""
        ["']??              # may or may not have single or double quotes around the field name
        """
        + stField +
        r"""
        ["']??              # throughout, use non-greedy match format (extra '?')
        \s+?VARCHAR\s*?     # optional whitespace around 'VARCHAR'
        [(]\s*?             # optional whitespace within parentheses
        (?P<stRecLen>\d+)   # capture the digits as stRecLen
        \s*?[)]
        """, re.VERBOSE | re.IGNORECASE)
        lLen = reRecLen.findall(stSQL)
#        print "lLen in lenOfVarcharTableField:", lLen
        if len(lLen) == 0:
            return -2 # none found
        if len(lLen) > 1:
            return -4 # multiple found, invalid
        return int(lLen[0])

def dictFromTableDefaults(stTable):
    """
    Given a table, returns a dictionary with keys corresponding to all the fields.
    If a field has a default, that is returned as the member value, otherwise None
    """
    """
    the following 'cursor.description' format does not work right;
    tuples are only the field name followed by 'None' seven times
    
        stSQL = "SELECT * FROM NDVIcalc;"
        rec = curD.execute(stSQL).fetchone()
        print 'curD.description:', curD.description

    """
    #following format fails
    #fields = curD.execute('PRAGMA table_info(?)', (stTable,)).fetchall()
    fields = curD.execute('PRAGMA table_info("' + stTable + '")').fetchall()
    """
    positions in this tuple (zero based):
    0 = numerical index of this field
    1 = name of the field as a string
    2 = data type of the field; not really, see SQLite docs
    3 = whether the field is required
    4 = default value, if any
    5 = whether the field participates in the primary key
    Example:
        (0, 'ID', 'INTEGER', 1, None, 1)
        (1, 'CalcName', 'VARCHAR(50)', 1, None, 0)
        (2, 'ChartFromRefDay', 'BOOL', 1, '0', 0)
        (3, 'RefDay', 'date', 0, None, 0)
        (4, 'RefStationID', 'INTEGER', 0, None, 0)
        ...
        (10, 'VISFunction', 'VARCHAR(50)', 0, '"=v"', 0)
        (11, 'PlusMinusCutoffHours', 'FLOAT', 0, '2', 0)
        (12, 'Opt1ClrDayVsSetTholds', 'BOOL', 1, '1', 0)
        (13, 'ClearDay', 'date', 0, None, 0)
        (14, 'ThresholdPctLow', 'FLOAT', 0, '0.75', 0)    
    """
    d = {}
    for field in fields:
#        print field
        stFldNm = field[1]
        if field[4] == None: # there is no default value
            d[stFldNm] = None
        else: # process the default value
            if field[2].upper() == 'FLOAT': # the data type, as much as there is one in sqlite
                val = float(field[4])
            elif field[2][:3].upper() == 'INT':
                val = int(field[4])
            elif field[2][:4].upper() == 'BOOL':
                val = int(field[4]) # convert to 0 or 1
#                if field[4] == '1':
#                    val = True
#                else:
#                    val = False
            else: # text
                val = re.sub(r'^"|"$', '', field[4]) # strip any quotes
            d[stFldNm] = val
    return d

def dictFromTableID(stTable, iID):
    """
    Given a table and a number that is a value in the table's 'ID' field,
    returns a dictionary with keys corresponding to all the fields.
    The values are from the corresponding table fields.
    If the record is not found, returns None
    """
    stSQL = 'SELECT * FROM ' + stTable + ' WHERE ID = ?;'
    curD.execute(stSQL, (iID,))
    rec = curD.fetchone() # returns one record, or None
    if rec == None: 
        return None    
#   d = copy.copy(recs) # this crashes
    d = {}
    for recName in rec.keys(): # copy the record into the dictionary
        d[recName] = rec[recName]
    return d

def dictIntoTable_InsertOrReplace(stTable, dict):
    """
    Given a table and a dictionary that has keys corresponding to
    all the table's field names, writes the dictionary to the table
    as INSERT OR REPLACE.
    If the ID already exists in the table, UPDATEs the record
    If the ID does not exist in the table, INSERTs a new record
    Returns the new or updated record ID, or None on failure
    Normally, you would have generated the dictionary by the functions
    'dictFromTableDefaults' or 'dictFromTableID'
    """
    """
    Dictionary does not preserve order, so write SQL using the order the dictionary delivers.
    Build an SQL string using named parameters e.g.:
    'INSERT OR REPLACE INTO Stations (Longitude, Name, ID, SiteID, Latitude)
         VALUES (:Longitude, :Name, :ID, :SiteID, :Latitude)
    """
    lKs = []
    lVs = []
    for k in dict.keys():
        lKs.append(k)
        lVs.append(':' + k)
    stKs = ', '.join(lKs)
    stVs = ', '.join(lVs)
    stSQL = 'INSERT OR REPLACE INTO ' + stTable + ' (' + stKs + ') '  \
            ' VALUES (' + stVs + ')'
#    print stSQL
    # for development, let any errors occur and display to output
#    try:
    curD.execute(stSQL, dict)
    newRowID = curD.lastrowid
    return newRowID
#    except:
#        return None
    
def countTableFieldItems(stTable, stField, stItem=None):
    """
    Tests whether an item is in the given field of a given table
    Returns 0 if not, the number or matching records if so
    Input is three strings:
    stTable is the table
    stField is the field in that table
    stItem is the value to test
    If stItem is None or left out, counts all records in the table
    """
    if stItem == None:
        stSQL = 'SELECT ' + stField + ' FROM ' + stTable + ';'
        curD.execute(stSQL)
    else:
        stSQL = 'SELECT ' + stField + ' FROM ' + stTable + ' WHERE ' + stField + ' = ?;'
        curD.execute(stSQL, (stItem,))
    recs = curD.fetchall()
    return len(recs)    

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
    # if a channel has only one segment, assure Start is earliest data for that channel

    curD.execute("SELECT COUNT(*) AS 'recCt' FROM ChannelsWithOneSegment;")
    t = curD.fetchone() # a tuple with one value
    if t[0] > 0: # there is at least one channel that has a single segment
        stSQL = """
        UPDATE ChannelSegments 
        SET 
         SegmentBegin = (SELECT MIN(UTTimestamp)
          FROM Data 
          WHERE Data.ChannelID = ChannelSegments.ChannelID)
        WHERE
         ChannelSegments.ChannelID IN (
          SELECT ChannelID
          FROM ChannelsWithOneSegment
         );
         """
    #curD.execute(stSQL)
    # too slow; using Data table with 19,560,908 records, took 4,725.416 seconds (1.3 hours)
    # this for an operation that seldom does anything
    # implement a different way

    # create a channel segment for any channel data after the latest explicit end time
    # Make table, which may be empty; just as quick to make the table as to test the source query
    #curD.execute("DROP TABLE IF EXISTS tmpFirstDataTimeAfterSegmentEnds;")
    #curD.execute("CREATE TABLE tmpFirstDataTimeAfterSegmentEnds AS SELECT * FROM FirstDataTimeAfterSegmentEnds;")
    # above, using Data table with 19,560,908 records, took 142.679 seconds
    # too slow
    # instead, create a Start after the max End if it doesn't already have a Start later than the max End
    # regardless if there are data points in that time segment yet
    stSQL = """
        INSERT INTO ChannelSegments ( ChannelID, SegmentBegin )
        SELECT MaxSegmentEnds.ChannelID, MaxSegmentEnds.MaxSegmEnd
        FROM MaxSegmentEnds
        WHERE (((MaxSegmentEnds.ChannelID) NOT IN (
         SELECT MaxSegmentEnds.ChannelID
         FROM MaxSegmentEnds LEFT JOIN ChannelSegments
         ON MaxSegmentEnds.ChannelID = ChannelSegments.ChannelID
         WHERE (([ChannelSegments].[SegmentBegin]>=[MaxSegmentEnds].[MaxSegmEnd]))))
        );
    """
    curD.execute(stSQL)

    # finally, create a channel segment for any data channel that has none yet
    stSQL = """
    INSERT INTO ChannelSegments ( ChannelID, SegmentBegin )
    SELECT Data.ChannelID, MIN(Data.UTTimestamp) AS MinOfUTTimestamp
    FROM Data LEFT JOIN ChannelSegments ON Data.ChannelID = ChannelSegments.ChannelID
    WHERE (((ChannelSegments.ChannelID) Is Null))
    GROUP BY Data.ChannelID;    
    """
    curD.execute(stSQL) # can be rather slow, but necessary
    # for Data table with 141,811 records, took 2.455ms
    # created 15 segments
    offerSeriesForChannels() # if a Series is auto available, fill in
    
def getTextFromTC(objTextControl, default = None):
    """
    Given a wx text control, returns the text stripped of leading/trailing
    whitespace and with duplicate whitespace removed.
    If nothing is left returns the default, which is None if not explicitly given
    """
    # clean up whitespace; remove leading/trailing & multiples
    stS = " ".join(objTextControl.GetValue().split())
    if stS == '':
        return default
    else:
        return stS

def getIntFromTC(objTextControl, default = None):
    """
    Given a wx text control, returns the contents converted to an integer if possible.
    If not valid as an integer, returns the default, which is None if not explicitly given
    """
    try:
        return int(objTextControl.GetValue())
    except:
        return default

def getFloatFromTC(objTextControl, default = None):
    """
    Given a wx text control, returns the contents converted to an float if possible.
    If not valid as a float, returns the default, which is None if not explicitly given
    """
    try:
        return float(objTextControl.GetValue())
    except:
        return default

def getDateFromTC(objTextControl, default = None):
    """
    Given a wx text control, returns the contents converted to a string in standard UNIX
    date format 'yyyy-mm-dd' if possible.
    If not valid as a date, returns the default, which is None if not explicitly given
    """
    dt = wx.DateTime() # Uninitialized datetime
    DateValid = dt.ParseDate(objTextControl.GetValue())
    if DateValid == -1: # invalid date
        return default
    else: # store in standard format
        return dt.Format('%Y-%m-%d')

def getDateTimeFromTC(objTextControl, default = None):
    """
    Given a wx text control, returns the contents converted to a string in standard UNIX
    datetime format 'yyyy-mm-dd hh:mm:ss' if possible.
    If not valid as a date/time, returns the default, which is None if not explicitly given
    """
    dt = wx.DateTime() # Uninitialized datetime
    DateValid = dt.ParseDateTime(objTextControl.GetValue())
    if DateValid == -1: # invalid date/time
        return default
    else: # store in standard format
        return dt.Format('%Y-%m-%d %H:%M:%S')

def getBoolFromCB(objCheckBox):
    """
    Given a wx checkbox control
    returns 1 if true, 0 if false
    """
    if objCheckBox.GetValue():
        return 1
    else:
        return 0

def fillComboboxFromSQL(objComboBox, stSQL, keyCol=0, visibleCol=1):
    """
    Given a combobox and an SQL statement that returns at least two columns;
    First, clears the combobox's list, then returns the combobox with the
    records appended as it's selection entries.
    The visible items are from 'visibleCol' in the results set.
    The 'keyCol' items can be retrieved using this format, where CB is the combobox:
    keyItem = CB.GetClientData(CB.GetSelection())
    both columns are zero based
    """
    objComboBox.Clear()
    curD.execute(stSQL)
    recs = curD.fetchall()
    for rec in recs:
        objComboBox.Append(rec[visibleCol], rec[keyCol])

def setComboboxToClientData(objComboBox, keyVal):
    """
    Given a combobox with it's list filled by the 'fillComboboxFromSQL' function
    and given a variable containing the key value,
    sets the combobox selection to the item with that key
    """
    if keyVal != None:
        for i in range(objComboBox.GetCount()):
            if objComboBox.GetClientData(i) == keyVal:
                objComboBox.SetSelection(i)
                return

def getComboboxIndex(objComboBox):
    """
    Given a combobox with it's list filled by the 'fillComboboxFromSQL' function
    returns the key value of the selected item, if any
    """
    return objComboBox.GetClientData(objComboBox.GetSelection())

##
def fillListctrlFromSQL(objListctrl, stSQL, keyCol=0, visibleCol=1):
    """
    Given a listctrl and an SQL statement that returns at least two columns;
    Returns the list control with the records appended as it's selection entries
    The visible items are from 'visibleCol' in the results set.
    The 'keyCol' items can be retrieved using a format like the following,
    where LC is the list control:
    keyItem = LC.GetItemData(LC.GetFocusedItem())
    both columns are zero based
    """
    objListctrl.DeleteAllItems()
    recs = curD.execute(stSQL).fetchall()
    i=0 # dummy variable, will change with each InsertStringItem
    for rec in recs:
        objListctrl.InsertStringItem(i, rec[visibleCol])
        objListctrl.SetItemData(i, rec[keyCol])

def fillComboCtrlPopupFromSQL(popupCtrl, stSQL, colWidthList = []):
    """
    For multi-column combo boxes:
    Given a ComboControl Popup which has a ListCtrl as its Control,
    empties the ListCtrl and re-fills it from the data returned by
    the passed SQL statement. Also takes an optional list of column
    widths. The query fields become column names, except the first
    field should be a numerical ID that will become ItemData.
    These ItemData keys can be retrieved using a format like the following,
    where self.LC is the list control, e.g. in the pop-up's OnDismiss function:
        if self.curitem == -1:
            print "In 'OnDismiss', no current item",
        else:
            keyItem = self.LC.GetItemData(self.curitem)
            print "In 'OnDismiss', GetItemData", keyItem
 
    """
    objListctrl = popupCtrl.GetControl()
    objListctrl.ClearAll()
    row = curD.execute(stSQL).fetchone()
    colNum = -1 # skip the key field, must increment 1 before inserting 1st name
    try:
        for fldName in row.keys():
            if colNum >= 0: # skip the key field
                objListctrl.InsertColumn(colNum, fldName)
                try:
                    colWidth = colWidthList[colNum]
                except:
                    colWidth = 100 # default, may eventually get form the field data
                objListctrl.SetColumnWidth(colNum, colWidth)
            print "Added column", colNum, fldName
            colNum += 1
    except:
        return # no data, leave table empty
    # columns set up, now insert rows
    recs = curD.execute(stSQL).fetchall()
    # based on this:
#        lc.InsertStringItem(i, rec[1]) # 1st column
#        lc.SetStringItem(i, 1, rec[2]) #2nd, and further, columns
#        lc.SetStringItem(i, 2, rec[3]) ...
#        lc.SetItemData(i, rec[0])
    for rec in recs:
        i = objListctrl.GetItemCount() # assure inserting at end
        print " - > Adding record", i
        objListctrl.InsertStringItem(i, str(rec[1] or ''))
        print "Added first named field", str(rec[1] or '(empty field)')
        for n in range(2, colNum+1):
            objListctrl.SetStringItem(i, n-1, str(rec[n] or ''))
            print "Added named field", n, str(rec[n] or '(empty field)')
        objListctrl.SetItemData(i, rec[0])
        print "Added key ", rec[0]
        
def ckDupOutputColumnsNotAggregate():
    curD.execute('SELECT * FROM DupOutputColumnsNotAggregate;')
    # fields: BookName, WorksheetName, ListingOrder
    rec = curD.fetchone()
    if rec == None:
        return None
    else:
        sB = ' Columns of the same numerical order will overwrite in unpredictable ways (unless ' \
            'they are all "Aggregate" and match on Column Heading, type ' \
            'of Aggregation, and Format).\n\n The first problem is in Book "%(bkName)s", ' \
            'Worksheet "%(shName)s", Column %(shNum)d. There may be others.'
        dF = {"bkName": rec['BookName'], "shName": rec['WorksheetName'], "shNum": rec['ListingOrder']}
        stErr = sB % dF
        stWndHeader = 'Duplicate Column'
        return (stErr, stWndHeader)

def ckDupOutputColumnsMismatch():
    curD.execute('SELECT * FROM DupOutputColumnsMismatch;')
    # fields: BookName, WorksheetName, ListingOrder
    rec = curD.fetchone()
    if rec == None:
        return None
    else:
        sB = ' Multiple sources can Aggregate into the same numerical column, but only if they ' \
            'have exactly the same Column Heading, ' \
            'type of Aggregation, and Format.\n\n The first mismatch is in Book "%(bkName)s", ' \
            'Worksheet "%(shName)s", Column %(shNum)d. There may be others.'
        dF = {"bkName": rec['BookName'], "shName": rec['WorksheetName'], "shNum": rec['ListingOrder']}
        stErr = sB % dF
        stWndHeader = 'Duplicate Column'
        return (stErr, stWndHeader)

def stationLongitude(iStationID):
    """
    given a Station ID
    returns the Longitude of the Station, either from the Stations table or the FieldSites table
    or None if not available in either table
    """
    stSQL_Station = 'SELECT LongitudeDecDegrees FROM Stations WHERE ID = ?;'
    try: # first, try the Stations table
        lon = curD.execute(stSQL_Station, (iStationID,)).fetchone()['LongitudeDecDegrees']
        if lon != None: # got a valid value from the Stations table
            return lon
        else: # Longitude was null in the stations table, try the FieldSites table
            stSQL_SiteID = 'SELECT SiteID FROM Stations WHERE ID = ?;'
            try:
                siteID = curD.execute(stSQL_SiteID, (iStationID,)).fetchone()['SiteID']
                if siteID == None: # SiteID is null in the Stations table
                    return None
                else:
                    stSQL_Site= 'SELECT LongitudeDecDegrees FROM FieldSites WHERE ID = ?;'
                    try:
                        lon = curD.execute(stSQL_Site, (siteID,)).fetchone()['LongitudeDecDegrees']
                        if lon == None: # Longitude was null in the FieldSites table
                            return None
                        else: # got a valid value from the FieldSites table
                            return lon
                    except: #
                        return None # no record in the FieldSites table for the passed ID 
            except:
                return None # no record in the Stations table for the passed ID 
    except:
        return None # no record in the Stations table for the passed ID

def ordinalDayOfYear(stDate):
    try:
        dtGiven = datetime.datetime.strptime(stDate, "%Y-%m-%d").date()
        dt1stOfYr = datetime.date(dtGiven.year, 1, 1)
        td = dtGiven - dt1stOfYr
        return td.days + 1   
    except:
        return None

def equationOfTime(stDate):
    """
    given a date
    returns the number of minutes solar time will be ahead or behind clock time
    """
    try:
        iOrdDayOfYr = ordinalDayOfYear(stDate)
        stSQL = "SELECT MinutesCorrection FROM EqnOfTime WHERE DayOfYear = ?;"
        curD.execute(stSQL, (iOrdDayOfYr,))
        rec = curD.fetchone()
        return rec['MinutesCorrection']
    except:
        return 0

def minutesCorrection(stDate, fLongitude):
    """
    Given a date and a longitude, returns a correction from Universal Time
        (UT, same as Greenwich Mean Time) to solar time at that longitude
    Longitude "rotates" the UT time to the correct position around the globe
        This is usually the major correction
    Day-of-year is used to look up an orbital correction factor known as the
        "equation of time".  This is usually a smaller correction factor
    """
    try:
        fpLn = float(fLongitude)
    except: # no valid longitude, use zero
        fpLn = 0
    else: #Correct for longitude
        fCorr = 60 * ((-fpLn / 15))
    # even if no valid longitude, at least correct for astonomical "equation of time"
    fCorr = fCorr + equationOfTime(stDate)
    return fCorr

def solarCorrection(stDate, fLongitude):
    """
    Given a date and a longitude, returns a timedelta which is the correction from Universal Time
        (UT, same as Greenwich Mean Time) to solar time at that longitude
    Longitude "rotates" the UT time to the correct position around the globe
        This is usually the major correction
    Day-of-year is used to look up an orbital correction factor known as the
        "equation of time".  This is usually a smaller correction factor
    If no longitude is given, returns the equation-of-time correction only
    """
    try:
        fpLn = float(fLongitude)
    except: # no valid longitude, use zero
        fpLn = 0.0
    else: #Correct for longitude
        fCorr = 60.0 * ((-fpLn / 15))
    # even if no valid longitude, at least correct for astonomical "equation of time"
    fCorr = fCorr + equationOfTime(stDate)
    return datetime.timedelta(minutes = fCorr)

def countOfSheetRows(sheetID):
    """
    Given a record ID in the table 'OutputSheets',
    Generates a count of the rows of the dataset
    Everything else is determininstic based on values in the database tables
    """
    sFmtDateOnly = '%Y-%m-%d'
    curD.execute('SELECT * FROM OutputSheets WHERE ID = ?;', (sheetID,))
    rec = curD.fetchone()
    shDict = {}
    for recName in rec.keys():
        shDict[recName] = rec[recName]
    # get values from the parent Book
    # fields: ID BookName, Longitude, HourOffset, NumberOfTimeSlicesPerDay,
    #   OutputDataStart, OutputDataEnd, PutAllOutputRowsInOneSheet, BlankRowBetweenDataBlocks
    curD.execute('SELECT * FROM OutputBooks WHERE ID = ?;', (shDict['BookID'],))
    rec = curD.fetchone()
    bkDict = {}
    for recName in rec.keys():
        bkDict[recName] = rec[recName]

    # get the list of dates to pull data for
    lDtLimits = [] # check for any start or end limits
    if bkDict['OutputDataStart'] != None: # any start criteria
        lDtLimits.append(" DataDates.Date >= '" + bkDict['OutputDataStart'].strftime(sFmtDateOnly) + "' ")
    if bkDict['OutputDataEnd'] != None: # any end criteria
        if len(lDtLimits) > 0:
            lDtLimits.append("AND")
        lDtLimits.append(" DataDates.Date <= '" + bkDict['OutputDataEnd'].strftime(sFmtDateOnly) + "' ")
    if len(lDtLimits) > 0: # complete any WHERE clause
        lDtLimits.insert(0, "\nWHERE ")
    stSQL = "SELECT Count(DataDates.Date) AS CtDates FROM DataDates" + "".join(lDtLimits) + ";"
    curD.execute(stSQL)
    rec = curD.fetchone()
    return rec['CtDates'] * bkDict['NumberOfTimeSlicesPerDay']

def generateSheetRows(sheetID, formatValues = True, cr = curD):
    """
    Given a record ID in the table 'OutputSheets',
    Generates the rows of the dataset
    Everything else is determininstic based on values in the database tables
    Each row is returned as a list of strings, including formatted dates, times, and numbers
    Default cursor is 'curD', but allows a different one e.g. for a separate thread
    """
    # a few format strings:
    sFmtFullDateTime = '%Y-%m-%d %H:%M:%S'
    sFmtDateOnly = '%Y-%m-%d'
    # get values for this sheet
    # fields: ID, BookID, WorksheetName, DataSetNickname, ListingOrder
    cr.execute('SELECT * FROM OutputSheets WHERE ID = ?;', (sheetID,))
    rec = cr.fetchone()
    shDict = {}
    for recName in rec.keys():
        shDict[recName] = rec[recName]
        
    # get values from the parent Book
    # fields: ID BookName, Longitude, HourOffset, NumberOfTimeSlicesPerDay,
    #   OutputDataStart, OutputDataEnd, PutAllOutputRowsInOneSheet, BlankRowBetweenDataBlocks
    cr.execute('SELECT * FROM OutputBooks WHERE ID = ?;', (shDict['BookID'],))
    rec = cr.fetchone()
    bkDict = {}
    for recName in rec.keys():
        bkDict[recName] = rec[recName]
    # will use the following two intervals a lot
    tdHrOffset = datetime.timedelta(hours = bkDict['HourOffset'])
    iHalfTimeSliceSecs = (24 * 60 * 60) / (2*(bkDict['NumberOfTimeSlicesPerDay']))
    tdHalfTimeSlice = datetime.timedelta(seconds = iHalfTimeSliceSecs)
                
    # get data for column heads and formats
    stSQL = "SELECT Count(OutputColumns.ID) AS CountOfID, OutputColumns.ColumnHeading,\n" \
        "OutputColumns.AggType, \n" \
        "OutputColumns.Format_Python, OutputColumns.Format_Excel, OutputColumns.ListingOrder\n" \
        "FROM OutputColumns GROUP BY OutputColumns.WorksheetID, OutputColumns.ColumnHeading,\n" \
        "OutputColumns.AggType, \n" \
        "OutputColumns.Format_Python, OutputColumns.Format_Excel, OutputColumns.ListingOrder\n" \
        "HAVING (((OutputColumns.WorksheetID) = ?))\n" \
        "ORDER BY OutputColumns.ListingOrder;"
    cr.execute(stSQL, (sheetID,))
    recs = cr.fetchall()
    # store as a list of dictionaries
    clDict = {}
    lCols = []
    for rec in recs:
        clDict = {}
        for recName in rec.keys():
            clDict[recName] = rec[recName]
        lCols.append(copy.copy(clDict))        

    # get the length of list needed; may be more than the number of records if there are blank columns
    stSQL = "SELECT MAX(CAST(ListingOrder AS INTEGER)) AS MaxLstOrd " \
        "FROM OutputColumns " \
        "WHERE WorksheetID = ?;"
    cr.execute(stSQL, (sheetID,))
    rec = cr.fetchone()
    iRowLen = rec['MaxLstOrd']

    # get the list of dates to pull data for
    lDtLimits = [] # check for any start or end limits
    if bkDict['OutputDataStart'] != None: # any start criteria
        lDtLimits.append(" DataDates.Date >= '" + bkDict['OutputDataStart'].strftime(sFmtDateOnly) + "' ")
    if bkDict['OutputDataEnd'] != None: # any end criteria
        if len(lDtLimits) > 0:
            lDtLimits.append("AND")
        lDtLimits.append(" DataDates.Date <= '" + bkDict['OutputDataEnd'].strftime(sFmtDateOnly) + "' ")
    if len(lDtLimits) > 0: # complete any WHERE clause
        lDtLimits.insert(0, "\nWHERE ")
    stSQL = "SELECT DataDates.Date FROM DataDates" + "".join(lDtLimits) + "\nORDER BY DataDates.Date;"
    cr.execute(stSQL)
    recs = cr.fetchall()
    lDates = []
    for rec in recs:
        lDates.append(rec['Date'])
    # define the following here; used many times the same
    stSQLVisCol = "SELECT * FROM OutputColumns " \
        "WHERE WorkSheetID=? AND ListingOrder=? " \
        "ORDER BY ID;"
    
    for sDt in lDates:
        # get the data for each date
        # create a date that represents how we are going to label this date. Since all data queries
        # are by solar time, this is the 'solar time' representation of the day's "solar midnight"
        dtNominalDay = datetime.datetime.strptime(sDt, "%Y-%m-%d")
        # create a date which is the UT clock time when solar midnight occurs at this longitude for this nominal date
        tdSolarCorr = solarCorrection(sDt, bkDict['Longitude'])
        dtUTSolarMidnight = dtNominalDay + tdSolarCorr
        for iTimeSliceCt in range(bkDict['NumberOfTimeSlicesPerDay']):
            # nodes are at one half, three halves, 5 halves, ... of a time slice
            dtSolarTimeNode = dtNominalDay + (((2*iTimeSliceCt)+1) * tdHalfTimeSlice)
            # generate the UT clock time, corrected for longitude and equation-of-time
            # can be hours different from nominal (solar) time
            dtUTTimeNode = dtUTSolarMidnight + (((2*iTimeSliceCt)+1) * tdHalfTimeSlice)
            dtUTTimeBegin = dtUTTimeNode - tdHalfTimeSlice
            dtUTTimeEnd = dtUTTimeNode + tdHalfTimeSlice
            print "dtSolarTimeNode:", dtSolarTimeNode.strftime(sFmtFullDateTime)
            print "   dtUTTimeNode:", dtUTTimeNode.strftime(sFmtFullDateTime)
            
            # make a standard list of this many empty strings; some may remain empty
            lData = ['' for i in range(iRowLen)]
            for colDict in lCols:
                iVisColIndex = colDict['ListingOrder'] - 1
#                print "colDict:", colDict
                # multiple table records may contribute to the same visible column, if
                # it is type "Aggregate", and ColHead, AggType and ListingOrder are the same for all recs
                cr.execute(stSQLVisCol, (sheetID, colDict['ListingOrder']))
                # in most cases, there will be only one record (if > 1, only use the 1st)
                # deal with valid multiples under if ColType = "Aggregate"
                rec = cr.fetchone()
                stFmtPy = rec['Format_Python']
                stFmtXl = rec['Format_Excel']
                if rec['ColType'] == "Timestamp":
                    if formatValues == True:
                        if stFmtPy == None:
                            lData[iVisColIndex] = dtUTTimeNode.strftime(sFmtFullDateTime) #default
                        else:
                            try:
                                lData[iVisColIndex] = dtUTTimeNode.strftime(stFmtPy)
                            except:
                                lData[iVisColIndex] = 'format error'
                    else: # use default format that preserves all date/time information
                        lData[iVisColIndex] = dtUTTimeNode.strftime(sFmtFullDateTime)
                    # dress this up for other formats later
                if rec['ColType'] == "Constant":
                    lData[iVisColIndex] = rec['Constant']
                if rec['ColType'] == "Formula":
                    lData[iVisColIndex] = rec['Formula']
                    # figure out how to resolve formulas; for now just write them in
                if rec['ColType'] == "Aggregate":
                    # There may be multiple OutputColumns records that match on
                    #  ListingOrder, Column Heading, Aggregation Type, and Format
                    #  in this case, aggregate over all of them to produce cell contents.
                    if colDict['AggType'] == 'StDev': # not implemented yet
                        lData[iVisColIndex] = rec['AggType']
                    else:
                        lSql = ['SELECT ']
                        lSql.append(colDict['AggType'])
                        lSql.append('(CAST(Data.Value AS REAL)) AS Agg ' \
                                'FROM (OutputColumns LEFT JOIN ChannelSegments ' \
                                'ON (OutputColumns.AggDataSeriesID = ChannelSegments.SeriesID) ' \
                                'AND (OutputColumns.AggStationID = ChannelSegments.StationID)) ' \
                                'LEFT JOIN Data ON ChannelSegments.ChannelID = Data.ChannelID ' \
                                'WHERE OutputColumns.WorksheetID=? ' \
                                'AND OutputColumns.ListingOrder=? ' \
                                'AND Data.UTTimestamp>=ChannelSegments.SegmentBegin ' \
                                'AND Data.UTTimestamp<COALESCE(ChannelSegments.SegmentEnd, datetime("now")) ' \
                                'AND Data.UTTimestamp>=? ' \
                                'AND Data.UTTimestamp<? ' \
                                'AND Data.Use=1;')
                        stSQL = ''.join(lSql)
#                        print "stSQL:", stSQL
                        cr.execute(stSQL, (sheetID, colDict['ListingOrder'] ,dtUTTimeBegin, dtUTTimeEnd))
                        rec = cr.fetchone()
                        if rec['Agg'] != None:
                            if formatValues == True:
                                if stFmtPy == None:
                                    lData[iVisColIndex] = str(rec['Agg'])
                                else:
                                    lData[iVisColIndex] = stFmtPy % rec['Agg']
                            else: # deliver the value as a number
                                lData[iVisColIndex] = rec['Agg']

            yield lData
   
    # get the data for the columns
    # fields:  ID, WorksheetID, ColumnHeading, ColType, TimeSystem, TimeIsInterval, IntervalIsFrom,
    #  Constant, Formula,AggType, AggStationID, AggDataSeriesID, Format_Python, Format_Excel, ListingOrder

def offerSeriesForChannels():
    """
    If the Series for a Channel Segment is still Null, fill in the SeriesID if one is available.
    Presently, these are only available for Greenlogger files that have full metadata.
    """
    stSQL = """
        UPDATE ChannelSegments
        SET
         SeriesID = (SELECT tmpChanSegSeries.SeriesID 
          FROM tmpChanSegSeries
          WHERE tmpChanSegSeries.ChannelID = ChannelSegments.ChannelID)
        WHERE
         EXISTS (SELECT *
          FROM tmpChanSegSeries
          WHERE tmpChanSegSeries.ChannelID = ChannelSegments.ChannelID)
        AND ChannelSegments.SeriesID IS NULL;
    """
    try:
        curD.execute(stSQL)
    except:
        pass # fail silently

def clearParseLog():
    curT.executescript("""
        DROP TABLE IF EXISTS "tmpParseLog";
    """)
    tmpConn.execute("VACUUM")
    curT.executescript("""
        CREATE TABLE "tmpParseLog"
        ("ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
        "LogItem" VARCHAR(200));
    """)

def writeToParseLog(stLog):
    curT.execute("INSERT INTO tmpParseLog (LogItem) VALUES (?);", (stLog,))

# set up these defaults
noSensID = assureItemIsInTableField('(n/a)', 'Sensors', 'SensorSerialNumber')
noDataTypeID = assureItemIsInTableField('(n/a)', 'DataTypes', 'TypeText')
noDataUnitsID = assureItemIsInTableField('(n/a)', 'DataUnits', 'UnitsText')

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

if __name__ == "__main__":
    pass # nothing yet
