import wx, sqlite3, datetime
import os, sys, re
import scidb

class DropTargetForFilesToParse(wx.FileDropTarget):
    def __init__(self, progressArea, msgArea):
        wx.FileDropTarget.__init__(self)
        self.progressArea = progressArea
        self.msgArea = msgArea

    def OnDropFiles(self, x, y, filenames):
        self.progressArea.SetInsertionPointEnd()
#        self.progressArea.WriteText("\n%d file(s) dropped at %d,%d:\n" %
#                              (len(filenames), x, y))
        self.progressArea.WriteText("\n%d file(s) dropped\n" % (len(filenames),))


        for name in filenames:
            self.progressArea.WriteText(name + '\n')
            fileresult = self.parseFileIntoDB(name)
#            self.progressArea.SetInsertionPointEnd()
#            self.progressArea.WriteText(fileresult + '\n')

    def parseFileIntoDB(self, filename):
        """
        given a string which is the full path to a file
        determines the file structure and parses the
        data into the proper tables

        for initial testing, simply parses any text file into
        the temp DB, the table "Text"
        """
        dctInfo = {}
        dctInfo['fullPath'] = filename
        
        self.getFileInfo(dctInfo)
        print dctInfo
        if not ('dataFormat' in dctInfo):
            self.progressArea.SetInsertionPointEnd()
            self.progressArea.WriteText('Could not determine data format' + '\n')
            return "Could not determine data format"

        self.progressArea.SetInsertionPointEnd()
        self.progressArea.WriteText('Data format detected as: "' +
                                    dctInfo['dataFormat'] + '"\n')
        if dctInfo['dataFormat'] == r"Hoboware text export":
            self.parseHoboWareTextFile(dctInfo)
        # add others as else if here
        else:
            self.progressArea.SetInsertionPointEnd()
            self.progressArea.WriteText('Parsing of this data format is not implemented yet\n')
            return "Done"                       

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

        self.putTextLinesIntoTmpTable(infoDict)
        #parse file, start with header line; 1st line in this file format
        scidb.curT.execute("SELECT * FROM tmpLines ORDER BY ID;")
        for rec in scidb.curT:
            if rec['ID'] == 1:
#                print rec['Line']
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
                    print dictChannels[ky][:]
                for ky in dictChannels.keys():
                    scidb.assureChannelIsInDB(dictChannels[ky])
                print 'After Channel function'
                for ky in dictChannels.keys():
                    print dictChannels[ky][:]
                
            else: # not the 1st (header) line, but a line of data
                lData = rec['Line'].split('\t')
                # ignore item zero, a line number, not used
                sTimeStamp = lData[1]
                for iCol in range(len(lData)):
                    if iCol > 1: # an item of data
                        tsAsTime = datetime.datetime.strptime(sTimeStamp, "%Y-%m-%d %H:%M:%S")
                        tsAsDate = tsAsTime.date()
                        scidb.curT.execute("insert into testDates(note, d, ts) values (?, ?, ?)", ("test insert", tsAsDate, tsAsTime))
                        print sTimeStamp, lData[iCol]
                        
                    
                
       
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
        numToInsertAtOnce = 3557 # arbitrary number, guessing to optimize
        lstLines = []
        with open(infoDict['fullPath'], 'r') as f:
            for sLine in f:
                ct += 1
                # much faster to insert a batch at once
                lstLines.append((sLine,))
                if  len(lstLines) >= numToInsertAtOnce:
                    self.msgArea.ChangeValue("counting lines in file: " +
                            str(ct))
                    # could also use curT instead of tmpConn; below uses implicit cursor
                    scidb.tmpConn.executemany(stSQL, lstLines)
                    lstLines = []
                scidb.tmpConn.commit()
                wx.Yield()
        # file should be closed by here, avoid possible corruption if left open
        # put last batch of lines into DB
        if  len(lstLines) > 0:
            scidb.tmpConn.executemany(stSQL, lstLines)
            lstLines = []
        # get count
        scidb.curT.execute("SELECT count(*) AS 'lineCt' FROM tmpLines;")
        t = scidb.curT.fetchone() # a tuple with one value
        infoDict['lineCt'] = t[0]
        self.msgArea.ChangeValue(str(infoDict['lineCt']) + " lines in file")


    def getFileInfo(self, infoDict):
        """
        Data files have so many possible parameters, use a dictionary to track them
        Only requirement on entering this function is the dictionary has a
        member 'fullPath', which is a string that is a full file path
        """
        if (os.path.isdir(infoDict['fullPath'])):
            infoDict['fileErr'] = "Path is a directory"
            infoDict['isDir'] = True
            return
        if not os.path.exists(infoDict['fullPath']):
            infoDict['fileErr'] = "File does not exist"
            return
        if not os.path.isfile(infoDict['fullPath']):
            infoDict['fileErr'] = "Not a file"
            return
        infoDict['fileSize'] = os.path.getsize(infoDict['fullPath'])
        # splitext gives a 2-tuple of what's before and after the ext delim
        infoDict['fileExtension'] = os.path.splitext(infoDict['fullPath'])[1]
        if infoDict['fileExtension'] == r'dtf':
            infoDict['dataFormat'] = "binary Onset DTF"
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
                iLineCt += 1
                # diagnostics
                if iLineCt == 1:
                    infoDict['firstLine'] = sLine
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
                        infoDict['versionNumber'] = 13
                        # in versions <=13, header is 1st non-blank line
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


#

class ParseFiles(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size = (450, 400))
        self.InitUI()
#        self.Centre()
        self.Show(True)

    def InitUI(self):

        framePanel = wx.Panel(self)
        GBSizer = wx.GridBagSizer(5, 5)

        hdr = wx.StaticText(framePanel, label="Drag files below to add their data to the database")
        GBSizer.Add(hdr, pos=(0, 0), span=(1, 2), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)

        btnShowLog = wx.Button(framePanel, label="Show Log", size=(90, 28))
        btnShowLog.Bind(wx.EVT_BUTTON, lambda evt, str=btnShowLog.GetLabel(): self.onClick_BtnShowLog(evt, str))
#        btnShowLog.Bind(wx.EVT_BUTTON, OnBtnShowLogClick)
        GBSizer.Add(btnShowLog, pos=(0, 5), flag=wx.RIGHT|wx.BOTTOM, border=5)

        textProgress = wx.TextCtrl(framePanel, style = wx.TE_MULTILINE)
        GBSizer.Add(textProgress, pos=(1, 0), span=(4, 6),
            flag=wx.EXPAND|wx.TOP|wx.RIGHT|wx.BOTTOM, 
            border=5)

        lblProgTitle = wx.StaticText(framePanel, -1, "Progress:")
        GBSizer.Add(lblProgTitle, pos=(5, 0), span=(1, 1),
            flag=wx.EXPAND|wx.TOP|wx.RIGHT|wx.BOTTOM, 
            border=5)

        textProgMsgs = wx.TextCtrl(framePanel, style = wx.TE_MULTILINE)
        GBSizer.Add(textProgMsgs, pos=(5, 1), span=(1, 5),
            flag=wx.EXPAND|wx.TOP|wx.RIGHT|wx.BOTTOM, 
            border=5)
        
        dt = DropTargetForFilesToParse(textProgress, textProgMsgs)
        textProgress.SetDropTarget(dt)

        txtSelManual = wx.StaticText(framePanel, label="Or select file manually")
        GBSizer.Add(txtSelManual, pos=(6, 0), span=(1, 5),
            flag=wx.ALIGN_RIGHT|wx.TOP|wx.RIGHT|wx.BOTTOM, border=5)

        btnBrowse = wx.Button(framePanel, label="Browse", size=(90, 28))
        btnBrowse.Bind(wx.EVT_BUTTON, lambda evt, str=btnBrowse.GetLabel(): self.onClick_BtnBrowse(evt, str))

        GBSizer.Add(btnBrowse, pos=(6, 5), flag=wx.RIGHT|wx.BOTTOM, border=5)
       
        GBSizer.AddGrowableCol(1)
        GBSizer.AddGrowableRow(2)

        framePanel.SetSizerAndFit(GBSizer)

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


app = wx.App()
ParseFiles(None, -1, 'Add Data to Database')
app.MainLoop()