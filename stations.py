import wx, sqlite3, datetime
import os, sys, re, cPickle
import scidb

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# DragList

class DragList(wx.ListCtrl):
    def __init__(self, *arg, **kw):
        wx.ListCtrl.__init__(self, *arg, **kw)

        self.Bind(wx.EVT_LIST_BEGIN_DRAG, self._startDrag)

        dt = ListDrop(self)
        self.SetDropTarget(dt)

    def getItemInfo(self, idx):
        """Collect all relevant data of a listitem, and put it in a list"""
        l = []
        l.append(idx) # We need the original index, so it is easier to eventualy delete it
        l.append(self.GetItemData(idx)) # Itemdata
        l.append(self.GetItemText(idx)) # Text first column
        for i in range(1, self.GetColumnCount()): # Possible extra columns
            l.append(self.GetItem(idx, i).GetText())
        return l

    def _startDrag(self, e):
        """ Put together a data object for drag-and-drop _from_ this list. """
        l = []
        idx = -1
        while True: # find all the selected items and put them in a list
            idx = self.GetNextItem(idx, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
            if idx == -1:
                break
            l.append(self.getItemInfo(idx))

        # Pickle the items list.
        itemdata = cPickle.dumps(l, 1)
        # create our own data format and use it in a
        # custom data object
        ldata = wx.CustomDataObject("ListCtrlItems")
        ldata.SetData(itemdata)
        # Now make a data object for the  item list.
        data = wx.DataObjectComposite()
        data.Add(ldata)

        # Create drop source and begin drag-and-drop.
        dropSource = wx.DropSource(self)
        dropSource.SetData(data)
        res = dropSource.DoDragDrop(flags=wx.Drag_DefaultMove)

        # If move, we want to remove the item from this list.
        if res == wx.DragMove:
            # It's possible we are dragging/dropping from this list to this list.  In which case, the
            # index we are removing may have changed...

            # Find correct position.
            l.reverse() # Delete all the items, starting with the last item
            for i in l:
                pos = self.FindItem(i[0], i[2])
                self.DeleteItem(pos)

    def _insert(self, x, y, seq):
        """ Insert text at given x, y coordinates --- used with drag-and-drop. """

        # Find insertion point.
        index, flags = self.HitTest((x, y))

        if index == wx.NOT_FOUND: # not clicked on an item
            if flags & (wx.LIST_HITTEST_NOWHERE|wx.LIST_HITTEST_ABOVE|wx.LIST_HITTEST_BELOW): # empty list or below last item
                index = self.GetItemCount() # append to end of list
            elif self.GetItemCount() > 0:
                if y <= self.GetItemRect(0).y: # clicked just above first item
                    index = 0 # append to top of list
                else:
                    index = self.GetItemCount() + 1 # append to end of list
        else: # clicked on an item
            # Get bounding rectangle for the item the user is dropping over.
            rect = self.GetItemRect(index)

            # If the user is dropping into the lower half of the rect, we want to insert _after_ this item.
            # Correct for the fact that there may be a heading involved
            if y > rect.y - self.GetItemRect(0).y + rect.height/2:
                index += 1

        for i in seq: # insert the item data
            idx = self.InsertStringItem(index, i[2])
            self.SetItemData(idx, i[1])
            for j in range(1, self.GetColumnCount()):
                try: # Target list can have more columns than source
                    self.SetStringItem(idx, j, i[2+j])
                except:
                    pass # ignore the extra columns
            index += 1

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ListDrop

class ListDrop(wx.PyDropTarget):
    """ Drop target for simple lists. """

    def __init__(self, source):
        """ Arguments:
         - source: source listctrl.
        """
        wx.PyDropTarget.__init__(self)

        self.dv = source

        # specify the type of data we will accept
        self.data = wx.CustomDataObject("ListCtrlItems")
        self.SetDataObject(self.data)

    # Called when OnDrop returns True.  We need to get the data and
    # do something with it.
    def OnData(self, x, y, d):
        # copy the data from the drag source to our data object
        if self.GetData():
            # convert it back to a list and give it to the viewer
            ldata = self.data.GetData()
            l = cPickle.loads(ldata)
            self.dv._insert(x, y, l)

        # what is returned signals the source what to do
        # with the original data (move, copy, etc.)  In this
        # case we just return the suggested value given to us.
        return d

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
#        print dctInfo
        for k in dctInfo:
            print k, dctInfo[k]
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
        self.msgArea.ChangeValue(str(infoDict['lineCt']) +
            " lines processed; " + str(dataRecsAdded) +
            " data records added to database, " + str(dataRecsDupSkipped) +
            " duplicates skipped.")
        
       
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
                lstLines.append((sLine,))
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



class SetupStationsPanel(wx.Panel):
    def __init__(self, parent, id):
        wx.Panel.__init__(self, parent, id)
        self.InitUI()

    def InitUI(self):

        GBSizer = wx.GridBagSizer(5, 5)

        hdr = wx.StaticText(self, label="Drag Stations and Series to assign them to Channel Segments")
        GBSizer.Add(hdr, pos=(0, 0), span=(1, 2), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)

#        btnShowLog = wx.Button(self, label="Show Log", size=(90, 28))
#        btnShowLog.Bind(wx.EVT_BUTTON, lambda evt, str=btnShowLog.GetLabel(): self.onClick_BtnShowLog(evt, str))
#        GBSizer.Add(btnShowLog, pos=(0, 5), flag=wx.RIGHT|wx.BOTTOM, border=5)

        hLine = wx.StaticLine(self)
        GBSizer.Add(hLine, pos=(1, 0), span=(1, 6), 
            flag=wx.EXPAND|wx.BOTTOM, border=1)

        hdrStation = wx.StaticText(self, label="Stations:")
        GBSizer.Add(hdrStation, pos=(2, 0), span=(1, 1), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        
        btnAddStation = wx.Button(self, label="Add", size=(70, 28))
#        btnAddStation.Bind(wx.EVT_BUTTON, lambda evt, str=btnAddStation.GetLabel(): self.onClick_BtnAddStation(evt, str))
        GBSizer.Add(btnAddStation, pos=(2, 1), flag=wx.RIGHT|wx.BOTTOM, border=5)
        
        lstStations = DragList(self, style=wx.LC_LIST)
        GBSizer.Add(lstStations, pos=(3, 0), span=(1, 2), flag=wx.TOP|wx.LEFT, border=5)

        hdrSeries = wx.StaticText(self, label="Series:")
        GBSizer.Add(hdrSeries, pos=(4, 0), span=(1, 1), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        
        btnAddSeries = wx.Button(self, label="Add", size=(70, 28))
#        btnAddSeries.Bind(wx.EVT_BUTTON, lambda evt, str=btnAddSeries.GetLabel(): self.onClick_BtnAddSeries(evt, str))
        GBSizer.Add(btnAddSeries, pos=(4, 1), flag=wx.RIGHT|wx.BOTTOM, border=5)
        
        lstSeries = DragList(self, style=wx.LC_LIST)
        GBSizer.Add(lstSeries, pos=(5, 0), span=(1, 2), flag=wx.TOP|wx.LEFT, border=5)

        hdrChanSegs = wx.StaticText(self, label="Channel Segments:")
        GBSizer.Add(hdrChanSegs, pos=(2, 2), span=(1, 1), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)

        lstChanSegs = DragList(self, style=wx.LC_REPORT)
        GBSizer.Add(lstChanSegs, pos=(3, 2), span=(1, 1), flag=wx.TOP|wx.LEFT, border=5)

       
#        GBSizer.AddGrowableCol(2)
#        GBSizer.AddGrowableRow(3)

#        textProgress = wx.TextCtrl(self, style = wx.TE_MULTILINE)
#        GBSizer.Add(textProgress, pos=(1, 0), span=(4, 6),
#            flag=wx.EXPAND|wx.TOP|wx.RIGHT|wx.BOTTOM, 
#            border=5)

#        lblProgTitle = wx.StaticText(self, wx.ID_ANY, "Progress:")
#        GBSizer.Add(lblProgTitle, pos=(5, 0), span=(1, 1),
#            flag=wx.EXPAND|wx.TOP|wx.RIGHT|wx.BOTTOM, 
#            border=5)

#        textProgMsgs = wx.TextCtrl(self, style = wx.TE_MULTILINE)
#        GBSizer.Add(textProgMsgs, pos=(5, 1), span=(1, 5),
#            flag=wx.EXPAND|wx.TOP|wx.RIGHT|wx.BOTTOM, 
#            border=5)
        
#        dt = DropTargetForFilesToParse(textProgress, textProgMsgs)
#        textProgress.SetDropTarget(dt)

#        txtSelManual = wx.StaticText(self, label="Or select file manually")
#        GBSizer.Add(txtSelManual, pos=(6, 0), span=(1, 5),
#            flag=wx.ALIGN_RIGHT|wx.TOP|wx.RIGHT|wx.BOTTOM, border=5)

#        btnBrowse = wx.Button(self, label="Browse", size=(90, 28))
#        btnBrowse.Bind(wx.EVT_BUTTON, lambda evt, str=btnBrowse.GetLabel(): self.onClick_BtnBrowse(evt, str))

#        GBSizer.Add(btnBrowse, pos=(6, 5), flag=wx.RIGHT|wx.BOTTOM, border=5)

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

class SetupStationsFrame(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title)
        self.InitUI()
        self.SetSize((750, 600))
#        self.Centre()
        self.Show(True)

    def InitUI(self):
        framePanel = SetupStationsPanel(self, wx.ID_ANY)

def main():
    app = wx.App(redirect=False)
    SetupStationsFrame(None, wx.ID_ANY, 'Assign Stations and Series')
    app.MainLoop() 

if __name__ == '__main__':
    main()
