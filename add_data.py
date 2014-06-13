import wx, sqlite3, datetime
import os, sys, re, ast
import scidb

# add_data_TNP2
# TNP 8-JUN-2014 If units not specified, add units as 'NA'

sUTimeFmt = '%Y-%m-%d %H:%M:%S'

class DropTargetForFilesToParse(wx.FileDropTarget):
    def __init__(self, progressArea, msgArea):
        wx.FileDropTarget.__init__(self)
        self.progressArea = progressArea
        self.msgArea = msgArea

    def OnDropFiles(self, x, y, filenames):
        # for testing, disable clearing of the Parse Log
        #scidb.clearParseLog() 
        self.progressArea.SetInsertionPointEnd()
#        self.progressArea.WriteText("\n%d file(s) dropped at %d,%d:\n" %
#                              (len(filenames), x, y))
        self.progressArea.WriteText("\n%d file(s) dropped\n" % (len(filenames),))

        tStartParse = datetime.datetime.now()
        for name in filenames:
            self.progressArea.WriteText(name + '\n')
            fileresult = self.parseFileIntoDB(name)
#            self.progressArea.SetInsertionPointEnd()
#            self.progressArea.WriteText(fileresult + '\n')
        dPR = datetime.datetime.now() - tStartParse
        print "file(s) parsed, elapsed seconds:", dPR.total_seconds()
        tStartDD = datetime.datetime.now()
        print "about to do refreshDataDates"
        scidb.refreshDataDates()
        dDD = datetime.datetime.now() - tStartDD
        print "refreshDataDates, elapsed seconds:", dDD.total_seconds()
        tStartFX = datetime.datetime.now()
        scidb.autofixChannelSegments()
        print "about to do autofixChannelSegments"
        dFX = datetime.datetime.now() - tStartFX
        print "autofixChannelSegments, elapsed seconds:", dFX.total_seconds()

    def parseFileIntoDB(self, filename):
        """
        given a string which is the full path to a file
        determines the file structure and parses the
        data into the proper tables

        """
        tStartParse = datetime.datetime.now()
        dctInfo = {}
        dctInfo['fullPath'] = filename
        
        self.getFileInfo(dctInfo)
#        print dctInfo
        for k in dctInfo:
            print k, dctInfo[k]
        if 'isDir' in dctInfo: # a folder was dragged in, get everything inside it
            scidb.writeToParseLog(tStartParse.strftime(sUTimeFmt) + ", start processing folder: " + dctInfo['fullPath'])
            print "Processing folder", dctInfo['fullPath']
            for subdir, dirs, files in os.walk(dctInfo['fullPath']):
            #    print "subdir, dirs, files:", subdir, dirs, files
                for file in files:
                    stPath = os.path.join(subdir, file)
#                    print stPath
                    fileresult = self.parseFileIntoDB(stPath)
            stParseSecs = "%.3f" % ((datetime.datetime.now() - tStartParse).total_seconds())
            scidb.writeToParseLog(stParseSecs + " seconds elapsed processing folder: " + dctInfo['fullPath'])
        else: # a file
            scidb.writeToParseLog(tStartParse.strftime(sUTimeFmt) + ", start processing file: " + dctInfo['fullPath'])
            if not ('dataFormat' in dctInfo):
                stLog = '"' + dctInfo['fileName'] + '", could not determine data format'
                self.progressArea.SetInsertionPointEnd()
                self.progressArea.WriteText(stLog + '\n')
                stParseSecs = "%.3f" % ((datetime.datetime.now() - tStartParse).total_seconds())
                scidb.writeToParseLog(stParseSecs + " seconds elapsed; " + stLog)
                return stLog

            self.progressArea.SetInsertionPointEnd()
            stLog = '"' + dctInfo['fileName'] + '" data format detected as: "' + dctInfo['dataFormat'] + '"'
            self.progressArea.WriteText(stLog + '\n')
            scidb.writeToParseLog(stLog)
            if dctInfo['dataFormat'] == r"Hoboware text export":
                self.parseHoboWareTextFile(dctInfo)
            elif dctInfo['dataFormat'] == r"Greenlogger text file":
                self.parseGLTextFile(dctInfo)
            elif dctInfo['dataFormat'] == r"blueTerm log file":
                self.parseBlueTermFile(dctInfo)
            # add others as elif here
            else:
                dctInfo['stParseMsg'] = 'Parsing of this data format is not implemented yet'
                self.progressArea.SetInsertionPointEnd()
                self.progressArea.WriteText(dctInfo['stParseMsg'] + '\n')
            if 'stParseMsg' in dctInfo:
                scidb.writeToParseLog(dctInfo['stParseMsg'])

            stParseSecs = "%.3f" % ((datetime.datetime.now() - tStartParse).total_seconds())
            scidb.writeToParseLog(stParseSecs + " seconds elapsed parsing file")
        return "Done"                       



    def parseBlueTermFile(self, infoDict):
        """
        a BlueTerm log file can contain captured data from a series of daily
        GL text files, possibly even from different loggers
        """
        dataRecItemCt = 0
        dataRecsAdded = 0
        dataRecsDupSkipped = 0

        self.putTextLinesIntoTmpTable(infoDict)

        # find the different data dump segments
        # within each one, data will be from only one logger, and so we
        #  can use the same metadata header
        # make a list of 2-tuples; tuple item 0 = the starting ID of the
        # dump segment and tuple item 1 = the ending ID
        lDmpSegs = []
        stSQL = """SELECT ID, Line FROM tmpLines
            WHERE Line = '{"datadump":"begin"}' OR Line = '{"datadump":"end"}'
            ORDER BY ID;"""
        dmSegs = scidb.curT.execute(stSQL).fetchall()
        # begin or end may be missing, due to log interruption
        idSegStart = None
        idSegEnd = None
        # only use segments that have valid begin/end
        for dmSegItm in dmSegs:
            if dmSegItm['Line'] == '{"datadump":"begin"}':
                idSegStart = dmSegItm['ID']
            elif dmSegItm['Line'] == '{"datadump":"end"}':
                if idSegStart != None:
                    # make the tuple
                    tSeg = (idSegStart, dmSegItm['ID'])
                    # append to list
                    lDmpSegs.append(tSeg)
                    # null the vars
                    idSegStart = None
                    idSegEnd = None
            else: # this should not happen, but tie up if it does
                idSegStart = None
                idSegEnd = None
                    
        print "dump segments:", lDmpSegs
        
        # being worked on >>>>
        iNumSegs = len(lDmpSegs)
        if iNumSegs == 0:
            infoDict['stParseMsg'] = " No valid data segments in file."
            # will skip following loop
        iCtSeg = 0
        for tSeg in lDmpSegs:
            iCtSeg += 1
            idSegStart, idSegEnd = tSeg
            # get the metadata header; if multiple will all be the same for one dump segment
            stSQL = """SELECT Line 
                    FROM tmpLines 
                    WHERE ID > ? AND ID < ? 
                    AND Line LIKE '{"Instrument identifier":%'
                    GROUP BY Line;"""
            mtDat =  scidb.curT.execute(stSQL, tSeg).fetchone()
            dictHd = ast.literal_eval(mtDat['Line'])
            # somewhat redundant to do 'LoggerSerialNumber' here (fn 'assureChannelIsInDB' would fill in
            # later), but allows putting Model into the DB
            iInstSpecID = scidb.assureItemIsInTableField(dictHd['Model'], "InstrumentSpecs", "InstrumentSpec")
            iLoggerID = scidb.assureItemIsInTableField(dictHd['Instrument identifier'], "Loggers", "LoggerSerialNumber")
            scidb.curD.execute("UPDATE Loggers SET InstrumentSpecID = ? WHERE ID = ?;", (iInstSpecID, iLoggerID))
            
            # get the hour offset(s); most files will have only one
            stSQL = "SELECT substr(Line, 21, 3) as TZ FROM tmpLines " \
                    "WHERE ID > ? AND ID < ? " \
                    "AND Line LIKE '____-__-__ __:__:__ ___%' GROUP BY TZ;"
            hrOffsets = scidb.curT.execute(stSQL, tSeg).fetchall()
            for hrOffset in hrOffsets:
                iTimeZoneOffset = int(hrOffset['TZ'])
                # make a dictionary of channel IDs for data lines that have this hour offset
                # would be slightly different for different hour offsets
                lCols = dictHd['Columns'] # get col metadata; this is a list of dictionaries
    #            # it is indexed by the columns list, and is zero-based
    #            lCh = [0 for i in range(len(lCols))] # initially, fill with all zeroes
                dictChannels = {} # this is the dictionary we will build
                for dictCol in lCols:
                    # somewhat redundant to fill these in before calling function 'assureChannelIsInDB', but
                    #  allows assigning sensor device types
                    iDeviceTypeID = scidb.assureItemIsInTableField(dictCol['Device'], "DeviceSpecs", "DeviceSpec")
                    iSensorID = scidb.assureItemIsInTableField(dictCol['Identifier'], "Sensors", "SensorSerialNumber")
                    scidb.curD.execute("UPDATE Sensors SET DeviceSpecID = ? WHERE ID = ?;", (iDeviceTypeID, iSensorID))
    #                iDataTypeID = scidb.assureItemIsInTableField(dictCol['DataType'], "DataTypes", "TypeText")
    #                iDataUnitsID = scidb.assureItemIsInTableField(dictCol['DataUnits'], "DataUnits", "UnitsText")
                    # build list to create the channel
                    # list items are: ChannelID, originalCol, Logger, Sensor, dataType, dataUnits, hrOffset, new
                    lChannel = [0, dictCol['Order'], dictHd['Instrument identifier'], dictCol['Identifier'],
                                dictCol['DataType'], dictCol['DataUnits'], iTimeZoneOffset, '']
                    dictChannels[dictCol['Order']] = (lChannel[:]) # the key is the column number
                    scidb.assureChannelIsInDB(dictChannels[dictCol['Order']]) # get or create the channel
                    iChannelID = dictChannels[dictCol['Order']][0]
                    # store the column name as a Series
                    iSeriesID = scidb.assureItemIsInTableField(dictCol['Name'], "DataSeries", "DataSeriesDescription")
                    # tie it to this Channel, to offer later
                    stSQLcs = 'INSERT INTO tmpChanSegSeries(ChannelID, SeriesID) VALUES (?, ?);'
                    try:
                        scidb.curD.execute(stSQLcs, (iChannelID, iSeriesID))
                    except sqlite3.IntegrityError:
                        pass # silently ignore duplicates

    #            print 'Before Channel function'
    #            for ky in dictChannels.keys():
    #                print ky, dictChannels[ky][:]
    #            for ky in dictChannels.keys():
    #                scidb.assureChannelIsInDB(dictChannels[ky])
    #            print 'After Channel function'
    #            for ky in dictChannels.keys():
    #                print ky, dictChannels[ky][:]

                # make a list of channel IDs for the set of lines with this HrOffset, for quick lookup
                # it is indexed by the columns list, and is zero-based
                lCh = []
                for iCol in range(len(lCols)):
                    iNomCol = iCol + 1
                    if iNomCol in dictChannels:
                        lChanSet = dictChannels[iNomCol][:]
                        lCh.append(lChanSet[0])
                    else: # does not correspond to a data colum
                        lCh.append(0) # placeholder, to make list indexes work right             
            
                # done setting up channels, get data lines
                stSQL = "SELECT ID, Line FROM tmpLines " \
                    "WHERE ID > ? AND ID < ? " \
                    "AND substr(Line, 21, 3) = ? " \
                    "AND Line LIKE '____-__-__ __:__:__ ___%' ORDER BY ID;"
                recs = scidb.curT.execute(stSQL, (idSegStart, idSegEnd, hrOffset['TZ'],)).fetchall()
                iNumSegLines = len(recs)
                iCtSegLines = 0
                for rec in recs:
                    iCtSegLines += 1
                    lData = rec['Line'].split('\t')
                    # item zero is the timestamp followed by the timezone offset
                    sTimeStamp = lData[0][:-4] # drop timezone offset, we already have it
                    tsAsTime = datetime.datetime.strptime(sTimeStamp, "%Y-%m-%d %H:%M:%S")
                    tsAsTime.replace(tzinfo=None) # make sure it does not get local timezone info
                    tsAsTime = tsAsTime + datetime.timedelta(hours = -iTimeZoneOffset)
                    tsAsDate = tsAsTime.date()
                    stSQL = "INSERT INTO Data (UTTimestamp, ChannelID, Value) VALUES (?, ?, ?)"
                    for iCol in range(len(lData)):
                        if iCol > 0: # an item of data
                            # give some progress diagnostics
                            dataRecItemCt += 1
                            if dataRecItemCt % 100 == 0:
                                self.msgArea.ChangeValue("Segment " + str(iCtSeg) +
                                    " of " + str(iNumSegs) +
                                    ", HrOffset " + str(iTimeZoneOffset) +
                                    ", Line " + str(iCtSegLines) +
                                    " of " + str(iNumSegLines) + "; " +
                                    str(dataRecsAdded) + " records added, " +
                                    str(dataRecsDupSkipped) + " duplicates skipped.")
                                wx.Yield()
                            try: # much faster to try and fail than to test first
                                scidb.curD.execute(stSQL, (tsAsTime, lCh[iCol], lData[iCol]))
                                dataRecsAdded += 1 # count it
                            except sqlite3.IntegrityError: # item is already in Data table
                                dataRecsDupSkipped += 1 # count but otherwise ignore
                            finally:
                                wx.Yield()
        # <<<<< being worked on
        # finished parsing lines
        infoDict['numNewDataRecsAdded'] = dataRecsAdded
        infoDict['numDupDataRecsSkipped'] = dataRecsDupSkipped
        infoDict['stParseMsg'] = str(infoDict['lineCt']) + " lines processed; " + \
            str(dataRecsAdded) + " data records added to database, " + \
            str(dataRecsDupSkipped) + " duplicates skipped."
        self.msgArea.ChangeValue(infoDict['stParseMsg'])
        

    def parseGLTextFile(self, infoDict):
        """
        parse a GreenLogger text file
        """
        dataRecItemCt = 0
        dataRecsAdded = 0
        dataRecsDupSkipped = 0

#        print "About to put lines into temp table"
        self.putTextLinesIntoTmpTable(infoDict)
#        print "Finished putting lines into temp table"
        # get the metadata header
        stSQL = """SELECT Line FROM tmpLines WHERE Line LIKE '{"Instrument identifier":%' GROUP BY Line;"""
        mtDat =  scidb.curT.execute(stSQL).fetchone()
        dictHd = ast.literal_eval(mtDat['Line'])
        # somewhat redundant to do 'LoggerSerialNumber' here (fn 'assureChannelIsInDB' would fill in
        # later), but allows putting Model into the DB
        iInstSpecID = scidb.assureItemIsInTableField(dictHd['Model'], "InstrumentSpecs", "InstrumentSpec")
        iLoggerID = scidb.assureItemIsInTableField(dictHd['Instrument identifier'], "Loggers", "LoggerSerialNumber")
        scidb.curD.execute("UPDATE Loggers SET InstrumentSpecID = ? WHERE ID = ?;", (iInstSpecID, iLoggerID))
        
        # get the hour offset(s); most files will have only one
        stSQL = "SELECT substr(Line, 21, 3) as TZ FROM tmpLines " \
                "WHERE Line LIKE '____-__-__ __:__:__ ___%' GROUP BY TZ;"
        hrOffsets = scidb.curT.execute(stSQL).fetchall()
        for hrOffset in hrOffsets:
            iTimeZoneOffset = int(hrOffset['TZ'])
            # make a dictionary of channel IDs for data lines that have this hour offset
            # would be slightly different for different hour offsets
            lCols = dictHd['Columns'] # get col metadata; this is a list of dictionaries
#            # it is indexed by the columns list, and is zero-based
#            lCh = [0 for i in range(len(lCols))] # initially, fill with all zeroes
            dictChannels = {} # this is the dictionary we will build
            for dictCol in lCols:
                # somewhat redundant to fill these in before calling function 'assureChannelIsInDB', but
                #  allows assigning sensor device types
                iDeviceTypeID = scidb.assureItemIsInTableField(dictCol['Device'], "DeviceSpecs", "DeviceSpec")
                iSensorID = scidb.assureItemIsInTableField(dictCol['Identifier'], "Sensors", "SensorSerialNumber")
                scidb.curD.execute("UPDATE Sensors SET DeviceSpecID = ? WHERE ID = ?;", (iDeviceTypeID, iSensorID))
#                iDataTypeID = scidb.assureItemIsInTableField(dictCol['DataType'], "DataTypes", "TypeText")
#                iDataUnitsID = scidb.assureItemIsInTableField(dictCol['DataUnits'], "DataUnits", "UnitsText")
                # build list to create the channel
                # list items are: ChannelID, originalCol, Logger, Sensor, dataType, dataUnits, hrOffset, new
                lChannel = [0, dictCol['Order'], dictHd['Instrument identifier'], dictCol['Identifier'],
                            dictCol['DataType'], dictCol['DataUnits'], iTimeZoneOffset, '']
                dictChannels[dictCol['Order']] = (lChannel[:]) # the key is the column number
                scidb.assureChannelIsInDB(dictChannels[dictCol['Order']]) # get or create the channel
                iChannelID = dictChannels[dictCol['Order']][0]
                # store the column name as a Series
                iSeriesID = scidb.assureItemIsInTableField(dictCol['Name'], "DataSeries", "DataSeriesDescription")
                # tie it to this Channel, to offer later
                stSQLcs = 'INSERT INTO tmpChanSegSeries(ChannelID, SeriesID) VALUES (?, ?);'
                try:
                    scidb.curD.execute(stSQLcs, (iChannelID, iSeriesID))
                except sqlite3.IntegrityError:
                    pass # silently ignore duplicates

#            print 'Before Channel function'
#            for ky in dictChannels.keys():
#                print ky, dictChannels[ky][:]
#            for ky in dictChannels.keys():
#                scidb.assureChannelIsInDB(dictChannels[ky])
#            print 'After Channel function'
#            for ky in dictChannels.keys():
#                print ky, dictChannels[ky][:]

            # make a list of channel IDs for the set of lines with this HrOffset, for quick lookup
            # it is indexed by the columns list, and is zero-based
            lCh = []
            for iCol in range(len(lCols)):
                iNomCol = iCol + 1
                if iNomCol in dictChannels:
                    lChanSet = dictChannels[iNomCol][:]
                    lCh.append(lChanSet[0])
                else: # does not correspond to a data colum
                    lCh.append(0) # placeholder, to make list indexes work right             
        
            # done setting up channels, get data lines
            stSQL = "SELECT ID, Line FROM tmpLines WHERE substr(Line, 21, 3) = ? " \
                "AND Line LIKE '____-__-__ __:__:__ ___%' ORDER BY ID;"
            recs = scidb.curT.execute(stSQL, (hrOffset['TZ'],)).fetchall()
            for rec in recs:
                lData = rec['Line'].split('\t')
                # item zero is the timestamp followed by the timezone offset
                sTimeStamp = lData[0][:-4] # drop timezone offset, we already have it
                tsAsTime = datetime.datetime.strptime(sTimeStamp, "%Y-%m-%d %H:%M:%S")
                tsAsTime.replace(tzinfo=None) # make sure it does not get local timezone info
                tsAsTime = tsAsTime + datetime.timedelta(hours = -iTimeZoneOffset)
                tsAsDate = tsAsTime.date()
                stSQL = "INSERT INTO Data (UTTimestamp, ChannelID, Value) VALUES (?, ?, ?)"
                for iCol in range(len(lData)):
                    if iCol > 0: # an item of data
                        # give some progress diagnostics
                        dataRecItemCt += 1
                        if dataRecItemCt % 100 == 0:
                            self.msgArea.ChangeValue("Line " + str(rec['ID']) +
                                " of " + str(infoDict['lineCt']) + "; " +
                                str(dataRecsAdded) + " records added, " +
                                str(dataRecsDupSkipped) + " duplicates skipped.")
                            wx.Yield()
                        try: # much faster to try and fail than to test first
                            scidb.curD.execute(stSQL, (tsAsTime, lCh[iCol], lData[iCol]))
                            dataRecsAdded += 1 # count it
                        except sqlite3.IntegrityError: # item is already in Data table
                            dataRecsDupSkipped += 1 # count but otherwise ignore
                        finally:
                            wx.Yield()

        # finished parsing lines
        infoDict['numNewDataRecsAdded'] = dataRecsAdded
        infoDict['numDupDataRecsSkipped'] = dataRecsDupSkipped
        infoDict['stParseMsg'] = str(infoDict['lineCt']) + " lines processed; " + \
            str(dataRecsAdded) + " data records added to database, " + \
            str(dataRecsDupSkipped) + " duplicates skipped."
        self.msgArea.ChangeValue(infoDict['stParseMsg'])

        
    def parseHoboWareTextFile(self, infoDict):
        """
        parse a data file exported as text by HoboWare
        """
        sStrip = '" \x0a\x0d' # characters to strip from parsed items
        # regular expression pattern to find logger number
        pLogger = re.compile(r'LGR S/N: (?P<nLogger>\d+)')
        # regular expression pattern to find sensor number
        pSensor = re.compile(r'SEN S/N: (?P<nSensor>\d+)')
        # regular expression pattern to find hour offset
        pHrOffset = re.compile(r'Time, GMT(?P<sHrOffset>.+)')
        dataRecItemCt = 0
        dataRecsAdded = 0
        dataRecsDupSkipped = 0

        print "About to put lines into temp table"
        self.putTextLinesIntoTmpTable(infoDict)
        print "Finished putting lines into temp table"
        #parse file, start with header line; 1st line in this file format
        scidb.curT.execute("SELECT * FROM tmpLines ORDER BY ID;")
        for rec in scidb.curT:
            if rec['ID'] == 1:
                """
                Build a dictionary of the channels.
                The indexes will be the column numbers because all data files have at least that.
                The value will be a 7-membered list
                The first item in each list will be the primary key in the Channels table.
                The list is first created with this = 0.
                The rest of the list is built up, then the list is sent to a function
                 that looks in the database.
                The function fills in the primary key, either existing or newly created.
                List item 7 will be "new" if the record is new, otherwise "existing"
                The list contains the text values of logger serial number, sensor serial number,
                 data type, and data units.
                The function takes care of filling in all these in their respective tables.
                When the dictionary is complete, the calling procedure can quickly insert data values
                 into the data table by just pulling list item [0] for the dictionary key, which key
                 is the column number in the source file.
                This loose structure allows some kludgy workarounds for bugs that were in some versions
                 of the data files.
                """
                lHdrs = rec['Line'].split('\t')
                # ignore item zero, just a pound sign and possibly three junk characters
                # item 1 is the hour offset, and clue to export bugs we need to workaround
                sHd = lHdrs[1].strip(sStrip)
                m = pHrOffset.search(sHd)
                if m:
                    sTimeOffset = m.group('sHrOffset')
                    lTimeOffsetComponents = sTimeOffset.split(':')
                    sTimeOffsetHrs = lTimeOffsetComponents[0]
                    iHrOffset = int(sTimeOffsetHrs)
                else:
                    iHrOffset = 0
               
                dictChannels = {}
                # list items are: ChannelID, originalCol, Logger, Sensor, dataType, dataUnits, hrOffset, new
                lChannel = [0, 0, '', '', '', '', iHrOffset, '']

                for iCol in range(len(lHdrs)):
                    # skip items 0 & 1
                    if iCol > 1: # a header for a data column
                        lChannel[1] = iCol + 1 # stored columns are 1-based
                        sHd = lHdrs[iCol].strip(sStrip)
                        # get the type and units
                        lTypeUnits = sHd.split('(',2)
                        sTypeUnits = lTypeUnits[0].strip(' ')
                        lTypeUnits = sTypeUnits.split(',')
                        
                        ## TNP_MOD
                        ## If units specified, make units 'NA'
                        if(len(lTypeUnits)==1):
                            lTypeUnits.append('NA')
                        
                        if lTypeUnits[0]:
                            sType = lTypeUnits[0].strip(' ')
                        else:
                            sType = '(na)'
                        lChannel[4] = sType
                        if lTypeUnits[1]:
                            sUnits = lTypeUnits[1].strip(' ')
                        else:
                            sUnits = '(na)'
                        lChannel[5] = sUnits
                        # get the logger ID and sensor ID
                        m = pLogger.search(sHd)
                        if m:
                            sLoggerID = m.group('nLogger')
                        else:
                            sLoggerID = '(na)'
                        lChannel[2] = sLoggerID
                        m = pSensor.search(sHd)
                        if m:
                            sSensorID = m.group('nSensor')
                        else:
                            sSensorID = "(na)"
                        lChannel[3] = sSensorID
                        dictChannels[iCol + 1] = (lChannel[:])
                # gone through all the headers, apply bug workarounds here
                
                print 'Before Channel function'
                for ky in dictChannels.keys():
                    print ky, dictChannels[ky][:]
                for ky in dictChannels.keys():
                    scidb.assureChannelIsInDB(dictChannels[ky])
                print 'After Channel function'
                for ky in dictChannels.keys():
                    print ky, dictChannels[ky][:]
                # make a list of channel IDs for the rest of this file, for quick lookup
                # it is indexed by the columns list, and is zero-based
                lCh = []
                for iCol in range(len(lHdrs)):
                    iNomCol = iCol + 1
                    if iNomCol in dictChannels:
                        lChanSet = dictChannels[iNomCol][:]
                        lCh.append(lChanSet[0])
                    else: # does not correspond to a data colum
                        lCh.append(0) # placeholder, to make list indexes work right
                
            else: # not the 1st (header) line, but a line of data
                lData = rec['Line'].split('\t')
                # ignore item zero, a line number, not used
                sTimeStamp = lData[1]
                tsAsTime = datetime.datetime.strptime(sTimeStamp, "%Y-%m-%d %H:%M:%S")
                tsAsTime.replace(tzinfo=None) # make sure it does not get local timezone info
                tsAsTime = tsAsTime + datetime.timedelta(hours = -iHrOffset)
                tsAsDate = tsAsTime.date()
                stSQL = "INSERT INTO Data (UTTimestamp, ChannelID, Value) VALUES (?, ?, ?)"
                for iCol in range(len(lData)):
                    if iCol > 1: # an item of data
                        # give some progress diagnostics
                        dataRecItemCt += 1
                        if dataRecItemCt % 100 == 0:
                            self.msgArea.ChangeValue("Line " + str(rec['ID']) +
                                " of " + str(infoDict['lineCt']) + "; " +
                                str(dataRecsAdded) + " records added, " +
                                str(dataRecsDupSkipped) + " duplicates skipped.")
                            wx.Yield()
                        try: # much faster to try and fail than to test first
                            scidb.curD.execute(stSQL, (tsAsTime, lCh[iCol], lData[iCol]))
                            dataRecsAdded += 1 # count it
                        except sqlite3.IntegrityError: # item is already in Data table
                            dataRecsDupSkipped += 1 # count but otherwise ignore
                        finally:
                            wx.Yield()

        # finished parsing lines
        infoDict['numNewDataRecsAdded'] = dataRecsAdded
        infoDict['numDupDataRecsSkipped'] = dataRecsDupSkipped
        infoDict['stParseMsg'] = str(infoDict['lineCt']) + " lines processed; " + \
            str(dataRecsAdded) + " data records added to database, " + \
            str(dataRecsDupSkipped) + " duplicates skipped."
        self.msgArea.ChangeValue(infoDict['stParseMsg'])        
       
    def putTextLinesIntoTmpTable(self, infoDict):
        """
        Usable for data files that are in text format:
        This function puts the lines as separate records into the temporary
        table "tmpLines", which it creates new each time.
        Adds the member infoDict['lineCt']
        """
        scidb.curT.executescript("""
            DROP TABLE IF EXISTS "tmpLines";
        """)
        scidb.tmpConn.execute("VACUUM")
        scidb.curT.executescript("""
            CREATE TABLE "tmpLines"
            ("ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
            "Line" VARCHAR(200));
        """)
        stSQL = 'INSERT INTO tmpLines(Line) VALUES (?);'
        ct = 0
        numToInsertAtOnce = 1000 # arbitrary number, guessing to optimize
        lstLines = []
        with open(infoDict['fullPath'], 'rb') as f:
            
            for sLine in f:
                ct += 1
                # much faster to insert a batch at once
                wx.Yield()
                st = sLine.strip() # removes ambiguous x0A, x0D, etc, chars from ends
                if st != '': # ignore empty lines

                    m = re.search(r"\{.*\}", st) # if the line has a JSON string in it
                    if m: # take it out into a separate line
                        sJ = m.group(0)
                        lstLines.append((sJ,))
                        stx = st.replace(sJ,'')
                        if len(stx) > 0:
                            lstLines.append((stx,))
                    else:
                        lstLines.append((st,))
                wx.Yield()
                if  len(lstLines) >= numToInsertAtOnce:
                    self.msgArea.ChangeValue("counting lines in file: " +
                            str(ct))
                    scidb.tmpConn.execute("BEGIN DEFERRED TRANSACTION")
                    scidb.curT.executemany(stSQL, lstLines)
                    scidb.tmpConn.execute("COMMIT TRANSACTION")
                    lstLines = []
                    wx.Yield()
                scidb.tmpConn.commit()
                wx.Yield()
        # file should be closed by here, avoid possible corruption if left open
        # put last batch of lines into DB
        if  len(lstLines) > 0:
            wx.Yield()
            scidb.tmpConn.execute("BEGIN DEFERRED TRANSACTION")
            scidb.curT.executemany(stSQL, lstLines)
            scidb.tmpConn.execute("COMMIT TRANSACTION")
            lstLines = []
            wx.Yield()
        # get count
        scidb.curT.execute("SELECT count(*) AS 'lineCt' FROM tmpLines;")
        t = scidb.curT.fetchone() # a tuple with one value
        infoDict['lineCt'] = t[0]
        self.msgArea.ChangeValue(str(infoDict['lineCt']) + " lines in file")
        wx.Yield()
        return


    def getFileInfo(self, infoDict):
        """
        Data files have so many possible parameters, use a dictionary to track them
        Only requirement on entering this function is the dictionary has a
        member 'fullPath', which is a string that is a full file path
        """
        if (os.path.isdir(infoDict['fullPath'])):
#            infoDict['fileErr'] = "Path is a directory"
            infoDict['isDir'] = True
            return
        if not os.path.exists(infoDict['fullPath']):
            infoDict['fileErr'] = "File does not exist"
            return
        if not os.path.isfile(infoDict['fullPath']):
            infoDict['fileErr'] = "Not a file"
            return
        infoDict['fileName'] = os.path.basename(infoDict['fullPath'])
        infoDict['fileSize'] = os.path.getsize(infoDict['fullPath'])
        # splitext gives a 2-tuple of what's before and after the ext delim
        infoDict['fileExtension'] = os.path.splitext(infoDict['fullPath'])[1]
        if infoDict['fileExtension'] == r'.dtf':
            infoDict['dataFormat'] = "binary Onset DTF"
            return
        # example 'blueTerm_20140513_164442.log'
        if infoDict['fileName'][:9] == r'blueTerm_' and infoDict['fileExtension'] == r'.log':
            infoDict['dataFormat'] = "blueTerm log file"
            return
        # find first non-blank line, and keep track of which line it is
        iLineCt = 0
        iBytesSoFar = 0
        try:
            f = open(infoDict['fullPath'], 'rb')
            while True:
                iBytesSoFar = f.tell()
                sLine = f.readline()
                if (sLine == ""): # empty when no more lines can be read
                    break
                if sLine.strip() == '': # removes ambiguous x0A, x0D, etc, chars from ends
                    continue # ignore empty lines at the beginning
                iLineCt += 1
                # diagnostics
#                if iLineCt == 1:
#                   infoDict['firstLine'] = sLine
                # format can be determined in first few lines or not at all
                if iLineCt >= 6:
                    break
                if len(sLine.strip()) > 0: # not a blank line
                    # test if it is text file exported by Hoboware
                    # following kludges are because Onset changed output file format
                    # i.e. different bugs through various versions of Hoboware
                    # details are important to avoid glitches during actual import
                    # in 2010, header line had only "Time..."
#                    lDiagnostics.append("sLine[:14]= " + sLine[:14])
                    if iLineCt == 1 and sLine[:14] == '"#"\t"Time, GMT':
                        infoDict['dataFormat'] = "Hoboware text export"
                        infoDict['yearVersion'] = 2010
                        break
                    
                    # in 2011, header line had "Date Time...:
                    # 1st part of 1st line should be (including quotes): "#" "Date Time, GMT
#                    lDiagnostics.append("sLine[:19]= " + sLine[:19])
                    if iLineCt == 1 and sLine[:19] == '"#"\t"Date Time, GMT':
                        infoDict['dataFormat'] = "Hoboware text export"
                        infoDict['yearVersion'] = 2011
                        break
                    
                    # in version 3.5.0 (released 2013), header starts with additional characters:
                    # 1st part of 1st line after 3 junk characters
                    # should be (including quotes): "#" "Date Time, GMT
#                    lDiagnostics.append("sLine[3:22]= " + sLine[3:22])
                    if iLineCt == 1 and  (sLine[3:22] == '"#"\t"Date Time, GMT'):
                        infoDict['dataFormat'] = "Hoboware text export"
                        infoDict['yearVersion'] = 2013
                        break
                    
                    # Test for other data formats
                    
                    if iLineCt == 1 and ('PuTTY log' in sLine):
                        infoDict['dataFormat'] = "PuTTY log"
                        break

                    if ('Timestamp\tBBDn\tIRDn\tBBUp\tIRUp\tT(C)\tVbatt(mV)' in sLine):
                        infoDict['dataFormat'] = "Greenlogger text file"
                        infoDict['versionNumber'] = 0
                        # version 0 means no metadata, simple text header is 1st non-blank line
                        break

                    if ('{"Instrument identifier":' in sLine):
                        infoDict['dataFormat'] = "Greenlogger text file"
                        infoDict['versionNumber'] = 1
                        # version 1 means JSON metadata header is 1st non-blank line
                        break

                    # test for iButton file
                    # look at 2nd line
                    f.seek(0)
                    sLine = f.readline()
                    iLineCt = 1 # prev verified 1st line existed
                    sLine = f.readline()
                    if (sLine == ""):
                        break
                    iLineCt += 1
                    #  1st part of 2nd line should be (including quotes): "Timezone",
#                    lDiagnostics.append("line " + str(iLineCt) + ", [:11]= " + sLine[:11])
                    if not (iLineCt == 2 and sLine[:11] == '"Timezone",'):
                        break
                    # look at 4th line, 3rd line should be blank
                    sLine = f.readline()
                    if (sLine == ""):
                        break
                    iLineCt += 1
                    sLine = f.readline()
                    if (sLine == ""):
                        break
                    iLineCt += 1
                    # 1st part of 4th line should be (including quotes): "Serial No.","
#                    lDiagnostics.append("line " + str(iLineCt) + ", [:14]= " + sLine[:14])
                    if not (iLineCt == 4 and sLine[:14] == '"Serial No.","'):
                        break
                    # look at 5th line 
                    sLine = f.readline()
                    if (sLine == ""):
                        break
                    iLineCt += 1
                    # 1st part of 5th line should be (including quotes): "Location:","
#                    lDiagnostics.append("line " + str(iLineCt) + ", [:13]= " + sLine[:13])
                    if iLineCt == 5 and sLine[:13] == '"Location:","':
                        infoDict['dataFormat'] = "iButton"
                        break


            f.close()
        except IOError, error:
            infoDict['fileErr'] = 'Error opening file\n' + str(error)
            try:
                f.close()
            except:
                pass
        except UnicodeDecodeError, error:
            infoDict['fileErr'] = 'Cannot open non ascii files\n' + str(error)
            try:
                f.close()
            except:
                pass


class ParseFilesPanel(wx.Panel):
    def __init__(self, parent, id):
        wx.Panel.__init__(self, parent, id)
        self.InitUI()

    def InitUI(self):

        GBSizer = wx.GridBagSizer(5, 5)

        hdr = wx.StaticText(self, label="Drag files below to add their data to the database")
        GBSizer.Add(hdr, pos=(0, 0), span=(1, 2), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)

        btnShowLog = wx.Button(self, label="Show Log", size=(90, 28))
        btnShowLog.Bind(wx.EVT_BUTTON, lambda evt, str=btnShowLog.GetLabel(): self.onClick_BtnShowLog(evt, str))
#        btnShowLog.Bind(wx.EVT_BUTTON, OnBtnShowLogClick)
        GBSizer.Add(btnShowLog, pos=(0, 5), flag=wx.RIGHT|wx.BOTTOM, border=5)

        textProgress = wx.TextCtrl(self, style = wx.TE_MULTILINE)
        GBSizer.Add(textProgress, pos=(1, 0), span=(4, 6),
            flag=wx.EXPAND|wx.TOP|wx.RIGHT|wx.BOTTOM, 
            border=5)

        lblProgTitle = wx.StaticText(self, wx.ID_ANY, "Progress:")
        GBSizer.Add(lblProgTitle, pos=(5, 0), span=(1, 1),
            flag=wx.EXPAND|wx.TOP|wx.RIGHT|wx.BOTTOM, 
            border=5)

        textProgMsgs = wx.TextCtrl(self, style = wx.TE_MULTILINE)
        GBSizer.Add(textProgMsgs, pos=(5, 1), span=(1, 5),
            flag=wx.EXPAND|wx.TOP|wx.RIGHT|wx.BOTTOM, 
            border=5)
        
        dt = DropTargetForFilesToParse(textProgress, textProgMsgs)
        textProgress.SetDropTarget(dt)

        txtSelManual = wx.StaticText(self, label="Or select file manually")
        GBSizer.Add(txtSelManual, pos=(6, 0), span=(1, 5),
            flag=wx.ALIGN_RIGHT|wx.TOP|wx.RIGHT|wx.BOTTOM, border=5)

        btnBrowse = wx.Button(self, label="Browse", size=(90, 28))
        btnBrowse.Bind(wx.EVT_BUTTON, lambda evt, str=btnBrowse.GetLabel(): self.onClick_BtnBrowse(evt, str))

        GBSizer.Add(btnBrowse, pos=(6, 5), flag=wx.RIGHT|wx.BOTTOM, border=5)
       
        GBSizer.AddGrowableCol(1)
        GBSizer.AddGrowableRow(2)

        self.SetSizerAndFit(GBSizer)

    def openfile(self, event):
        dlg = wx.FileDialog(self, "Choose a file", os.getcwd(), "", "*.*", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            mypath = os.path.basename(path)
            self.SetStatusText("Not implemented yet")
            #self.SetStatusText("You selected: %s" % mypath)
            dlg.Destroy()
    
    def onButton(self, event, strLabel):
        """"""
        print ' You clicked the button labeled "%s"' % strLabel

    def onClick_BtnShowLog(self, event, strLabel):
        """"""
        wx.MessageBox('"Show Log" is not implemented yet', 'Info', 
            wx.OK | wx.ICON_INFORMATION)

    def onClick_BtnBrowse(self, event, strLabel):
        """"""
        wx.MessageBox('"Browse" is not implemented yet', 'Info', 
            wx.OK | wx.ICON_INFORMATION)



class ParseFilesFrame(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title)
        self.InitUI()
        self.SetSize((450, 400))
#        self.Centre()
        self.Show(True)

    def InitUI(self):
        framePanel = ParseFilesPanel(self, wx.ID_ANY)

def main():
    app = wx.App(redirect=False)
    ParseFilesFrame(None, wx.ID_ANY, 'Add Data to Database')
    app.MainLoop() 

if __name__ == '__main__':
    main()
