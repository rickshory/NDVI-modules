import wx, sqlite3, datetime, copy, csv
import os, sys, re, cPickle, datetime
import scidb
import wx.lib.scrolledpanel as scrolled, wx.grid
import multiprocessing
try:
    import win32com.client
    hasCom = True
except ImportError:
    hasCom = False


ID_ADD_BOOK = 101
ID_ADD_SHEET = 201
ID_DEL_BOOK = 202
ID_MAKE_BOOK = 203
ID_ADD_COL = 301
ID_DEL_SHEET = 302
ID_MAKE_SHEET = 303
ID_DEL_COL = 402

treePopMenuItems = {ID_ADD_BOOK:'Add a Book',
    ID_ADD_SHEET:'Add a Sheet to this Book', ID_DEL_BOOK:'Delete this Book',
    ID_MAKE_BOOK:'Create this Book dataset',                
    ID_ADD_COL:'Add a Column to this Sheet', ID_DEL_SHEET:'Delete this Sheet',
    ID_MAKE_SHEET:'Create this Sheet dataset',                
    ID_DEL_COL:'Delete this Column'}

class Dialog_Book(wx.Dialog):
    def __init__(self, parent, id, title = "Add a new Book"):
        wx.Dialog.__init__(self, parent, id)
        self.InitUI()
        self.SetSize((350, 300))
        self.SetTitle("Add a new Book") # overrides title passed above

    def InitUI(self):
#        pnl = InfoPanel_Book(self, wx.ID_ANY)
        self.pnl = InfoPanel_Book(self)
   
    def OnClose(self, event):
        self.Destroy()

class Dialog_Sheet(wx.Dialog):
    def __init__(self, parent, id, title = "Add a new Sheet", parentTableRec = None):
        wx.Dialog.__init__(self, parent, id)
        self.InitUI(parentTableRec)
        self.SetSize((350, 300))
        self.SetTitle("Add a new sheet") # overrides title passed above

    def InitUI(self, parentTableRec):
#        pnl = InfoPanel_Sheet(self, wx.ID_ANY)
        self.pnl = InfoPanel_Sheet(self, parentTableRec)
   
    def OnClose(self, event):
        self.Destroy()

class Dialog_Column(wx.Dialog):
    def __init__(self, parent, id, title = "Add a new Column", parentTableRec = None):
        wx.Dialog.__init__(self, parent, id)
        self.InitUI(parentTableRec)
        self.SetSize((350, 300))
        self.SetTitle("Add a new column") # overrides title passed above

    def InitUI(self, parentTableRec):
#        pnl = InfoPanel_Column(self, wx.ID_ANY)
        self.pnl = InfoPanel_Column(self, parentTableRec)
   
    def OnClose(self, event):
        self.Destroy()        

class InfoPanel_DataSets(wx.Panel):
    def __init__(self, parent, id):
        wx.Panel.__init__(self, parent, id)
        self.InitUI()
        
    def InitUI(self):
        self.SetBackgroundColour(wx.WHITE) # this overrides color of enclosing panel
        dsPnlSiz = wx.GridBagSizer(1, 1)
        dsPnlSiz.Add(wx.StaticText(self, -1, 'Right-click the "DataSets" tree to the left to add a Book'),
                     pos=(0, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=10)
        dsPnlSiz.Add(wx.StaticText(self, -1, "Within a Book, you'll add one or more Sheets"),
                     pos=(1, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=10)
        dsPnlSiz.Add(wx.StaticText(self, -1, "Within a Sheet, you'll set up the Columns"),
                     pos=(2, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=10)
        dsPnlSiz.Add(wx.StaticText(self, -1, "When enough information is entered, a preview will appear below."),
                     pos=(3, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=10)
        dsPnlSiz.Add(wx.StaticText(self, -1, "You can go back and edit any level at any time"),
                     pos=(4, 0), flag=wx.LEFT|wx.BOTTOM, border=10)
        self.SetSizer(dsPnlSiz)

class InfoPanel_Book(scrolled.ScrolledPanel):
    def __init__(self, parent, treePyData = None):
        scrolled.ScrolledPanel.__init__(self, parent, -1)
#    def __init__(self, parent, id):
#        wx.Panel.__init__(self, parent, id)
        self.InitUI(treePyData)
        
    def InitUI(self, treePyData):
        if treePyData is None:
            self.sourceTable = '(none)'
            self.recID = 0
        else:
            self.sourceTable = treePyData[0]
            self.recID = treePyData[1]
        self.SetBackgroundColour(wx.WHITE) # this overrides color of enclosing panel
        bkPnlSiz = wx.GridBagSizer(1, 1)
        note1 = wx.StaticText(self, -1, 'Bold ')
        bolded = note1.GetFont() 
        bolded.SetWeight(wx.BOLD) 
        note1.SetFont(bolded)
        gRow = 0
        bkPnlSiz.Add(note1, pos=(gRow, 0), flag=wx.ALIGN_RIGHT|wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        bkPnlSiz.Add(wx.StaticText(self, -1, 'items are required'),
                     pos=(gRow, 1), flag=wx.TOP|wx.RIGHT|wx.BOTTOM, border=5)

        gRow += 1
        bkPnlSiz.Add(wx.StaticLine(self), pos=(gRow, 0), span=(1, 3), flag=wx.EXPAND)
        
        gRow += 1
        bookNameLabel = wx.StaticText(self, -1, 'Book Name')
        bookNameLabel.SetFont(bolded)
        bkPnlSiz.Add(bookNameLabel, pos=(gRow, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.tcBookName = wx.TextCtrl(self)
        bkPnlSiz.Add(self.tcBookName, pos=(gRow, 1), span=(1, 1), 
            flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)

        gRow += 1
        bkPnlSiz.Add(wx.StaticText(self, -1, 'Book Name must be unique'),
                     pos=(gRow, 0), span=(1, 2), flag=wx.LEFT|wx.BOTTOM, border=5)

        gRow += 1
        bkPnlSiz.Add(wx.StaticLine(self), pos=(gRow, 0), span=(1, 2), flag=wx.EXPAND)

        gRow += 1
        longitudeLabel = wx.StaticText(self, -1, 'Longitude')
        longitudeLabel.SetFont(bolded)
        bkPnlSiz.Add(longitudeLabel, pos=(gRow, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.tcLongitude = wx.TextCtrl(self)
        bkPnlSiz.Add(self.tcLongitude, pos=(gRow, 1), span=(1, 1), 
            flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)

        gRow += 1
        bkPnlSiz.Add(wx.StaticText(self, -1, '(for calculating solar time)'),
                     pos=(gRow, 0), span=(1, 2), flag=wx.LEFT|wx.BOTTOM, border=5)

        gRow += 1
        bkPnlSiz.Add(wx.StaticLine(self), pos=(gRow, 0), span=(1, 2), flag=wx.EXPAND)

        gRow += 1
        hrOffsetLabel = wx.StaticText(self, -1, 'Hour Offset')
        hrOffsetLabel.SetFont(bolded)
        bkPnlSiz.Add(hrOffsetLabel, pos=(gRow, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.tcHrOffset = wx.TextCtrl(self)
        bkPnlSiz.Add(self.tcHrOffset, pos=(gRow, 1), span=(1, 1), 
            flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)

        gRow += 1
        bkPnlSiz.Add(wx.StaticText(self, -1, '(for calculating clock time)'),
                     pos=(gRow, 0), span=(1, 2), flag=wx.LEFT|wx.BOTTOM, border=5)

        gRow += 1
        bkPnlSiz.Add(wx.StaticLine(self), pos=(gRow, 0), span=(1, 2), flag=wx.EXPAND)

        gRow += 1
        timeSlicesLabel = wx.StaticText(self, -1, 'Time slices per day')
        timeSlicesLabel.SetFont(bolded)
        bkPnlSiz.Add(timeSlicesLabel, pos=(gRow, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.tcTimeSlices = wx.TextCtrl(self)
        bkPnlSiz.Add(self.tcTimeSlices, pos=(gRow, 1), span=(1, 1), 
            flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)

        gRow += 1
        bkPnlSiz.Add(wx.StaticText(self, -1, '(e.g. 1 for daily data, 24 for hourly data)'),
                     pos=(gRow, 0), span=(1, 2), flag=wx.LEFT|wx.BOTTOM, border=5)

        gRow += 1
        bkPnlSiz.Add(wx.StaticLine(self), pos=(gRow, 0), span=(1, 2), flag=wx.EXPAND)
        
        gRow += 1
        lstDates = scidb.getDatesList()
        bkPnlSiz.Add(wx.StaticText(self, -1, 'From'),
                     pos=(gRow, 0), span=(1, 1), flag=wx.ALIGN_RIGHT)
        self.cbxDateFrom = wx.ComboBox(self, -1, choices=lstDates, style=wx.CB_READONLY)
        bkPnlSiz.Add(self.cbxDateFrom, pos=(gRow, 1), span=(1, 1), flag=wx.LEFT, border=5)

        gRow += 1
        bkPnlSiz.Add(wx.StaticText(self, -1, 'To'),
                     pos=(gRow, 0), span=(1, 1), flag=wx.ALIGN_RIGHT)
        self.cbxDateTo = wx.ComboBox(self, -1, choices=lstDates, style=wx.CB_READONLY)
        bkPnlSiz.Add(self.cbxDateTo, pos=(gRow, 1), span=(1, 1), flag=wx.LEFT, border=5)

        gRow += 1
        bkPnlSiz.Add(wx.StaticText(self, -1, 'Optional, to limit date range'),
                     pos=(gRow, 0), span=(1, 2), flag=wx.LEFT|wx.BOTTOM, border=5)

        gRow += 1
        bkPnlSiz.Add(wx.StaticLine(self), pos=(gRow, 0), span=(1, 2), flag=wx.EXPAND)

        gRow += 1
        self.ckSheetsTogether = wx.CheckBox(self, label="Put all sheets' data together into one table")
        bkPnlSiz.Add(self.ckSheetsTogether, pos=(gRow, 0), span=(1, 2), flag=wx.LEFT|wx.BOTTOM, border=5)

        gRow += 1
        self.ckSpaceBetwBlocks = wx.CheckBox(self, label="Blank row between these data blocks")
        bkPnlSiz.Add(self.ckSpaceBetwBlocks, pos=(gRow, 0), span=(1, 2), flag=wx.LEFT|wx.BOTTOM, border=5)

        gRow += 1
        bkPnlSiz.Add(wx.StaticLine(self), pos=(gRow, 0), span=(1, 2), flag=wx.EXPAND)

        gRow += 1
        self.btnSave = wx.Button(self, label="Save", size=(90, 28))
        self.btnSave.Bind(wx.EVT_BUTTON, lambda evt: self.onClick_BtnSave(evt))
        bkPnlSiz.Add(self.btnSave, pos=(gRow, 0), flag=wx.LEFT|wx.BOTTOM, border=5)
        self.btnCancel = wx.Button(self, label="Cancel", size=(90, 28))
        self.btnCancel.Bind(wx.EVT_BUTTON, lambda evt: self.onClick_BtnCancel(evt))
        bkPnlSiz.Add(self.btnCancel, pos=(gRow, 1), flag=wx.LEFT|wx.BOTTOM, border=5)

#        parObjClass = self.GetParent().GetClassName()
#        print "Parent object class:", parObjClass
#        if parObjClass == 'wxDialog':
#            print "in the Dialog, don't try to set up values"
#        else:
        if self.recID:
            print "Source Table:", self.sourceTable, ", Record ID:", self.recID
            self.fillBookPanelControls()
        else:
            print "no recID in Book panel, will not initialize values"
        self.SetSizer(bkPnlSiz)
        self.SetAutoLayout(1)
        self.SetupScrolling()

    def fillBookPanelControls(self):
#        stSQL = """
#        SELECT BookName, Longitude, HourOffset,
#        OutputDataStart, OutputDataEnd, NumberOfTimeSlicesPerDay,
#        PutAllOutputRowsInOneSheet, BlankRowBetweenDataBlocks
#        FROM OutputBooks WHERE ID = ?
#        """
        stSQL = "SELECT * FROM OutputBooks WHERE ID=?"
        scidb.curD.execute(stSQL, (self.recID,))
        rec = scidb.curD.fetchone()
        self.tcBookName.SetValue(rec['BookName'])
        self.tcLongitude.SetValue('%f' % rec['Longitude'])
        self.tcHrOffset.SetValue('%d' % rec['HourOffset'])
        self.tcTimeSlices.SetValue('%d' % rec['NumberOfTimeSlicesPerDay'])
        if rec['OutputDataStart'] != None:
            self.cbxDateFrom.SetValue('%s' % rec['OutputDataStart'])
        else:
            self.cbxDateFrom.SetValue('')
        if rec['OutputDataEnd'] != None:
            self.cbxDateTo.SetValue('%s' % rec['OutputDataEnd'])
        else:
            self.cbxDateTo.SetValue('')
        if rec['PutAllOutputRowsInOneSheet'] == 1:
            self.ckSheetsTogether.SetValue(1)
        else:
            self.ckSheetsTogether.SetValue(0)
        if rec['BlankRowBetweenDataBlocks'] == 1:
            self.ckSpaceBetwBlocks.SetValue(1)
        else:
            self.ckSpaceBetwBlocks.SetValue(0)

    def onClick_BtnSave(self, event):
        """
        If this frame is shown in a Dialog, the Book is being created.
        Attempt to create a new record and make the new record ID available.
        If this frame is shown in the main form, attempt to save any changes to the existing DB record
        """
        parObject = self.GetParent()
        parClassName = parObject.GetClassName() # "wxDialog" if in the dialog

        # clean up whitespace; remove leading/trailing & multiples
        stBookName = " ".join(self.tcBookName.GetValue().split())
        print "stBookName:", stBookName
        if stBookName == '':
            wx.MessageBox('Need Book Name', 'Missing',
                wx.OK | wx.ICON_INFORMATION)
            self.tcBookName.SetValue(stBookName)
            self.tcBookName.SetFocus()
            self.Scroll(0, 0) # the required controls are all at the top
            return
        if parClassName == "wxDialog":
            if scidb.countTableFieldItems('OutputBooks', 'BookName', stBookName) > 0:
                wx.MessageBox('There is already a Book Name "' + stBookName + '"', 'Duplicate',
                    wx.OK | wx.ICON_INFORMATION)
                self.tcBookName.SetValue('')
                self.tcBookName.SetFocus()
                self.Scroll(0, 0) # the required controls are all at the top
                return
        else:
            # test that some record other than the current one does not have the same name we're trying to rename this one to
            stSQL = "SELECT COUNT(*) AS CtDups FROM OutputBooks WHERE BookName = ? AND ID != ?;"
            scidb.curD.execute(stSQL, (stBookName, self.recID))
            rec = scidb.curD.fetchone() # will only be one record
            if rec['CtDups'] > 0: # there is a conflict
                wx.MessageBox('There is another Book named "' + stBookName + '". Use a different name.', 'Duplicate',
                    wx.OK | wx.ICON_INFORMATION)
                self.tcBookName.SetValue(stBookName)
                self.tcBookName.SetFocus()
                self.Scroll(0, 0) # the required controls are all at the top
                return

        maxLen = scidb.lenOfVarcharTableField('OutputBooks', 'BookName')
        if maxLen < 1:
            wx.MessageBox('Error %d getting [OutputBooks].[BookName] field length.' % maxLen, 'Error',
                wx.OK | wx.ICON_INFORMATION)
            return
        if len(stBookName) > maxLen:
            wx.MessageBox('Max length for Book Name is %d characters.\n\nIf trimmed version is acceptable, retry.' % maxLen, 'Invalid',
                wx.OK | wx.ICON_INFORMATION)
            self.tcBookName.SetValue(stBookName[:(maxLen)])
            self.tcBookName.SetFocus()
            self.Scroll(0, 0) # the required controls are all at the top
            return
        try:
            fpLongitude = float(self.tcLongitude.GetValue())
        except:
            wx.MessageBox('Missing or invalid Longitude.', 'Invalid',
                wx.OK | wx.ICON_INFORMATION)
            self.tcLongitude.SetValue('')
            self.tcLongitude.SetFocus()
            self.Scroll(0, 0) # the required controls are all at the top
            return
        if fpLongitude < -180 or fpLongitude > 180:
            wx.MessageBox('Longitude is outside the valid range +-180 degrees', 'Invalid',
                wx.OK | wx.ICON_INFORMATION)
            self.tcLongitude.SetValue('')
            self.tcLongitude.SetFocus()
            self.Scroll(0, 0) # the required controls are all at the top
            return
        print "Longitude:", fpLongitude
        try:
            iHrOffset = int(self.tcHrOffset.GetValue())
        except:
            wx.MessageBox('Missing or invalid Hour Offset.', 'Invalid',
                wx.OK | wx.ICON_INFORMATION)
            self.tcHrOffset.SetValue('')
            self.tcHrOffset.SetFocus()
            self.Scroll(0, 0) # the required controls are all at the top
            return
        if iHrOffset < -12 or iHrOffset > 12:
            wx.MessageBox('Hour Offset is outside the valid range +-12 hours', 'Invalid',
                wx.OK | wx.ICON_INFORMATION)
            self.tcHrOffset.SetValue('')
            self.tcHrOffset.SetFocus()
            self.Scroll(0, 0) # the required controls are all at the top
            return
        print "HourOffset:", iHrOffset
        try:
            iTimeSlices = int(self.tcTimeSlices.GetValue())
        except:
            wx.MessageBox('Missing or invalid Time Slices number.', 'Invalid',
                wx.OK | wx.ICON_INFORMATION)
            self.tcTimeSlices.SetValue('')
            self.tcTimeSlices.SetFocus()
            self.Scroll(0, 0) # the required controls are all at the top
            return
        if iTimeSlices < 1:
            wx.MessageBox('Time Slices per Day must be 1 or greater', 'Invalid',
                wx.OK | wx.ICON_INFORMATION)
            self.tcTimeSlices.SetValue('')
            self.tcTimeSlices.SetFocus()
            self.Scroll(0, 0) # the required controls are all at the top
            return
        print "TimeSlicesPerDay:", iTimeSlices
        dtFrom = self.cbxDateFrom.GetValue()
        if dtFrom == '':
            dtFrom = None
        dtTo = self.cbxDateTo.GetValue()
        if dtTo == '':
            dtTo = None
        if dtFrom != None and dtTo != None and dtFrom > dtTo:
            wx.MessageBox('Date "From" must be before date "To"', 'Invalid',
                wx.OK | wx.ICON_INFORMATION)
#            self.cbxDateFrom.SetValue('')
            self.cbxDateFrom.SetFocus()
            self.Scroll(0, 0) # the required controls are all at the top
            return   
        print "OutputDataStart:", dtFrom
        print "OutputDataEnd:", dtTo
        if self.ckSheetsTogether.GetValue():
            bOneBlock = 1
        else:
            bOneBlock = 0
        print "PutAllOutputRowsInOneSheet:", bOneBlock
        if self.ckSpaceBetwBlocks.GetValue():
            bSpBetw = 1
        else:
            bSpBetw = 0
        print "BlankRowBetweenDataBlocks:", bSpBetw
        
#        wx.MessageBox('OK so far, but "Save" is not implemented yet', 'Info', 
#            wx.OK | wx.ICON_INFORMATION)
#        return
        if parClassName == "wxDialog": # in the Dialog, create a new DB record
            stSQL = """
                INSERT INTO OutputBooks
                (BookName, Longitude, HourOffset,
                NumberOfTimeSlicesPerDay,
                OutputDataStart, OutputDataEnd, 
                PutAllOutputRowsInOneSheet, BlankRowBetweenDataBlocks)
                VALUES (?,?,?,?,?,?,?,?);
                """
            try:
                scidb.curD.execute(stSQL, (stBookName, fpLongitude, iHrOffset,
                        iTimeSlices, dtFrom, dtTo, bOneBlock, bSpBetw))
                scidb.datConn.commit()
                # get record ID of new record
                self.newRecID = scidb.curD.lastrowid
                self.addRecOK = 1

            except sqlite3.IntegrityError: # duplicate name or required field missing
                print "could not add Book record to DB table"
                wx.MessageBox('Error creating book', 'Error', 
                    wx.OK | wx.ICON_INFORMATION)
                self.newRecID = 0
                self.addRecOK = 0
            # let calling routine destroy, after getting any needed parameters
            parObject.EndModal(self.addRecOK)
 #            parObject.Destroy()
        else: # in the frame, update the existing record
            self.newRecID = 0 # this will not be a new record
            stSQL = """
                UPDATE OutputBooks SET  
                BookName = ?, Longitude = ?, HourOffset = ?,
                NumberOfTimeSlicesPerDay = ?,
                OutputDataStart = ?, OutputDataEnd = ?, 
                PutAllOutputRowsInOneSheet = ?, BlankRowBetweenDataBlocks = ?
                WHERE ID = ?;
            """
            try:
                scidb.curD.execute(stSQL, ( stBookName, fpLongitude, iHrOffset,
                        iTimeSlices, dtFrom, dtTo, bOneBlock, bSpBetw, self.recID ))
                scidb.datConn.commit()
                self.updateRecOK = 1
                # update the label on the tree branch
                parObject1 = self.GetParent() # the details panel
#                print "Parent 1:", parObject1, ", Class", parObject1.GetClassName()
                parObject2 = parObject1.GetParent() # the vertical splitter window
#                print "Parent 2:", parObject2, ", Class", parObject2.GetClassName()
                parObject3 = parObject2.GetParent() # panel
#                print "Parent 3:", parObject3, ", Class", parObject3.GetClassName()
                parObject4 = parObject3.GetParent() # the horizontal splitter window
#                print "Parent 4:", parObject4, ", Class", parObject4.GetClassName()
                parObject5 = parObject4.GetParent() # the main panel that owns the tree
#                print "Parent 5:", parObject5, ", Class", parObject5.GetClassName()
#                print "Parent 5 book branch ID?:", parObject5.bookBranchID
#                parObject5.dsTree.SetItemText(parObject5.bookBranchID, stBookName)
                parObject5.dsTree.SetItemText(parObject5.dsInfoPnl.correspondingTreeItem, stBookName)
                wx.MessageBox('Changes saved', 'Updated',
                    wx.OK | wx.ICON_INFORMATION)
            except:
                print "could not update Book record to DB table"
                wx.MessageBox('Error updating book', 'Error', 
                    wx.OK | wx.ICON_INFORMATION)
                self.updateRecOK = 0
        return
        

    def onClick_BtnCancel(self, event):
        """
        If this frame is shown in a Dialog, the Book is being created. Exit with no changes.
        If this frame is shown in the main form, restore it from the saved DB record
        """
        self.newRecID = 0 # new record does not apply
        parObject = self.GetParent()
        if parObject.GetClassName() == "wxDialog":
            parObject.EndModal(0) # if in the creation dialog, exit with no changes to the DB
#            parObject.Destroy() 
        else: # in the main form
            wx.MessageBox('Undoing any edits', 'Undo', 
                wx.OK | wx.ICON_INFORMATION)
            self.fillBookPanelControls()
        return

class InfoPanel_Sheet(scrolled.ScrolledPanel):
    def __init__(self, parent, treePyData):
        scrolled.ScrolledPanel.__init__(self, parent, -1)
#    def __init__(self, parent, id):
#        wx.Panel.__init__(self, parent, id)
        self.InitUI(treePyData)
        
    def InitUI(self, treePyData):
        self.parentClassName = self.GetParent().GetClassName()
        print "Initializing Sheet frame; self.parentClass:", self.parentClassName
        if self.parentClassName == 'wxDialog':
            # we are in the dialog we use to create a new Sheet record
            # right-clicked tree item was the node we will create a new branch onto
            self.parentTable = treePyData[0] # the parent table, should be 'OutputBooks'
            self.parentRecID = treePyData[1] # the record ID in that table
            # provides foreign key for completing a new record in the current table
            self.sourceTable = 'OutputSheets'
            self.recID = 0 # no record yet
            # set up new record
            self.ShDict = dict(ID = None, BookID = self.parentRecID,
                WorksheetName = None, DataSetNickname = None,
                ListingOrder = None)
            # set up some guesses to help the user
            # if this will be the 1st Sheet in this Book
            stSQL = "SELECT MAX(CAST(ListingOrder AS INTEGER)) AS MaxLstOrd " \
                "FROM OutputSheets WHERE BookID = ?;"
            scidb.curD.execute(stSQL, (self.parentRecID,))
            rec = scidb.curD.fetchone()
            if rec['MaxLstOrd'] == None: # no other Sheets yet, offer defaults
                self.ShDict['ListingOrder'] = 1
            else: # already some Sheets
                self.ShDict['ListingOrder'] = rec['MaxLstOrd'] + 1
            self.ShDict['WorksheetName'] = 'Sheet' + str(self.ShDict['ListingOrder'])
            self.ShDict['DataSetNickname'] = self.ShDict['WorksheetName']
            
        else: # in the details panel to view/edit the information for an existing record
            # selected tree item is the node to view/edit
            self.sourceTable = treePyData[0] # should be 'OutputSheets'
            self.recID = treePyData[1] # the record ID in that table
            self.parentTable = 'OutputBooks' # the parent table
            stSQL = "SELECT BookID FROM OutputSheets WHERE ID = ?;"
            scidb.curD.execute(stSQL, (self.recID,))
            rec = scidb.curD.fetchone()
            self.parentRecID = rec['BookID'] # the foreign key ID in the parent table
            # get existing record
            stSQL = "SELECT * FROM OutputSheets WHERE ID = ?;"
            scidb.curD.execute(stSQL, (self.recID,))
            rec = scidb.curD.fetchone()
#            ShDict = copy.copy(rec) # this crashes
            self.ShDict = {}
            for recName in rec.keys():
                self.ShDict[recName] = rec[recName]

        print "Initializing InfoPanel_Sheet ->>>>"
        print "treePyData:", treePyData
        print "self.sourceTable:", self.sourceTable
        print "self.recID:", self.recID
        print "self.parentTable:", self.parentTable
        print "self.parentRecID:", self.parentRecID
        self.SetBackgroundColour(wx.WHITE) # this overrides color of enclosing panel
        shPnlSiz = wx.GridBagSizer(1, 1)
        note1 = wx.StaticText(self, -1, 'Bold ')
        bolded = note1.GetFont() 
        bolded.SetWeight(wx.BOLD) 
        note1.SetFont(bolded)
        gRow = 0
        shPnlSiz.Add(note1, pos=(gRow, 0), flag=wx.ALIGN_RIGHT|wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        shPnlSiz.Add(wx.StaticText(self, -1, 'items are required'),
                     pos=(gRow, 1), flag=wx.TOP|wx.RIGHT|wx.BOTTOM, border=5)

        gRow += 1
        shPnlSiz.Add(wx.StaticLine(self), pos=(gRow, 0), span=(1, 3), flag=wx.EXPAND)
        
        gRow += 1
        sheetNameLabel = wx.StaticText(self, -1, 'Sheet Name')
        sheetNameLabel.SetFont(bolded)
        shPnlSiz.Add(sheetNameLabel, pos=(gRow, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.tcSheetName = wx.TextCtrl(self)
        self.tcSheetName.SetValue(self.ShDict['WorksheetName'])

        shPnlSiz.Add(self.tcSheetName, pos=(gRow, 1), span=(1, 1), 
            flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)

        gRow += 1
        shPnlSiz.Add(wx.StaticText(self, -1, 'Will be the Worksheet name if output as Excel'),
                     pos=(gRow, 0), span=(1, 2), flag=wx.LEFT|wx.BOTTOM, border=5)

        gRow += 1
        shPnlSiz.Add(wx.StaticLine(self), pos=(gRow, 0), span=(1, 2), flag=wx.EXPAND)

        gRow += 1
        shPnlSiz.Add(wx.StaticText(self, -1, 'Dataset nickname'),
                     pos=(gRow, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.tcNickname = wx.TextCtrl(self)
        self.tcNickname.SetValue(self.ShDict['DataSetNickname'])
        shPnlSiz.Add(self.tcNickname, pos=(gRow, 1), span=(1, 2), 
            flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)

        gRow += 1
        shPnlSiz.Add(wx.StaticText(self, -1, 'Longer descriptive name, optional'),
                     pos=(gRow, 0), span=(1, 2), flag=wx.LEFT|wx.BOTTOM, border=5)

        gRow += 1
        shPnlSiz.Add(wx.StaticLine(self), pos=(gRow, 0), span=(1, 2), flag=wx.EXPAND)

        gRow += 1
        shPnlSiz.Add(wx.StaticText(self, -1, 'Listing order'),
                     pos=(gRow, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.tcListingOrder = wx.TextCtrl(self)
        self.tcListingOrder.SetValue('%d' % self.ShDict['ListingOrder'])
        shPnlSiz.Add(self.tcListingOrder, pos=(gRow, 1), span=(1, 1), 
            flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)

        gRow += 1
        shPnlSiz.Add(wx.StaticText(self, -1, 'Use this to specify the order of Worksheets \nin a workbook (if in Excel). Will be \nauto-assigned if you leave it out.'),
                     pos=(gRow, 0), span=(1, 2), flag=wx.LEFT|wx.BOTTOM, border=5)

        gRow += 1
        shPnlSiz.Add(wx.StaticLine(self), pos=(gRow, 0), span=(1, 2), flag=wx.EXPAND)

        gRow += 1
        self.btnSave = wx.Button(self, label="Save", size=(90, 28))
        self.btnSave.Bind(wx.EVT_BUTTON, lambda evt: self.onClick_BtnSave(evt))
        shPnlSiz.Add(self.btnSave, pos=(gRow, 0), flag=wx.LEFT|wx.BOTTOM, border=5)
        self.btnCancel = wx.Button(self, label="Cancel", size=(90, 28))
        self.btnCancel.Bind(wx.EVT_BUTTON, lambda evt: self.onClick_BtnCancel(evt))
        shPnlSiz.Add(self.btnCancel, pos=(gRow, 1), flag=wx.LEFT|wx.BOTTOM, border=5)

        self.SetSizer(shPnlSiz)
        self.SetAutoLayout(1)
        self.SetupScrolling()

    def onClick_BtnSave(self, event):
        """
        If this frame is shown in a Dialog, the Sheet is being created.
        Attempt to create a new record and make the new record ID available.
        If this frame is shown in the main form, attempt to save any changes to the existing DB record
        """
        
        # clean up whitespace; remove leading/trailing & multiples
        stSheetName = " ".join(self.tcSheetName.GetValue().split())
        print "stSheetName:", stSheetName
        if stSheetName == '':
            wx.MessageBox('Need Sheet Name', 'Missing',
                wx.OK | wx.ICON_INFORMATION)
            self.tcSheetName.SetValue(stSheetName)
            self.tcSheetName.SetFocus()
            self.Scroll(0, 0) # the required controls are all at the top
            return
    
        maxLen = scidb.lenOfVarcharTableField('OutputSheets', 'WorksheetName')
        if maxLen < 1:
            wx.MessageBox('Error %d getting [OutputSheets].[WorksheetName] field length.' % maxLen, 'Error',
                wx.OK | wx.ICON_INFORMATION)
            return
        if len(stSheetName) > maxLen:
            wx.MessageBox('Max length for Sheet Name is %d characters.\n\nIf trimmed version is acceptable, retry.' % maxLen, 'Invalid',
                wx.OK | wx.ICON_INFORMATION)
            self.tcSheetName.SetValue(stSheetName[:(maxLen)])
            self.tcSheetName.SetFocus()
            self.Scroll(0, 0) # the required controls are all at the top
            return
        
        stNickname = " ".join(self.tcNickname.GetValue().split())
        maxLen = scidb.lenOfVarcharTableField('OutputSheets', 'DataSetNickname')
        if maxLen < 1:
            wx.MessageBox('Error %d getting [OutputSheets].[DataSetNickname] field length.' % maxLen, 'Error',
                wx.OK | wx.ICON_INFORMATION)
            return
        if len(stNickname) > maxLen:
            wx.MessageBox('Max length for Sheet Nickname is %d characters.\n\nIf trimmed version is acceptable, retry.' % maxLen, 'Invalid',
                wx.OK | wx.ICON_INFORMATION)
            self.tcNickname.SetValue(stNickname[:(maxLen)])
            self.tcNickname.SetFocus()
            self.Scroll(0, 0) # the required controls are all at the top
            return

        try:
            iLstOrd = int(self.tcListingOrder.GetValue())
        except:
            # autocreate, 1 higher than previously existing
            print "self.parentRecID, to use in ListingOrder query:",  self.parentRecID
            stSQL = "SELECT MAX(CAST(OutputSheets.ListingOrder AS INTEGER)) AS MaxLstOrd " \
                "FROM OutputSheets WHERE BookID = ?;"
            scidb.curD.execute(stSQL, (self.parentRecID,))
            rec = scidb.curD.fetchone()
            print "Max Listing order fetched:", rec
            if rec['MaxLstOrd'] == None: # none yet
                iLstOrd = 1
            else:
                iLstOrd = rec['MaxLstOrd'] + 1
            wx.MessageBox('Listing Order auto-set to %d.' % iLstOrd, 'Info',
                wx.OK | wx.ICON_INFORMATION)
        print "Listing Order:", iLstOrd
        
#        wx.MessageBox('OK so far, but "Save" is not implemented yet', 'Info', 
#            wx.OK | wx.ICON_INFORMATION)
#        return

        # we have self.parentClassName from initialization; "wxDialog" if in the dialog
        if self.parentClassName == "wxDialog": # in the Dialog, create a new DB record
            stSQL = """
                INSERT INTO OutputSheets
                (BookID, WorksheetName, DataSetNickname, ListingOrder)
                VALUES (?,?,?,?);
                """
            try:
                scidb.curD.execute(stSQL, (self.parentRecID, 
                        stSheetName, stNickname, iLstOrd))
                scidb.datConn.commit()
                # get record ID of new record
                self.newRecID = scidb.curD.lastrowid
                self.addRecOK = 1

            except sqlite3.IntegrityError: # duplicate name or required field missing
                print "could not add Sheet record to DB table"
                wx.MessageBox('Error creating sheet', 'Error', 
                    wx.OK | wx.ICON_INFORMATION)
                self.newRecID = 0
                self.addRecOK = 0
            # let calling routine destroy, after getting any needed parameters
            parObject = self.GetParent() # the dialog
            parObject.EndModal(self.addRecOK) #exit the dialog
 #            parObject.Destroy()
        else: # self.parentClassNameis not "wxDialog"; we're in the frame, update the existing record
            self.newRecID = 0 # this will not be a new record
            stSQL = """
                UPDATE OutputSheets SET  
                WorksheetName = ?, DataSetNickname = ?, ListingOrder = ?
                WHERE ID = ?;
            """
            try:
                scidb.curD.execute(stSQL, (stSheetName, stNickname, iLstOrd, self.recID))
                scidb.datConn.commit()
                self.updateRecOK = 1
                # update the label on the tree branch
                parObject1 = self.GetParent() # the details panel
#                print "Parent 1:", parObject1, ", Class", parObject1.GetClassName()
                parObject2 = parObject1.GetParent() # the vertical splitter window
#                print "Parent 2:", parObject2, ", Class", parObject2.GetClassName()
                parObject3 = parObject2.GetParent() # panel
#                print "Parent 3:", parObject3, ", Class", parObject3.GetClassName()
                parObject4 = parObject3.GetParent() # the horizontal splitter window
#                print "Parent 4:", parObject4, ", Class", parObject4.GetClassName()
                parObject5 = parObject4.GetParent() # the main panel that owns the tree
#                print "Parent 5:", parObject5, ", Class", parObject5.GetClassName()
#                print "Parent 5 book branch ID?:", parObject5.bookBranchID
#                parObject5.dsTree.SetItemText(parObject5.sheetBranchID, stSheetName)
                parObject5.dsTree.SetItemText(parObject5.dsInfoPnl.correspondingTreeItem, stSheetName)
                wx.MessageBox('Changes saved', 'Updated',
                    wx.OK | wx.ICON_INFORMATION)
            except:
                print "could not update Sheet record to DB table"
                wx.MessageBox('Error updating sheet', 'Error', 
                    wx.OK | wx.ICON_INFORMATION)
                self.updateRecOK = 0
        return
        

    def onClick_BtnCancel(self, event):
        """
        If this frame is shown in a Dialog, the Sheet is being created. Exit with no changes.
        If this frame is shown in the main form, restore it from the saved DB record
        """
        self.newRecID = 0 # new record does not apply
        parObject = self.GetParent()
        if parObject.GetClassName() == "wxDialog":
            parObject.EndModal(0) # if in the creation dialog, exit with no changes to the DB
#            parObject.Destroy() 
        else: # in the main form
            wx.MessageBox('Ignoring any edits', 'Undo', 
                wx.OK | wx.ICON_INFORMATION)
        return

class InfoPanel_Column(scrolled.ScrolledPanel):
    def __init__(self, parent, treePyData):
        scrolled.ScrolledPanel.__init__(self, parent, -1)
#    def __init__(self, parent, id):
#        wx.Panel.__init__(self, parent, id)
        self.InitUI(treePyData)
            
    def InitUI(self, treePyData):
        self.parentClassName = self.GetParent().GetClassName()
        print "Initializing Column frame; self.parentClass:", self.parentClassName
        if self.parentClassName == 'wxDialog':
            # we are in the dialog we use to create a new Column record
            # right-clicked tree item was the node we will create a new branch onto
            self.parentTable = treePyData[0] # the parent table, should be 'OutputSheets'
            self.parentRecID = treePyData[1] # the record ID in that table
            # provides foreign key for completing a new record in the current table
            self.sourceTable = 'OutputColunns' # this table
            self.recID = 0 # no record yet
            # set up new record
            self.ColDict = dict(ID = None, WorksheetID = self.parentRecID,
                ColumnHeading = None, ColType = None,
                TimeSystem = None, TimeIsInterval = 0, IntervalIsFrom = None,
                Constant = None, Formula = None,
                AggType = None, AggStationID = None, AggDataSeriesID = None,
                Format_Python = None, Format_Excel = None, ListingOrder = None)
            # set up some guesses to help the user
            # if this will be the 1st column in this sheet, offer a Timestamp
            stSQL = "SELECT MAX(CAST(OutputColumns.ListingOrder AS INTEGER)) AS MaxLstOrd " \
                "FROM OutputColumns WHERE WorksheetID = ?;"
            scidb.curD.execute(stSQL, (self.parentRecID,))
            rec = scidb.curD.fetchone()
            if rec['MaxLstOrd'] == None: # no other columns yet, offer a Timestamp
                self.ColDict['ColumnHeading'] = 'Timestamp'
                self.ColDict['ColType'] = 'Timestamp'
                self.ColDict['TimeSystem'] = 'Clock Time'
                self.ColDict['Format_Python'] = '%Y-%m-%d %H:%M:%S'
                self.ColDict['Format_Excel'] = 'yyyy-mm-dd hh:mm:ss'
                self.ColDict['ListingOrder'] = 1
            else: # already some columns, offer an Aggregate
                self.ColDict['ColType'] = 'Aggregate'
                self.ColDict['AggType'] = 'Avg'
                self.ColDict['Format_Python'] = '%.2f'
                self.ColDict['Format_Excel'] = '0.00'
                self.ColDict['ListingOrder'] = rec['MaxLstOrd'] + 1
                
        else: # in the details panel to view/edit the information for an existing record
            # selected tree item is the node to view/edit
            self.sourceTable = treePyData[0] # should be 'OutputColumns'
            self.recID = treePyData[1] # the record ID in that table
            self.parentTable = 'OutputSheets' # the parent table
            stSQL = "SELECT WorksheetID FROM OutputColumns WHERE ID = ?;"
            scidb.curD.execute(stSQL, (self.recID,))
            rec = scidb.curD.fetchone()
            self.parentRecID = rec['WorksheetID'] # the foreign key ID in the parent table
            # get existing record
            stSQL = "SELECT * FROM OutputColumns WHERE ID = ?;"
            scidb.curD.execute(stSQL, (self.recID,))
            rec = scidb.curD.fetchone()
#            ColDict = copy.copy(rec) # this crashes
            self.ColDict = {}
            for recName in rec.keys():
                self.ColDict[recName] = rec[recName]
    
        print "Initializing InfoPanel_Column ->>>>"
        print "treePyData:", treePyData
        print "self.sourceTable:", self.sourceTable
        print "self.recID:", self.recID
        print "self.parentTable:", self.parentTable
        print "self.parentRecID:", self.parentRecID

        print "ColDict:", self.ColDict

        self.SetBackgroundColour(wx.WHITE) # this overrides color of enclosing panel
        colPnlSiz = wx.GridBagSizer(1, 1)
        note1 = wx.StaticText(self, -1, 'Bold ')
        self.bolded = note1.GetFont() 
        self.bolded.SetWeight(wx.BOLD) 
        note1.SetFont(self.bolded)
        gRow = 0
        colPnlSiz.Add(note1, pos=(gRow, 0), flag=wx.ALIGN_RIGHT|wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        colPnlSiz.Add(wx.StaticText(self, -1, 'items are required'),
                     pos=(gRow, 1), flag=wx.TOP|wx.RIGHT|wx.BOTTOM, border=5)
  
        gRow += 1
        colPnlSiz.Add(wx.StaticLine(self), pos=(gRow, 0), span=(1, 3), flag=wx.EXPAND)
              
        gRow += 1
        colHeadLabel = wx.StaticText(self, -1, 'Column Heading')
        colHeadLabel.SetFont(self.bolded)
        colPnlSiz.Add(colHeadLabel, pos=(gRow, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.tcColHead = wx.TextCtrl(self)
        if self.ColDict['ColumnHeading'] != None:
            self.tcColHead.SetValue('%s' % self.ColDict['ColumnHeading'])
        colPnlSiz.Add(self.tcColHead, pos=(gRow, 1), span=(1, 1), 
            flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)
  
        gRow += 1
        colPnlSiz.Add(wx.StaticText(self, -1, "Text for the column's top cell, in the output dataset"),
                     pos=(gRow, 0), span=(1, 2), flag=wx.LEFT|wx.BOTTOM, border=5)
        gRow += 1
        colPnlSiz.Add(wx.StaticLine(self), pos=(gRow, 0), span=(1, 2), flag=wx.EXPAND)
   
        gRow += 1
        colPnlSiz.Add(wx.StaticText(self, -1, 'Listing order'),
                     pos=(gRow, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.tcListingOrder = wx.TextCtrl(self)
        if self.ColDict['ListingOrder'] != None:
            self.tcListingOrder.SetValue('%d' % self.ColDict['ListingOrder'])
        colPnlSiz.Add(self.tcListingOrder, pos=(gRow, 1), span=(1, 1), 
            flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)
   
        gRow += 1
        colPnlSiz.Add(wx.StaticText(self, -1, 'Use this to specify the order of Columns in a sheet. \nWill be auto-assigned if you leave it out.'),
                     pos=(gRow, 0), span=(1, 2), flag=wx.LEFT|wx.BOTTOM, border=5)
   
        gRow += 1
        colPnlSiz.Add(wx.StaticLine(self), pos=(gRow, 0), span=(1, 2), flag=wx.EXPAND)
 
        gRow += 1
        colTypeLabel = wx.StaticText(self, -1, 'Column Type')
        colTypeLabel.SetFont(self.bolded)
        colPnlSiz.Add(colTypeLabel, pos=(gRow, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        lstColTypes = ['Timestamp', 'Constant', 'Aggregate', 'Formula']
        self.cbxColType = wx.ComboBox(self, -1, choices=lstColTypes, style=wx.CB_READONLY)
        self.cbxColType.Bind(wx.EVT_COMBOBOX, lambda evt: self.onSelColType(evt))
        if self.ColDict['ColType'] != None:
            self.cbxColType.SetValue('%s' % self.ColDict['ColType'])
        colPnlSiz.Add(self.cbxColType, pos=(gRow, 1), span=(1, 1), flag=wx.LEFT, border=5)

        gRow += 1
        colPnlSiz.Add(wx.StaticLine(self), pos=(gRow, 0), span=(1, 2), flag=wx.EXPAND)

        self.colDetailPnl = wx.Panel(self, wx.ID_ANY) # content varies by ColType
        self.onSelColType() # have to explictly call this 1st time

        gRow += 1
        colPnlSiz.Add(self.colDetailPnl, pos=(gRow, 0), span=(1, 2), flag=wx.EXPAND)
        
        gRow += 1
        colPnlSiz.Add(wx.StaticLine(self), pos=(gRow, 0), span=(1, 3), flag=wx.EXPAND)
   
        gRow += 1
        self.btnSave = wx.Button(self, label="Save", size=(90, 28))
        self.btnSave.Bind(wx.EVT_BUTTON, lambda evt: self.onClick_BtnSave(evt))
        colPnlSiz.Add(self.btnSave, pos=(gRow, 0), flag=wx.LEFT|wx.BOTTOM, border=5)
        self.btnCancel = wx.Button(self, label="Cancel", size=(90, 28))
        self.btnCancel.Bind(wx.EVT_BUTTON, lambda evt: self.onClick_BtnCancel(evt))
        colPnlSiz.Add(self.btnCancel, pos=(gRow, 1), flag=wx.LEFT|wx.BOTTOM, border=5)

        self.SetSizer(colPnlSiz)
        self.SetAutoLayout(1)
        self.SetupScrolling()


    def onSelColType(self, event = -1):
        """
        Shows the relevant fields based on Column Type
        Default 'event = -1' is dummy value for initial call when first created
        """
        colTyp = self.cbxColType.GetValue()
        lstColTypes = ['Timestamp', 'Constant', 'Aggregate', 'Formula'] # valid values
        colDetailSiz = wx.GridBagSizer(1, 1)
        self.colDetailPnl.DestroyChildren()
        gRow = 0
        if colTyp == 'Timestamp':
            tsyLabel = wx.StaticText(self.colDetailPnl, -1, 'Time System')
            tsyLabel.SetFont(self.bolded)
            colDetailSiz.Add(tsyLabel, pos=(gRow, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
            lstTmSysOpts = ['Clock Time', 'Solar Time']
            self.cbxTmSys = wx.ComboBox(self.colDetailPnl, -1, choices=lstTmSysOpts, style=wx.CB_READONLY)

            if self.ColDict['TimeSystem'] == None:
                self.cbxTmSys.SetValue('%s' % lstTmSysOpts[0]) # default, usual
            else:
                self.cbxTmSys.SetValue('%s' % self.ColDict['TimeSystem'])
            colDetailSiz.Add(self.cbxTmSys, pos=(gRow, 1), span=(1, 1), flag=wx.LEFT, border=5)

            gRow += 1
            self.ckTmIsInterval = wx.CheckBox(self.colDetailPnl, label="Interval from a starting timestamp?")
            colDetailSiz.Add(self.ckTmIsInterval, pos=(gRow, 0), span=(1, 2), flag=wx.LEFT|wx.BOTTOM, border=5)
            self.ckTmIsInterval.SetValue(self.ColDict['TimeIsInterval'])

            gRow += 1
            colDetailSiz.Add(wx.StaticText(self.colDetailPnl, -1, 'Starting timestamp'),
                     pos=(gRow, 0), span=(1, 1), flag=wx.LEFT|wx.BOTTOM, border=5)
            self.tcIntervalIsFrom = wx.TextCtrl(self.colDetailPnl)
            if self.ColDict['IntervalIsFrom'] != None:
                self.tcIntervalIsFrom.SetValue('%s' % self.ColDict['IntervalIsFrom'])
            colDetailSiz.Add(self.tcIntervalIsFrom, pos=(gRow, 1), span=(1, 1), 
                flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)
            
        if colTyp == 'Constant':
            dtlLabel = wx.StaticText(self.colDetailPnl, -1, 'Constant')
            dtlLabel.SetFont(self.bolded)
            colDetailSiz.Add(dtlLabel, pos=(gRow, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
            self.tcConstant = wx.TextCtrl(self.colDetailPnl)
            if self.ColDict['Constant'] != None:
                self.tcConstant.SetValue('%s' % self.ColDict['Constant'])
            colDetailSiz.Add(self.tcConstant, pos=(gRow, 1), span=(1, 1), 
                flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)
            
            gRow += 1
            colDetailSiz.Add(wx.StaticText(self.colDetailPnl, -1, 'A label to appear in each row'),
                     pos=(gRow, 0), span=(1, 2), flag=wx.LEFT|wx.BOTTOM, border=5)
            
        if colTyp == 'Aggregate':
            aggLabel = wx.StaticText(self.colDetailPnl, -1, 'Aggregate')
            aggLabel.SetFont(self.bolded)
            colDetailSiz.Add(aggLabel, pos=(gRow, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)

            lstAggOpts = ['Avg', 'Min', 'Max', 'Count', 'Sum', 'StDev']
            self.cbxAggType = wx.ComboBox(self.colDetailPnl, -1, choices=lstAggOpts, style=wx.CB_READONLY)

            if self.ColDict['AggType'] == None:
                self.cbxAggType.SetValue('%s' % lstAggOpts[0]) # default, usual
            else:
                self.cbxAggType.SetValue('%s' % self.ColDict['AggType'])
            colDetailSiz.Add(self.cbxAggType, pos=(gRow, 1), span=(1, 1), flag=wx.LEFT, border=5)

            gRow += 1
            aggStaLabel = wx.StaticText(self.colDetailPnl, -1, 'Station')
            aggStaLabel.SetFont(self.bolded)
            colDetailSiz.Add(aggStaLabel, pos=(gRow, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)

            stSQL = "SELECT ID, StationName FROM Stations ORDER BY ID;"
            self.cbxAggStation = wx.ComboBox(self.colDetailPnl, -1, choices=[], style=wx.CB_READONLY)
            scidb.fillComboboxFromSQL(self.cbxAggStation, stSQL, keyCol=0, visibleCol=1)
            scidb.setComboboxToClientData(self.cbxAggStation, self.ColDict['AggStationID'])
            colDetailSiz.Add(self.cbxAggStation, pos=(gRow, 1), span=(1, 2), flag=wx.LEFT, border=5)

            gRow += 1
            aggSeriesLabel = wx.StaticText(self.colDetailPnl, -1, 'Series')
            aggSeriesLabel.SetFont(self.bolded)
            colDetailSiz.Add(aggSeriesLabel, pos=(gRow, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
            
            stSQL = "SELECT ID, DataSeriesDescription FROM DataSeries ORDER BY ID;"
            self.cbxAggSeries = wx.ComboBox(self.colDetailPnl, -1, choices=[], style=wx.CB_READONLY)
            scidb.fillComboboxFromSQL(self.cbxAggSeries, stSQL, keyCol=0, visibleCol=1)
            scidb.setComboboxToClientData(self.cbxAggSeries, self.ColDict['AggDataSeriesID'])
            colDetailSiz.Add(self.cbxAggSeries, pos=(gRow, 1), span=(1, 2), flag=wx.LEFT, border=5)

        if colTyp == 'Formula':
            fmlLabel = wx.StaticText(self.colDetailPnl, -1, 'Formula')
            fmlLabel.SetFont(self.bolded)
            colDetailSiz.Add(fmlLabel, pos=(gRow, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)

            self.tcFormula = wx.TextCtrl(self.colDetailPnl)
            if self.ColDict['Formula'] != None:
                self.tcFormula.SetValue('%s' % self.ColDict['Formula'])
            colDetailSiz.Add(self.tcFormula, pos=(gRow, 1), span=(1, 1), 
                flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)
            
            gRow += 1
            colDetailSiz.Add(wx.StaticText(self.colDetailPnl, -1, 'Only used for Excel output'),
                     pos=(gRow, 0), span=(1, 2), flag=wx.LEFT|wx.BOTTOM, border=5)

        # show the Contents Format textboxes for any Column Type except Constant
        if colTyp == 'Timestamp' or colTyp == 'Aggregate' or colTyp == 'Formula':
            gRow += 1
            colDetailSiz.Add(wx.StaticLine(self.colDetailPnl), pos=(gRow, 0), span=(1, 2), flag=wx.EXPAND)

            gRow += 1
            colDetailSiz.Add(wx.StaticText(self.colDetailPnl, -1, 'Format depends on Column Type'),
                     pos=(gRow, 0), span=(1, 2), flag=wx.LEFT|wx.BOTTOM, border=5)

            gRow += 1
            colDetailSiz.Add(wx.StaticText(self.colDetailPnl, -1, 'Format (Python)'),
                             pos=(gRow, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)

            self.tcFormat_Python = wx.TextCtrl(self.colDetailPnl)
            if self.ColDict['Format_Python'] != None:
                self.tcFormat_Python.SetValue('%s' % self.ColDict['Format_Python'])
            colDetailSiz.Add(self.tcFormat_Python, pos=(gRow, 1), span=(1, 1), 
                flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)

            gRow += 1
            colDetailSiz.Add(wx.StaticText(self.colDetailPnl, -1, 'Will be applied to text output'),
                     pos=(gRow, 0), span=(1, 2), flag=wx.LEFT|wx.BOTTOM, border=5)

            gRow += 1
            colDetailSiz.Add(wx.StaticText(self.colDetailPnl, -1, 'Format (Excel)'),
                             pos=(gRow, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)

            self.tcFormat_Excel = wx.TextCtrl(self.colDetailPnl)
            if self.ColDict['Format_Excel'] != None:
                self.tcFormat_Excel.SetValue('%s' % self.ColDict['Format_Excel'])
            colDetailSiz.Add(self.tcFormat_Excel, pos=(gRow, 1), span=(1, 1), 
                flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)

            gRow += 1
            colDetailSiz.Add(wx.StaticText(self.colDetailPnl, -1, 'Will be applied to Excel output'),
                     pos=(gRow, 0), span=(1, 2), flag=wx.LEFT|wx.BOTTOM, border=5)

        self.colDetailPnl.SetSizer(colDetailSiz)
        self.colDetailPnl.SetAutoLayout(1)
        self.colDetailPnl.Layout()
        self.Layout()
        # re-set up scrolling for panel; size change can cancel it
        self.SetAutoLayout(1)
        self.SetupScrolling()

    def validateColPanel(self):
        """
        Validate Column panel and extract values into 'ColDict'.
        Returns 0 if anything incomplete, 1 in all OK
        """
        # clean up whitespace; remove leading/trailing & multiples
        self.ColDict['ColumnHeading'] = " ".join(self.tcColHead.GetValue().split())
        print "ColumnHeading:", self.ColDict['ColumnHeading']
        if self.ColDict['ColumnHeading'] == '':
            wx.MessageBox('Need Column Heading', 'Missing',
                wx.OK | wx.ICON_INFORMATION)
            self.tcColHead.SetValue(self.ColDict['ColumnHeading'])
            self.tcColHead.SetFocus()
            self.Scroll(0, 0) # the required controls are all at the top
            return 0
    
        maxLen = scidb.lenOfVarcharTableField('OutputColumns', 'ColumnHeading')
        if maxLen < 1:
            wx.MessageBox('Error %d getting [OutputColumns].[ColumnHeading] field length.' % maxLen, 'Error',
                wx.OK | wx.ICON_INFORMATION)
            return 0
        if len(self.ColDict['ColumnHeading']) > maxLen:
            wx.MessageBox('Max length for Column Heading is %d characters.\n\nIf trimmed version is acceptable, retry.' % maxLen, 'Invalid',
                wx.OK | wx.ICON_INFORMATION)
            self.tcColHead.SetValue(self.ColDict['ColumnHeading'][:(maxLen)])
            self.tcColHead.SetFocus()
            self.Scroll(0, 0) # the required controls are all at the top
            return 0
        
        try:
            self.ColDict['ListingOrder'] = int(self.tcListingOrder.GetValue())
        except:
            # autocreate, 1 higher than previously existing
            print "self.parentRecID, to use in ListingOrder query:",  self.parentRecID
            stSQL = "SELECT MAX(CAST(OutputColumns.ListingOrder AS INTEGER)) AS MaxLstOrd " \
                    "FROM OutputColumns WHERE WorksheetID = ?;"
            scidb.curD.execute(stSQL, (self.parentRecID,))
            rec = scidb.curD.fetchone()
            print "Max Listing order fetched:", rec
            if rec['MaxLstOrd'] == None: # none yet
                self.ColDict['ListingOrder'] = 1
            else:
                self.ColDict['ListingOrder'] = rec['MaxLstOrd'] + 1
            self.tcListingOrder.SetValue('%d' % self.ColDict['ListingOrder'])
            wx.MessageBox('Listing Order auto-set to %d.' % self.ColDict['ListingOrder'], 'Info',
                wx.OK | wx.ICON_INFORMATION)
        print "Listing Order:", self.ColDict['ListingOrder']
        
        self.ColDict['ColType'] = self.cbxColType.GetValue() # constrained to list
        print "Column Type:", self.ColDict['ColType']
        if self.ColDict['ColType'] == '':
            wx.MessageBox('Need Column Type', 'Missing',
                wx.OK | wx.ICON_INFORMATION)
            self.cbxColType.SetFocus()
            self.Scroll(0, 0) # the required controls are all at the top
            return 0
        
        if self.ColDict['ColType'] == 'Timestamp':
            self.ColDict['TimeSystem'] = self.cbxTmSys.GetValue() # constrained to list
            if self.ColDict['TimeSystem'] == '':
                wx.MessageBox('Need Time System', 'Missing',
                    wx.OK | wx.ICON_INFORMATION)
                self.cbxTmSys.SetFocus()
                self.Scroll(0, 0) # the required controls are all at the top
                return 0

            self.ColDict['TimeIsInterval'] = self.ckTmIsInterval.GetValue()
            if self.ColDict['TimeIsInterval'] == 1:
                sFmt = '%Y-%m-%d %H:%M:%S'
                try:
                    #datetime.strptime(date_string, format)
                    self.ColDict['IntervalIsFrom'] = datetime.datetime.strptime(self.tcIntervalIsFrom.GetValue(), sFmt)
                except:
                    self.ColDict['IntervalIsFrom'] = None
                print "Retrieved IntervalIsFrom:", self.ColDict['IntervalIsFrom']
                if self.ColDict['IntervalIsFrom'] == None:
                    # offer a reasonable default
                    startOfCurYear = datetime.datetime(datetime.datetime.now().year, 1, 1)
                    self.tcIntervalIsFrom.SetValue(startOfCurYear.strftime(sFmt))
                    self.tcFormat_Python.SetValue('%.2f')
                    self.tcFormat_Excel.SetValue('0.00')
                    wx.MessageBox("""Starting timestamp set to beginning of this year,
                        which will give Julian Day for this year.
                        Adjust as needed, but keep the same format.""", 'Missing',
                        wx.OK | wx.ICON_INFORMATION)
                    return 0

        if self.ColDict['ColType'] == 'Constant':
            # clean up whitespace; remove leading/trailing & multiples
            self.ColDict['Constant'] = " ".join(self.tcConstant.GetValue().split())
            self.tcConstant.SetValue(self.ColDict['Constant'])
            if self.ColDict['Constant'] == '':
                wx.MessageBox('Blank "Constant" will just create an empty column.', 'Info',
                    wx.OK | wx.ICON_INFORMATION)
                self.ColDict['Constant'] = None
            else:
                maxLen = scidb.lenOfVarcharTableField('OutputColumns', 'Constant')
                if maxLen < 1:
                    wx.MessageBox('Error %d getting [OutputColumns].[Constant] field length.' % maxLen, 'Error',
                        wx.OK | wx.ICON_INFORMATION)
                    return 0
                if len(self.ColDict['Constant']) > maxLen:
                    wx.MessageBox("""Max length for "Constant" is %d characters.\nIf trimmed version is acceptable, retry.""" % maxLen, 'Too Long',
                        wx.OK | wx.ICON_INFORMATION)
                    self.tcConstant.SetValue(self.ColDict['Constant'][:(maxLen)])
                    self.tcConstant.SetFocus()
                    return 0

        if self.ColDict['ColType'] == 'Aggregate':
            self.ColDict['AggType'] = self.cbxAggType.GetValue() # constrained to list
            print "Aggregate Type:", self.ColDict['AggType']
            if self.ColDict['AggType'] == '':
                wx.MessageBox('Need Aggregate Type', 'Missing',
                    wx.OK | wx.ICON_INFORMATION)
                self.cbxAggType.SetFocus()
                return 0

            self.ColDict['AggStationID'] = scidb.getComboboxIndex(self.cbxAggStation)
            print "Station ID:", self.ColDict['AggStationID']
            if self.ColDict['AggStationID'] == None:
                wx.MessageBox('Select the Station to use data from', 'Missing',
                    wx.OK | wx.ICON_INFORMATION)
                self.cbxAggStation.SetFocus()
                return 0

            self.ColDict['AggDataSeriesID'] = scidb.getComboboxIndex(self.cbxAggSeries)
            print "Station ID:", self.ColDict['AggDataSeriesID']
            if self.ColDict['AggDataSeriesID'] == None:
                wx.MessageBox('Select the Data Series to use data from', 'Missing',
                    wx.OK | wx.ICON_INFORMATION)
                self.cbxAggSeries.SetFocus()
                return 0

        if self.ColDict['ColType'] == 'Formula':
            # clean up whitespace; remove leading/trailing & multiples
            self.ColDict['Formula'] = " ".join(self.tcFormula.GetValue().split())
            self.tcFormula.SetValue(self.ColDict['Formula'])
            if self.ColDict['Formula'] == '':
                wx.MessageBox('Blank "Formula" will just create an empty column.', 'Info',
                    wx.OK | wx.ICON_INFORMATION)
                self.ColDict['Formula'] = None
            else:
                maxLen = scidb.lenOfVarcharTableField('OutputColumns', 'Formula')
                if maxLen < 1:
                    wx.MessageBox('Error %d getting [OutputColumns].[Formula] field length.' % maxLen, 'Error',
                        wx.OK | wx.ICON_INFORMATION)
                    return 0
                if len(self.ColDict['Formula']) > maxLen:
                    wx.MessageBox("""Max length for "Formula" is %d characters.\nIf trimmed version is acceptable, retry.""" % maxLen, 'Too Long',
                        wx.OK | wx.ICON_INFORMATION)
                    self.tcFormula.SetValue(self.ColDict['Formula'][:(maxLen)])
                    self.tcFormula.SetFocus()
                    return 0
        # Contents Format textboxes are there for any Column Type except Constant
        if self.ColDict['ColType'] == 'Timestamp' or self.ColDict['ColType'] == 'Aggregate' or self.ColDict['ColType'] == 'Formula':
            self.ColDict['Format_Python'] = " ".join(self.tcFormat_Python.GetValue().split())
            print "Contents Format:", self.ColDict['Format_Python']
            if self.ColDict['Format_Python'] == '':
                self.tcFormat_Python.SetValue(self.ColDict['Format_Python'])    
            maxLen = scidb.lenOfVarcharTableField('OutputColumns', 'Format_Python')
            if maxLen < 1:
                wx.MessageBox('Error %d getting [OutputColumns].[Format_Python] field length.' % maxLen, 'Error',
                    wx.OK | wx.ICON_INFORMATION)
                return 0
            if len(self.ColDict['Format_Python']) > maxLen:
                wx.MessageBox('Max length for Python Format is %d characters.\n\nIf trimmed version is acceptable, retry.' % maxLen, 'Invalid',
                    wx.OK | wx.ICON_INFORMATION)
                self.tcFormat_Python.SetValue(self.ColDict['Format_Python'][:(maxLen)])
                self.tcFormat_Python.SetFocus()
                return 0
            if self.ColDict['Format_Python'] == '':
                self.ColDict['Format_Python'] = None # store Null instead of empty string

            self.ColDict['Format_Excel'] = " ".join(self.tcFormat_Excel.GetValue().split())
            print "Contents Format:", self.ColDict['Format_Excel']
            if self.ColDict['Format_Excel'] == '':
                self.tcFormat_Excel.SetValue(self.ColDict['Format_Excel'])    
            maxLen = scidb.lenOfVarcharTableField('OutputColumns', 'Format_Excel')
            if maxLen < 1:
                wx.MessageBox('Error %d getting [OutputColumns].[Format_Excel] field length.' % maxLen, 'Error',
                    wx.OK | wx.ICON_INFORMATION)
                return 0
            if len(self.ColDict['Format_Excel']) > maxLen:
                wx.MessageBox('Max length for Excel Format is %d characters.\n\nIf trimmed version is acceptable, retry.' % maxLen, 'Invalid',
                    wx.OK | wx.ICON_INFORMATION)
                self.tcFormat_Excel.SetValue(self.ColDict['Format_Excel'][:(maxLen)])
                self.tcFormat_Excel.SetFocus()
                return 0
            if self.ColDict['Format_Excel'] == '':
                self.ColDict['Format_Excel'] = None # store Null instead of empty string

        return 1 # everything validated
   
    def onClick_BtnSave(self, event):
        # finish rewriting this for Sheets
        """
        If this frame is shown in a Dialog, the Column is being created.
        Attempt to create a new record and make the new record ID available.
        If this frame is shown in the main form, attempt to save any changes to the existing DB record
        """
        if self.validateColPanel() == 0:
            return

#        wx.MessageBox('OK so far, but "Save" is not implemented yet', 'Info', 
#            wx.OK | wx.ICON_INFORMATION)
#        return
   
        # we have self.parentClassName from initialization; "wxDialog" if in the dialog
        if self.parentClassName == "wxDialog": # in the Dialog, create a new DB record
            stSQL = """
                INSERT INTO OutputColumns
                (WorksheetID, ColumnHeading, ColType,
                TimeSystem, TimeIsInterval, IntervalIsFrom,
                Constant, Formula, AggType, AggStationID, AggDataSeriesID,
                Format_Python, Format_Excel, ListingOrder)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?);
                """
            try:
                scidb.curD.execute(stSQL, (self.parentRecID, 
                    self.ColDict['ColumnHeading'], self.ColDict['ColType'], 
                    self.ColDict['TimeSystem'], self.ColDict['TimeIsInterval'], self.ColDict['IntervalIsFrom'], 
                    self.ColDict['Constant'], self.ColDict['Formula'], 
                    self.ColDict['AggType'], self.ColDict['AggStationID'], self.ColDict['AggDataSeriesID'], 
                    self.ColDict['Format_Python'], self.ColDict['Format_Excel'],
                    self.ColDict['ListingOrder']))
                scidb.datConn.commit()
                # get record ID of new record
                self.newRecID = scidb.curD.lastrowid
                self.addRecOK = 1

            except sqlite3.IntegrityError: # duplicate name or required field missing
                print "could not add Column record to DB table"
                wx.MessageBox('Error creating Column', 'Error', 
                    wx.OK | wx.ICON_INFORMATION)
                self.newRecID = 0
                self.addRecOK = 0
            # let calling routine destroy, after getting any needed parameters
            parObject = self.GetParent() # the dialog
            parObject.EndModal(self.addRecOK) #exit the dialog
   
        else: # self.parentClassNameis not "wxDialog"; we're in the frame, update the existing record
            self.newRecID = 0 # this will not be a new record
            stSQL = """
                UPDATE OutputColumns SET  
                ColumnHeading = ?, ColType = ?,
                TimeSystem = ?, TimeIsInterval = ?, IntervalIsFrom = ?,
                Constant = ?, Formula = ?,
                AggType = ?, AggStationID = ?, AggDataSeriesID = ?,
                Format_Python = ?, Format_Excel = ?, ListingOrder = ?
                WHERE ID = ?;
            """
            try:
                scidb.curD.execute(stSQL, (self.ColDict['ColumnHeading'], self.ColDict['ColType'], 
                    self.ColDict['TimeSystem'], self.ColDict['TimeIsInterval'], self.ColDict['IntervalIsFrom'], 
                    self.ColDict['Constant'], self.ColDict['Formula'], 
                    self.ColDict['AggType'], self.ColDict['AggStationID'], self.ColDict['AggDataSeriesID'], 
                    self.ColDict['Format_Python'], self.ColDict['Format_Excel'],
                    self.ColDict['ListingOrder'], self.recID))
                scidb.datConn.commit()
                self.updateRecOK = 1
                # update the label on the tree branch
                parObject1 = self.GetParent() # the details panel
#                print "Parent 1:", parObject1, ", Class", parObject1.GetClassName()
                parObject2 = parObject1.GetParent() # the vertical splitter window
#                print "Parent 2:", parObject2, ", Class", parObject2.GetClassName()
                parObject3 = parObject2.GetParent() # panel
#                print "Parent 3:", parObject3, ", Class", parObject3.GetClassName()
                parObject4 = parObject3.GetParent() # the horizontal splitter window
#                print "Parent 4:", parObject4, ", Class", parObject4.GetClassName()
                parObject5 = parObject4.GetParent() # the main panel that owns the tree
#                print "Parent 5:", parObject5, ", Class", parObject5.GetClassName()
                parObject5.dsTree.SetItemText(parObject5.dsInfoPnl.correspondingTreeItem, self.ColDict['ColumnHeading'])
                wx.MessageBox('Changes saved', 'Updated',
                    wx.OK | wx.ICON_INFORMATION)
            except sqlite3.IntegrityError:
                print "could not update Column record to DB table"
                wx.MessageBox('Error updating Column', 'Error', 
                    wx.OK | wx.ICON_INFORMATION)
                self.updateRecOK = 0       
        return
        
# rewrite for Column    

    def onClick_BtnCancel(self, event):
        """
        If this frame is shown in a Dialog, the Sheet is being created. Exit with no changes.
        If this frame is shown in the main form, restore it from the saved DB record
        """
        self.newRecID = 0 # new record does not apply
        parObject = self.GetParent()
        if parObject.GetClassName() == "wxDialog":
            parObject.EndModal(0) # if in the creation dialog, exit with no changes to the DB
#            parObject.Destroy() 
        else: # in the main form
            wx.MessageBox('To lose canges, click a different tree item, then click this one again.', 'Undo', 
                wx.OK | wx.ICON_INFORMATION)
#            wx.MessageBox('Undoing any edits', 'Undo', 
#                wx.OK | wx.ICON_INFORMATION)
            
        return   

class Dialog_MakeDataset(wx.Dialog):
    def __init__(self, parent, id, title = "Create Dataset", parentTableRec = None):
        wx.Dialog.__init__(self, parent, id)
        self.InitUI(parentTableRec)
        self.SetSize((450, 400))
        self.SetTitle(title) # overrides title passed above

    def InitUI(self, parentTableRec):
        print "Initializing Dialog_MakeDataset; parentTableRec:", parentTableRec
        self.sourceTable = parentTableRec[0] # 'OutputSheets' or 'OutputBooks'
        self.recID = parentTableRec[1] # the record ID in that table
        stSQL_Bk = """
            SELECT ID, BookName, Longitude, HourOffset, NumberOfTimeSlicesPerDay,
            OutputDataStart, OutputDataEnd,
            PutAllOutputRowsInOneSheet, BlankRowBetweenDataBlocks,
             COALESCE(OutputDataStart, (SELECT MIN(Date) FROM DataDates)) AS EffectiveStartDay, 
             COALESCE(OutputDataEnd, (SELECT MAX(Date) FROM DataDates)) AS EffectiveEndDay,
             (SELECT COUNT(Date) FROM DataDates 
            WHERE Date >= (SELECT COALESCE(B1.OutputDataStart,
            (SELECT MIN(D1.Date) FROM DataDates AS D1)) AS St FROM OutputBooks AS B1
            WHERE B1.ID = OutputBooks.ID) 
            AND Date <= (SELECT COALESCE(B2.OutputDataEnd,
            (SELECT MAX(D2.Date) FROM DataDates AS D2)) AS En FROM OutputBooks AS B2
            WHERE B2.ID = OutputBooks.ID))
             AS CtOfDays
            FROM OutputBooks WHERE OutputBooks.ID = ?;
        """
        stSQL_SheetsForBook = """
            SELECT ID, BookID, WorksheetName, DataSetNickname, ListingOrder,
            (SELECT COUNT(C1.ID) FROM OutputColumns AS C1 
            WHERE C1.WorksheetID = OutputSheets.ID) AS CtCols, 
            (SELECT COUNT(C2.ID) FROM OutputColumns AS C2 
            WHERE C2.WorksheetID = OutputSheets.ID 
            AND C2.ColType = 'Aggregate') AS CtAggCols 
            FROM OutputSheets
            WHERE BookID = ?
            ORDER BY ListingOrder;        
        """
        stSQL_Sheet = """
            SELECT ID, BookID, WorksheetName, DataSetNickname, ListingOrder,
            (SELECT COUNT(C1.ID) FROM OutputColumns AS C1 
            WHERE C1.WorksheetID = OutputSheets.ID) AS CtCols, 
            (SELECT COUNT(C2.ID) FROM OutputColumns AS C2 
            WHERE C2.WorksheetID = OutputSheets.ID 
            AND C2.ColType = 'Aggregate') AS CtAggCols 
            FROM OutputSheets
            WHERE ID = ?;        
        """
        if self.sourceTable == 'OutputSheets':
            stItem = 'Sheet'
            # get the sheet information
            scidb.curD.execute(stSQL_Sheet, (self.recID,))
            rec = scidb.curD.fetchone()
            self.shDict = {} # store sheet info in dictionary
            for recName in rec.keys():
                self.shDict[recName] = rec[recName]
            # also, store this dictionary in a 1-item list; same format as if multiple
            self.lShs = []
            self.lShs.append(copy.copy(self.shDict))
            self.stItemName = self.shDict['WorksheetName']
            # get the sheet's book information
            scidb.curD.execute(stSQL_Bk, (self.shDict['BookID'],))
            rec = scidb.curD.fetchone()
            self.bkDict = {} # store book info in dictionary
            for recName in rec.keys():
                self.bkDict[recName] = rec[recName]
        else:
            stItem = 'Book'
            # get the book information
            scidb.curD.execute(stSQL_Bk, (self.recID,))
            rec = scidb.curD.fetchone()
            self.bkDict = {} # store book info in dictionary
            for recName in rec.keys():
                self.bkDict[recName] = rec[recName]
            self.stItemName = self.bkDict['BookName']
            # get info for the book's sheets
            scidb.curD.execute(stSQL_SheetsForBook, (self.recID,))
            recs = scidb.curD.fetchall()
            # store as a list of dictionaries
            self.lShs = []
            for rec in recs:
                shDict = {}
                for recName in rec.keys():
                    shDict[recName] = rec[recName]
                self.lShs.append(copy.copy(shDict))                  

        self.SetBackgroundColour(wx.WHITE)
        mkDtSetSiz = wx.GridBagSizer(1, 1)
        note1 = wx.StaticText(self, -1, 'Make Dataset For: ')
        bolded = note1.GetFont() 
        bolded.SetWeight(wx.BOLD) 
        note1.SetFont(bolded)
        gRow = 0
        mkDtSetSiz.Add(note1, pos=(gRow, 0), flag=wx.ALIGN_RIGHT|wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        mkDtSetSiz.Add(wx.StaticText(self, -1, stItem + ' "' + self.stItemName + '"'),
                     pos=(gRow, 1), flag=wx.TOP|wx.RIGHT|wx.BOTTOM, border=5)

        gRow += 1
        mkDtSetSiz.Add(wx.StaticLine(self), pos=(gRow, 0), span=(1, 5), flag=wx.EXPAND)

        gRow += 1
        mkDtSetSiz.Add(wx.StaticText(self, -1, 'Output As:'),
                     pos=(gRow, 0), span=(1, 2), flag=wx.LEFT|wx.BOTTOM, border=5)

        iRBLeftBorderWd = 30
        gRow += 1
        self.rbExcel = wx.RadioButton(self, label='Excel workbook', style=wx.RB_GROUP)
        mkDtSetSiz.Add(self.rbExcel, pos=(gRow, 0), span=(1, 3), flag=wx.ALIGN_LEFT|wx.LEFT, border=iRBLeftBorderWd)
        self.rbExcel.Bind(wx.EVT_RADIOBUTTON, self.giveRBInfo)

        gRow += 1
        self.rbTabDelim = wx.RadioButton(self, label='Tab-delimited text')
        mkDtSetSiz.Add(self.rbTabDelim, pos=(gRow, 0), span=(1, 3), flag=wx.ALIGN_LEFT|wx.LEFT, border=iRBLeftBorderWd)
        self.rbTabDelim.Bind(wx.EVT_RADIOBUTTON, self.giveRBInfo)
        
        gRow += 1
        self.rbCommaDelim = wx.RadioButton(self, label='Comma-separated values ("CSV")')
        mkDtSetSiz.Add(self.rbCommaDelim, pos=(gRow, 0), span=(1, 3), flag=wx.ALIGN_LEFT|wx.LEFT, border=iRBLeftBorderWd)
        self.rbCommaDelim.Bind(wx.EVT_RADIOBUTTON, self.giveRBInfo)

        gRow += 1
        mkDtSetSiz.Add((0, 10), pos=(gRow, 0), span=(1, 3)) # some space

        gRow += 1
#        self.btnBrowseDir = wx.Button(self, label="Dir", size=(90, 28))
        self.btnBrowseDir = wx.Button(self, label="Dir", size=(-1, -1))
        self.btnBrowseDir.Bind(wx.EVT_BUTTON, lambda evt: self.onClick_BtnGetDir(evt))
        mkDtSetSiz.Add(self.btnBrowseDir, pos=(gRow, 0), flag=wx.LEFT, border=5)
        
        mkDtSetSiz.Add(wx.StaticText(self, -1, 'Base name, file or folder:'),
                     pos=(gRow, 1), span=(1, 1), flag=wx.ALIGN_RIGHT|wx.LEFT, border=5)

        self.tcBaseName = wx.TextCtrl(self, -1)
        mkDtSetSiz.Add(self.tcBaseName, pos=(gRow, 2), span=(1, 3),
            flag=wx.ALIGN_LEFT|wx.EXPAND, border=5)
        self.tcBaseName.SetValue(self.stItemName)

        gRow += 1
        self.tcDir = wx.TextCtrl(self, -1, style=wx.TE_MULTILINE)
        mkDtSetSiz.Add(self.tcDir, pos=(gRow, 0), span=(2, 5),
            flag=wx.ALIGN_LEFT|wx.LEFT|wx.BOTTOM|wx.EXPAND, border=5)
        gRow += 1 # space for the 2 grid rows for tcDir
        self.tcDir.SetValue('(save output in default directory)')

        
        gRow += 1
        mkDtSetSiz.Add(wx.StaticLine(self), pos=(gRow, 0), span=(1, 5), flag=wx.EXPAND)

        gRow += 1
        self.tcOutputOptInfo = wx.TextCtrl(self, -1, style=wx.TE_MULTILINE|wx.TE_READONLY)
        mkDtSetSiz.Add(self.tcOutputOptInfo, pos=(gRow, 0), span=(3, 5),
            flag=wx.ALIGN_LEFT|wx.TOP|wx.LEFT|wx.BOTTOM|wx.EXPAND, border=5)
        gRow += 1 # space for the three grid rows for tcOutputOptInfo
        gRow += 1

        self.giveRBInfo(-1) # have to explictly call this 1st time; -1 is dummy value for event
        
        gRow += 1
        mkDtSetSiz.Add(wx.StaticLine(self), pos=(gRow, 0), span=(1, 5), flag=wx.EXPAND)
        gRow += 1
        mkDtSetSiz.Add(wx.StaticLine(self), pos=(gRow, 0), span=(1, 5), flag=wx.EXPAND)

        gRow += 1
        sheetNoteBlocking1 = wx.StaticText(self, -1, 'NOTE: Making a dataset will block this application until complete.')
        sheetNoteBlocking1.SetFont(bolded)
        mkDtSetSiz.Add(sheetNoteBlocking1, pos=(gRow, 0), span=(1, 5), flag=wx.TOP|wx.LEFT, border=5)
        gRow += 1
        sheetNoteBlocking2 = wx.StaticText(self, -1, ' A full dataset can take a long time.')
        sheetNoteBlocking2.SetFont(bolded)
        mkDtSetSiz.Add(sheetNoteBlocking2, pos=(gRow, 0), span=(1, 5), flag=wx.LEFT|wx.BOTTOM, border=5)

        gRow += 1
        mkDtSetSiz.Add(wx.StaticLine(self), pos=(gRow, 0), span=(1, 5), flag=wx.EXPAND)
        gRow += 1
        mkDtSetSiz.Add(wx.StaticLine(self), pos=(gRow, 0), span=(1, 5), flag=wx.EXPAND)

        gRow += 1

        self.ckPreview = wx.CheckBox(self, label="Preview, Rows:")
        mkDtSetSiz.Add(self.ckPreview, pos=(gRow, 0), span=(1, 1),
            flag=wx.ALIGN_LEFT|wx.LEFT|wx.BOTTOM, border=5)
        self.ckPreview.SetValue(True)
        self.ckPreview.Bind(wx.EVT_CHECKBOX, self.onCkPreview)

        self.spinPvwRows = wx.SpinCtrl(self, -1, '', size=(50,-1))
        self.spinPvwRows.SetRange(1,100)
        self.spinPvwRows.SetValue(10)
        mkDtSetSiz.Add(self.spinPvwRows, pos=(gRow, 1), span=(1, 1),
            flag=wx.ALIGN_LEFT|wx.LEFT|wx.BOTTOM, border=5)

#        mkDtSetSiz.Add(wx.StaticText(self, -1, ' Rows'),
#                     pos=(gRow, 2), flag=wx.ALIGN_LEFT|wx.LEFT|wx.BOTTOM, border=5)

        self.btnMake = wx.Button(self, label="Make", size=(90, 28))
        self.btnMake.Bind(wx.EVT_BUTTON, lambda evt: self.onClick_BtnMake(evt))
        mkDtSetSiz.Add(self.btnMake, pos=(gRow, 3), flag=wx.LEFT|wx.BOTTOM, border=5)
        self.btnCancel = wx.Button(self, label="Cancel", size=(90, 28))
        self.btnCancel.Bind(wx.EVT_BUTTON, lambda evt: self.onClick_BtnCancel(evt))
        mkDtSetSiz.Add(self.btnCancel, pos=(gRow, 4), flag=wx.LEFT|wx.BOTTOM, border=5)

        gRow += 1
        self.tcProgress = wx.TextCtrl(self, -1, style=wx.TE_MULTILINE|wx.TE_READONLY)
        mkDtSetSiz.Add(self.tcProgress, pos=(gRow, 0), span=(4, 5),
            flag=wx.ALIGN_LEFT|wx.TOP|wx.LEFT|wx.BOTTOM|wx.EXPAND, border=5)
        gRow += 1 # space for the 4 grid rows for tcProgress
        gRow += 1
        gRow += 1

        # offer some estimate diagnostics
        self.tcProgress.AppendText('Estimate for full dataset: ')
        fEstSecsPerQuery = 0.2
        iNumRows = self.bkDict['CtOfDays'] * self.bkDict['NumberOfTimeSlicesPerDay']
        if self.sourceTable == 'OutputSheets':
            self.iTotRowEstimate = iNumRows
            self.tcProgress.AppendText(str(self.iTotRowEstimate) + ' rows; ')
            iNumQueries = self.shDict['CtAggCols'] + 1
            fNumSecsWorking = iNumRows * iNumQueries * fEstSecsPerQuery
            self.tcProgress.AppendText('working time, %d seconds ' % fNumSecsWorking)
        else: # book
            self.tcProgress.AppendText('%d rows in each of %d sheets' % (iNumRows, len(self.lShs)))
            self.iTotRowEstimate = iNumRows * len(self.lShs)
            self.tcProgress.AppendText(', for a total of %d rows; ' % self.iTotRowEstimate)
            iTotQueries = 0
            for shDict in self.lShs:
                iTotQueries += (shDict['CtAggCols'] + 1)
            fNumSecsWorking = iNumRows * iTotQueries * fEstSecsPerQuery
            self.tcProgress.AppendText('Estimated working time for whole dataset, %d seconds ' % fNumSecsWorking)
        self.SetSizer(mkDtSetSiz)
        self.SetAutoLayout(1)

    def onClick_BtnGetDir(self, event):
        """
        Get the directory to save the file we are about to make
        """
        dlg = wx.DirDialog(self, "Choose a directory:",
                           style=wx.DD_DEFAULT_STYLE
                           #| wx.DD_DIR_MUST_EXIST
                           #| wx.DD_CHANGE_DIR
                           )
        if dlg.ShowModal() == wx.ID_OK:
            self.tcDir.SetValue(dlg.GetPath())
#            print "You chose %s" % dlg.GetPath()
        dlg.Destroy()

    def onCkPreview(self, evt):
        if self.ckPreview.GetValue():
            self.spinPvwRows.Enable(True)
        else:
            self.spinPvwRows.Enable(False)

    def giveRBInfo(self, event):
        """
        Give the user some information about this output option
        """
        stMsg = ''
        if self.rbExcel.GetValue():
            stMsg = ' Excel output is only available on Windows systems, and only ' \
                'if you have Excel installed. Only Excel allows making a multi-Sheet Book. ' \
                'With other options, each Sheet becomes a separate file. \r' \
                ' With Excel, you will see the dataset as it builds. Other options do not show.'
        if self.rbTabDelim.GetValue():
            stMsg = ' With tab delimited output, each Sheet becomes a separate file. If you ' \
                ' make a whole Book at once, the Sheets will be a set of files, within a ' \
                'folder named for the Book.\r' \
                ' You will not see the dataset as it builds. It builds as a file (or files) on disk.'
        if self.rbCommaDelim.GetValue():
            stMsg = ' With CSV output, each Sheet becomes a separate file. If you ' \
                ' make a whole Book at once, the Sheets will be a set of files, within a Book ' \
                'folder.\r' \
                ' If you have a comma within any data item, that item will have quotes around it in ' \
                'the output file, to prevent the comma from breaking that row into a new ' \
                'column at that point.\r' \
                'You will not see the dataset as it builds. It builds as a file (or files) on disk.'
        self.tcOutputOptInfo.SetValue(stMsg)
        
    def onClick_BtnMake(self, event):
        """
        Make the dataset
        """
        # test if our file save info is valid
        stDir = self.tcDir.GetValue()
        if not os.path.exists(stDir):
            stDir = os.path.expanduser('~') # user doesn't like? next time choose one
            self.tcDir.SetValue(stDir)
        stBaseName = self.tcBaseName.GetValue()
#        if stBaseName[0] == '(': # assume '(default filename)' was sitting there
#            stBaseName = self.stItemName #default
#        stBaseName = "".join(x for x in stBaseName if x.isalnum())
#        self.tcBaseName.SetValue(stBaseName)
        stSavePath = os.path.join(stDir, stBaseName)
        print "stSavePath:", stSavePath
        if self.rbExcel.GetValue():
            stSavePath = stSavePath + '.xlsx'
        if self.rbTabDelim.GetValue():
            stSavePath = stSavePath + '.txt'
        if self.rbCommaDelim.GetValue():
            stSavePath = stSavePath + '.csv'
        if os.path.isfile(stSavePath):
            stMsg = '"' + stSavePath + '" already exists. Overwrite?'
            dlg = wx.MessageDialog(self, stMsg, 'File Exists', wx.YES_NO | wx.ICON_QUESTION)
            result = dlg.ShowModal()
            dlg.Destroy()
#            print "result of Yes/No dialog:", result
            if result == wx.ID_YES:
                try:
                    os.remove(stSavePath)
                except:
                    wx.MessageBox("Can't delete old file. Is it still open?", 'Info',
                        wx.OK | wx.ICON_INFORMATION)
                    return
            else:
                return

        if self.rbExcel.GetValue():
            self.makeExcel()
            return # end of if Excel

        else: # one of the text formats
            if self.sourceTable == 'OutputSheets': # going to create only one file, from this one sheet
                shDict = self.lShs[0]
                self.makeTextFile(0, shDict) # explictily pass the sheet dictionary
                return
            if self.sourceTable == 'OutputBooks': # process the whole book
                if self.bkDict['PutAllOutputRowsInOneSheet'] == 1:
                    self.makeTextFile(1, None) # flag to compile the whole book into one file, no shDict needed
                else:
                    iNumSheets = len(self.lShs)
                    iSheetCt = 0
                    for shDict in self.lShs:
                        iSheetCt += 1
                        stMsg = 'Doing sheet "' + shDict['WorksheetName'] + '", ' + str(iSheetCt) + ' of ' + str(iNumSheets)
                        self.tcOutputOptInfo.SetValue(stMsg)
                        self.makeTextFile(0, shDict) # explictily pass each sheet dictionary
                return
            return # end of if text file(s)    

    def makeExcel(self):
        """
        Make an Excel workbook
        """
        if hasCom == False: # we tested for this at the top of this module
            wx.MessageBox('This operating system cannot make Excel files', 'Info',
                wx.OK | wx.ICON_INFORMATION)
            return
        try:
            oXL = win32com.client.Dispatch("Excel.Application")
            oXL.Visible = 1
        except:
            wx.MessageBox('Excel is not on this computer', 'Info',
                wx.OK | wx.ICON_INFORMATION)
            return
        bXL = oXL.Workbooks.Add()
        #remove any extra sheets
        while bXL.Sheets.Count > 1:
#                    print "Workbook has this many sheets:", bXL.Sheets.Count
            bXL.Sheets(1).Delete()
        shXL = bXL.Sheets(1)
        boolSheetReady = True
        # before we go any further, try saving file
        stDir = self.tcDir.GetValue()
        stBaseName = self.tcBaseName.GetValue()
        stSavePath = os.path.join(stDir, stBaseName) + '.xlsx'

        if os.path.isfile(stSavePath):
            stMsg = '"' + stSavePath + '" already exists. Overwrite?'
            dlg = wx.MessageDialog(self, stMsg, 'File Exists', wx.YES_NO | wx.ICON_QUESTION)
            result = dlg.ShowModal()
            dlg.Destroy()
#            print "result of Yes/No dialog:", result
            if result == wx.ID_YES:
                try:
                    os.remove(stSavePath)
                except:
                    wx.MessageBox("Can't delete old file. Is it still open?", 'Info',
                        wx.OK | wx.ICON_INFORMATION)
                    return
            else:
                return

        try:
            bXL.SaveAs(stSavePath) # make sure there's nothing invalid about the filename
        except:
            wx.MessageBox('Can not save file "' + stSavePath + '"', 'Info',
                wx.OK | wx.ICON_INFORMATION)
            return
        self.tcOutputOptInfo.SetValue(' Creating Excel file "' + stSavePath + '"\n')


        for shDict in self.lShs:
            if boolSheetReady == False:
                self.tcOutputOptInfo.SetValue(self.tcOutputOptInfo.GetValue() + 'Sheet "' + shXL.Name + '"\n')
                print shXL.Name
                sPrevShNm = shXL.Name
                #shXL = bXL.Sheets.Add() # this works
                #print shXL.Name # this works, and is the expected new sheet 1st in the book
                #shXL.Move(After=bXL.Sheets(sPrevShNm)) # this moves sheet to a new book, then crashes
                oXL.Worksheets.Add(After=oXL.Sheets(sPrevShNm)) # creats sheet, but 1st in the book
                #worksheets.Add(After=worksheets(worksheets.Count)) # creats sheet, but 1st in the book 
                shXL = oXL.ActiveSheet
                print shXL.Name
                boolSheetReady = True
                
            iSheetID = shDict['ID']
            dsRow = 1
            dsCol = 1
            # name the worksheet
#                    shXL = bXL.Sheets(1)
            shXL.Name = shDict['WorksheetName']
            boolSheetReady = False # sheet has been used, next loop will add a new one
            #set up the column headings
            stSQL = "SELECT Count(ID) AS CountOfID, ColumnHeading, " \
                "AggType, Format_Excel, ListingOrder " \
                "FROM OutputColumns GROUP BY WorksheetID, ColumnHeading, " \
                "AggType, Format_Excel, ListingOrder " \
                "HAVING WorksheetID = ? " \
                "ORDER BY ListingOrder;"
            scidb.curD.execute(stSQL, (iSheetID,))
            recs = scidb.curD.fetchall()
            for rec in recs:
                shXL.Cells(dsRow,rec['ListingOrder']).Value = rec['ColumnHeading']
                #apply column formats
                if rec['Format_Excel'] != None:
                    try:
                        shXL.Columns(rec['ListingOrder']).NumberFormat = rec['Format_Excel']
                    except:
                        print 'Invalid Excel format, column ' + str(rec['ListingOrder'])

            if self.ckPreview.GetValue():
                iNumRowsToPreview = self.spinPvwRows.GetValue()
            else:
                iNumRowsToPreview = 1000000 # improve this
            iPreviewCt = 0

            # use the row generator
#                    waitForExcel = wx.BusyInfo("Making Excel output")
            sheetRows = scidb.generateSheetRows(iSheetID, formatValues = False)
            for dataRow in sheetRows:
                # yielded object is list with as many members as there are grid columns
                iPreviewCt += 1
                if iPreviewCt > iNumRowsToPreview:
                    break
                dsRow += 1
                for dsCol in range(len(dataRow)):
                    shXL.Cells(dsRow,dsCol+1).Value = dataRow[dsCol]
#                    del waitForExcel    
        shXL.Columns.AutoFit()
        bXL.Save() 
#                oXL.Cells(1,1).Value = "Hello"

    def makeTextFile(self, combineSheets, shDict):
        """
        Make a text file
        """
#        wx.MessageBox('Called makeTextFile function', 'Info',
#            wx.OK | wx.ICON_INFORMATION)
        stDir = self.tcDir.GetValue()
        stBaseName = self.tcBaseName.GetValue()
        stBasePath = os.path.join(stDir, stBaseName)
        if combineSheets == 0: # not making the whole book into one file, use base name for folder and add filename
            if not os.path.exists(stBasePath):
                try:
                    os.makedirs(stBasePath)
                except:
                    wx.MessageBox('Can not create folder "' + stBasePath + '"', 'Info',
                        wx.OK | wx.ICON_INFORMATION)
                    return
            stSavePath = os.path.join(stBasePath, shDict['WorksheetName'])

        else:
            stSavePath = stBasePath
        if self.rbTabDelim.GetValue():
            stSavePath = stSavePath + '.txt'
        if self.rbCommaDelim.GetValue():
            stSavePath = stSavePath + '.csv'
        if os.path.isfile(stSavePath):
            stMsg = '"' + stSavePath + '" already exists. Overwrite?'
            dlg = wx.MessageDialog(self, stMsg, 'File Exists', wx.YES_NO | wx.ICON_QUESTION)
            result = dlg.ShowModal()
            dlg.Destroy()
#            print "result of Yes/No dialog:", result
            if result == wx.ID_YES:
                try:
                    os.remove(stSavePath)
                except:
                    wx.MessageBox("Can't delete old file. Is it still open?", 'Info',
                        wx.OK | wx.ICON_INFORMATION)
                    return
            else:
                return
        try: # before we go any further
            # make sure there's nothing invalid about the filename
            fOut = open(stSavePath, 'wb') 
        except:
            wx.MessageBox('Can not create file "' + stSavePath + '"', 'Info',
                wx.OK | wx.ICON_INFORMATION)
            return

        if self.rbTabDelim.GetValue():
            wr = csv.writer(fOut, delimiter='\t', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        if self.rbCommaDelim.GetValue():
            wr = csv.writer(fOut, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        self.tcProgress.SetValue('Setting up column headings')
        # item unless book is specified to go all in one block (not implemented yet)
        # get the number of columns
        stSQL = 'SELECT MAX(CAST(ListingOrder AS INTEGER)) AS Ct ' \
            'FROM OutputColumns WHERE WorksheetID = ?'
        scidb.curD.execute(stSQL, (shDict['ID'],))
        rec = scidb.curD.fetchone()
        lColHds = ['' for x in range(rec['Ct'])]
        #set up the column headings
        stSQL = "SELECT Count(ID) AS CountOfID, " \
            "ColumnHeading, AggType, ListingOrder " \
            "FROM OutputColumns " \
            "GROUP BY WorksheetID, ColumnHeading, AggType, ListingOrder " \
            "HAVING WorksheetID = ? " \
            "ORDER BY ListingOrder;"
        scidb.curD.execute(stSQL, (shDict['ID'],))
        recs = scidb.curD.fetchall()
        for rec in recs:
            lColHds[rec['ListingOrder']-1] = rec['ColumnHeading']
        wr.writerow(lColHds)
        lMsg = []
        lMsg.append('')
        lMsg.append('')
        lMsg.append(' rows written to "')
        lMsg.append(stSavePath)
        lMsg.append('".')
        if self.ckPreview.GetValue():
            iNumRowsToDo = self.spinPvwRows.GetValue()
            lMsg[0] = 'Preview of '
            lMsg[1] = str(iNumRowsToDo)
        else:
            iNumRowsToDo = 1000000 # improve this
            lMsg[0] = 'Total of '
        iRowCt = 0
        # use the row generator
        sheetRows = scidb.generateSheetRows(shDict['ID'])
        for dataRow in sheetRows:
            # yielded object is list with as many members as there are columns
            iRowCt += 1
            if iRowCt > iNumRowsToDo:
                break
            self.tcProgress.SetValue('Doing row %d' % iRowCt)
            wx.Yield() # allow window updates to occur
            wr.writerow(dataRow)
            
        lMsg[1] = str(iRowCt)

        fOut.close()
        wx.MessageBox("".join(lMsg), 'Info',
            wx.OK | wx.ICON_INFORMATION)
        return # end of if CSV

    def onClick_BtnCancel(self, event):
        """
        Cancel making the dataset
        """
        self.EndModal(0)
#        wx.MessageBox('Not implemented yet', 'Info',
#            wx.OK | wx.ICON_INFORMATION)
        
    def OnClose(self, event):
        self.Destroy()

class SetupDatasetsPanel(wx.Panel):
    def __init__(self, parent, id):
        wx.Panel.__init__(self, parent, id)
        self.InitUI()

    def InitUI(self):
        #horizontal split means the split goes across
        #vertical split means the split goes up and down
        hSplit = wx.SplitterWindow(self, -1)
        setupPanel = wx.Panel(hSplit, -1)
        vSplit = wx.SplitterWindow(setupPanel, -1)
        treeViewPanel = wx.Panel(vSplit, -1)

        self.dsTree = wx.TreeCtrl(treeViewPanel, 1, wx.DefaultPosition, (-1,-1), wx.TR_HAS_BUTTONS|wx.TR_LINES_AT_ROOT)
        self.dsRootID = self.dsTree.AddRoot('DataSets')
#        print "dsRootID:", self.dsRootID
        # for every tree item except the root, the PyData is a 2-tuple: ([Table Name], [Record ID in that table])
        self.dsTree.SetPyData(self.dsRootID, ('(no table)',0))
        # build out any branches of the tree
        stSQL = "SELECT ID, BookName FROM OutputBooks;"
        scidb.curD.execute(stSQL)
        bookRecs = scidb.curD.fetchall()
        bookDict = {}
        for bookRec in bookRecs: # get them all now because another query to the same DB will stop the iterator
            self.bookBranchID = self.dsTree.AppendItem(self.dsRootID, bookRec["BookName"])
            # PyData is a 2-tuple: ([Table Name], [Record ID in that table])
            self.dsTree.SetPyData(self.bookBranchID, ('OutputBooks', bookRec["ID"]))
            bookDict[bookRec["ID"]] = [bookRec["BookName"], copy.copy(self.bookBranchID)]
        # iterate over the Books dictionary to get each one's Sheets
        for bookRecID in bookDict:
            stSQL = "SELECT ID, WorksheetName, ListingOrder FROM OutputSheets WHERE BookID = ?;"
            scidb.curD.execute(stSQL, (bookRecID,))
            sheetRecs = scidb.curD.fetchall()
            sheetDict = {}
            bookInfoList = bookDict[bookRecID]
#                print "retrieved bookInfoList:", bookInfoList
            bookBranchID = bookInfoList[1]
#                print "retrieved bookBranchID:", bookBranchID
            for sheetRec in sheetRecs: # get them all now because another query to the same DB will stop the iterator
                self.sheetBranchID = self.dsTree.AppendItem(bookBranchID, sheetRec["WorksheetName"])
                # PyData is a 2-tuple: ([Table Name], [Record ID in that table])
                self.dsTree.SetPyData(self.sheetBranchID, ('OutputSheets', sheetRec["ID"]))
                sheetDict[sheetRec["ID"]] = [sheetRec["WorksheetName"], copy.copy(self.sheetBranchID)]
            for sheetRecID in sheetDict:
                stSQL = "SELECT ID, ColumnHeading, ListingOrder FROM OutputColumns WHERE WorksheetID = ?;"
                scidb.curD.execute(stSQL, (sheetRecID,))
                colRecs = scidb.curD.fetchall()
                colDict = {}
                sheetInfoList = sheetDict[sheetRecID]
                sheetBranchID = sheetInfoList[1]
                for colRec in colRecs:  # get them all now, another query to the same DB will stop the iterator
                    self.colBranchID = self.dsTree.AppendItem(sheetBranchID, colRec["ColumnHeading"])
                    # PyData is a 2-tuple: ([Table Name], [Record ID in that table])
                    self.dsTree.SetPyData(self.colBranchID, ('OutputColumns', colRec["ID"]))
                    colDict[colRec["ID"]] = [colRec["ColumnHeading"], copy.copy(self.colBranchID)]

        self.dsTree.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged, id=1)
        self.tree_item_clicked = None
        # 1. Register source's EVT_s to invoke pop-up menu launcher
        wx.EVT_TREE_ITEM_RIGHT_CLICK(self.dsTree, -1, self.dsTreeRightClick)

        trPnlSiz = wx.BoxSizer(wx.VERTICAL)
        trPnlSiz.Add(self.dsTree, 1, wx.EXPAND)
        treeViewPanel.SetSizer(trPnlSiz)

        self.detailsPanel = wx.Panel(vSplit, -1)
        # SetBackgroundColour below is a test that this panel background does not show
        # but instead all padding done within the enclosed panel
        self.detailsPanel.SetBackgroundColour(wx.BLUE)
        self.detailsLabel = wx.StaticText(self.detailsPanel, -1, "This will have the details")
        self.detSiz = wx.BoxSizer(wx.VERTICAL)
        self.detSiz.Add(self.detailsLabel, 1, wx.EXPAND)
        self.detailsPanel.SetSizer(self.detSiz)
        
        vSplit.SplitVertically(treeViewPanel, self.detailsPanel)
        hSiz = wx.BoxSizer(wx.HORIZONTAL)
        hSiz.Add(vSplit, 1, wx.EXPAND)
        setupPanel.SetSizer(hSiz)
        
        self.previewPanel = scrolled.ScrolledPanel(hSplit, -1)
        self.previewPanel.SetBackgroundColour(wx.WHITE) # this overrides color of enclosing panel
        pvwSiz = wx.GridBagSizer(1, 1)
        gRow = 0
        self.pvwLabel = wx.StaticText(self.previewPanel, -1, 'Dataset preview below')
        pvwSiz.Add(self.pvwLabel, pos=(gRow, 0), span=(1, 3), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)

        gRow += 1
        pvwSiz.Add(wx.StaticLine(self.previewPanel), pos=(gRow, 0), span=(1, 3), flag=wx.EXPAND)
        
        gRow += 1
        self.pvwGrid = wx.grid.Grid(self.previewPanel, -1)
        self.pvwGrid.CreateGrid(0, 0)

        # hide row and column labels, the numbers down the left and the letters across the top
        self.pvwGrid.SetRowLabelSize(0)
        self.pvwGrid.SetColLabelSize(0)

        pvwSiz.Add(self.pvwGrid, pos=(gRow, 0), span=(1, 5), flag=wx.EXPAND|wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        pvwSiz.AddGrowableCol(4)
        pvwSiz.AddGrowableRow(gRow)

        self.previewPanel.SetSizer(pvwSiz)
        self.previewPanel.SetAutoLayout(1)
        self.previewPanel.SetupScrolling()

        hSplit.SplitHorizontally(setupPanel, self.previewPanel)

        vSiz = wx.BoxSizer(wx.VERTICAL)
        vSiz.Add(hSplit, 1, wx.EXPAND)
        self.SetSizer(vSiz)        

    def OnSelChanged(self, event):
        print "OnSelChanged"
#        self.newGridRow()
        item = event.GetItem()
        try: # event sometimes fires twice when new records created; following prevents errors caused by dead objects
            if self.dsInfoPnl:
#                print "dsInfoPnl exists"
                if self.dsInfoPnl.correspondingTreeItem:
#                    print "dsInfoPnl.correspondingTreeItem exists"
                    if self.dsInfoPnl.correspondingTreeItem == item:
#                        print "panel already shows the correct item"
                        return # panel already shows the correct item
        except:
            pass
#        self.detailsLabel.SetLabel(self.dsTree.GetItemText(item))
#        print "ItemData:", self.dsTree.GetItemData(item)
        # check for invalid column overlap
        errCk = scidb.ckDupOutputColumnsNotAggregate()
        if errCk != None:
            wx.MessageBox(errCk[0], errCk[1],
                wx.OK | wx.ICON_INFORMATION)
        # check for mismatches in otherwise valid column overlap
        errCk = scidb.ckDupOutputColumnsMismatch()
        if errCk != None:
            wx.MessageBox(errCk[0], errCk[1],
                wx.OK | wx.ICON_INFORMATION)
        ckPyData = self.dsTree.GetPyData(item)
        print "PyData:", ckPyData
        self.detailsPanel.DestroyChildren()
        if ckPyData[1] == 0:
            self.dsInfoPnl = InfoPanel_DataSets(self.detailsPanel, wx.ID_ANY)
        if ckPyData[0] == "OutputBooks":
            self.dsInfoPnl = InfoPanel_Book(self.detailsPanel, ckPyData)
        if ckPyData[0] == "OutputSheets":
            self.dsInfoPnl = InfoPanel_Sheet(self.detailsPanel, ckPyData)
        if ckPyData[0] == "OutputColumns":
            self.dsInfoPnl = InfoPanel_Column(self.detailsPanel, ckPyData)
            
        self.detSiz.Add(self.dsInfoPnl, 1, wx.EXPAND)
        self.dsInfoPnl.correspondingTreeItem = item
        self.detailsPanel.Layout()

        # set up the grid
        # first, erase it
        nR = self.pvwGrid.GetNumberRows()
        nC = self.pvwGrid.GetNumberCols()
        if nR > 0:
            self.pvwGrid.DeleteRows(numRows=nR)
        if nC > 0:
            self.pvwGrid.DeleteCols(numCols=nC)

        # build grid based on what is selected in the tree
        stPvwTopMsg = 'preview unavailable'
        if ckPyData[1] == 0: # 'DataSets' root of the tree
            stPvwTopMsg = 'Preview will appear below when you click on a tree item above'
        if ckPyData[0] == "OutputBooks":
            # look for the first sheet in this book
            stSQL = """SELECT ID as SheetID, WorksheetName, ListingOrder
                FROM OutputSheets
                WHERE BookID = ?
                ORDER BY ListingOrder, ID;"""
            scidb.curD.execute(stSQL, (ckPyData[1],))
            rec = scidb.curD.fetchone()
            if rec == None:
                stPvwTopMsg = 'No sheets in this book yet'
            else:
#                stPvwTopMsg = 'Preview of sheet %(shNum)d, "%(shName)s".' % {"shNum": rec['ListingOrder'], "shName": rec['WorksheetName']}
                sB = 'Preview of sheet' \
                    ' %(shNum)d, "%(shName)s".'
                dFm = {"shNum": rec['ListingOrder'], "shName": rec['WorksheetName']}
#                stPvwTopMsg = 'Preview of sheet %(shNum)d, "%(shName)s".' % dFm
                stPvwTopMsg = sB % dFm
                self.sheetID = rec['SheetID']
                self.insertPreviewGridHeaders(self.sheetID)

        if ckPyData[0] == "OutputSheets":
            # get this sheet
            self.sheetID = ckPyData[1]
            stSQL = """SELECT ID as SheetID, WorksheetName, ListingOrder
                FROM OutputSheets
                WHERE ID = ?
                ORDER BY ListingOrder, ID;"""
            scidb.curD.execute(stSQL, (self.sheetID,))
            rec = scidb.curD.fetchone()
            stPvwTopMsg = 'Preview of sheet %(shNum)d, "%(shName)s".' % {"shNum": rec['ListingOrder'], "shName": rec['WorksheetName']}
            self.insertPreviewGridHeaders(self.sheetID)
        if ckPyData[0] == "OutputColumns":
            # get this column's sheet
            stSQL = """SELECT OutputSheets.ID AS SheetID,
                OutputSheets.WorksheetName,
                OutputSheets.ListingOrder
                FROM OutputSheets
                WHERE (((OutputSheets.ID) In
                (SELECT OutputColumns.WorksheetID
                FROM OutputColumns
                WHERE (((OutputColumns.ID)=?)))))
                ORDER BY OutputSheets.ListingOrder, OutputSheets.ID;"""
            scidb.curD.execute(stSQL, (ckPyData[1],))
            rec = scidb.curD.fetchone()
            stPvwTopMsg = 'Preview of sheet %(shNum)d, "%(shName)s".' % {"shNum": rec['ListingOrder'], "shName": rec['WorksheetName']}
            self.sheetID = rec['SheetID']
            self.insertPreviewGridHeaders(self.sheetID)

        self.pvwLabel.SetLabel(stPvwTopMsg)
        self.pvwGrid.AutoSize()
        self.previewPanel.SetupScrolling()

    def insertPreviewGridHeaders(self, sheetID):
        stSQL = "SELECT Max(CAST(ListingOrder AS INTEGER)) AS MaxCol " \
            "FROM OutputColumns " \
            "WHERE WorksheetID = ?;"
        scidb.curD.execute(stSQL, (sheetID,))
        rec = scidb.curD.fetchone()
        if rec['MaxCol'] == None:
            self.pvwGrid.AppendRows() # 1 row 
            self.pvwGrid.AppendCols() # 1 column
            self.pvwGrid.SetCellValue(0, 0, '(no columns yet)')
            return
        self.pvwGrid.AppendRows() #1st row for headers
        self.pvwGrid.AppendCols(rec['MaxCol']) # make enough columns
        
        stSQL = """SELECT ID as ColID, ColumnHeading, ListingOrder
            FROM OutputColumns
            WHERE WorksheetID = ?
            ORDER BY ListingOrder, ID;"""
        scidb.curD.execute(stSQL, (sheetID,))
        recs = scidb.curD.fetchall()
        for rec in recs:
            # some headings may overwrite each other, that's what the preview is for
            self.pvwGrid.SetCellValue(0, rec['ListingOrder'] - 1, rec['ColumnHeading'])
            
        # following is still in testing
        # first test as a generator
        sheetRows = scidb.generateSheetRows(self.sheetID)
        iRwCt = 0
        iNumRowsToPreview = 10
        for dataRow in sheetRows:
            # yielded object is list with as many members as there grid columns
            iRwCt += 1
            if iRwCt > iNumRowsToPreview:
                break
            self.pvwGrid.AppendRows()
            iRow = self.pvwGrid.GetNumberRows() - 1 # the new row to fill in is the last row
            for iCol in range(len(dataRow)):
                self.pvwGrid.SetCellValue(iRow, iCol, dataRow[iCol])
            self.Update()
            self.pvwGrid.ForceRefresh
#            self.Refresh()
#            print iRwCt, dataRow
        

    def dsTreeRightClick(self, event):
        self.tree_item_clicked = right_click_context = event.GetItem()
        ckPyData = self.dsTree.GetPyData(self.tree_item_clicked)
        print "PyData from Right Click:", ckPyData
        menu = wx.Menu()
#        for (id,title) in menu_title_by_id.items():
        for (id,title) in treePopMenuItems.items():
            if ckPyData[1] == 0: # the root of the DataSets tree
                if id > 100 and id < 200: # only insert these menu items
                    print "Added to menu (id, title):", id, title
                    menu.Append( id, title )
            if ckPyData[0] == 'OutputBooks': # a Book branch
                if id > 200 and id < 300: # only insert these menu items
                    print "Added to menu (id, title):", id, title
                    menu.Append( id, title )
            if ckPyData[0] == 'OutputSheets': # a Sheet branch
                if id > 300 and id < 400: # only insert these menu items
                    print "Added to menu (id, title):", id, title
                    menu.Append( id, title )
            if ckPyData[0] == 'OutputColumns': # a Column branch
                if id > 400 and id < 500: # only insert these menu items
                    print "Added to menu (id, title):", id, title
                    menu.Append( id, title )

            ### 4. Launcher registers menu handlers with EVT_MENU, on the menu. ###
            wx.EVT_MENU( menu, id, self.MenuSelectionCb )

        ### 5. Launcher displays menu with call to PopupMenu, invoked on the
            #source component, passing event's GetPoint. ###
        self.PopupMenu( menu, event.GetPoint() )
        menu.Destroy() # destroy to avoid mem leak

    def MenuSelectionCb( self, event ):
        # do something
        opID = event.GetId()
        operation = treePopMenuItems[opID]
        print "operation:", operation
        
#        target = self.tree_item_clicked
        target = self.dsTree.GetItemText(self.tree_item_clicked)
        print "target:", target
        treeItemPyData = self.dsTree.GetPyData(self.tree_item_clicked)
        print "PyData of tree item right-clicked:", treeItemPyData
        # treeItemPyData (a 2-tuple; [table],[recID]) provides the record ID every
        # level below Book needs in order to create a new record.
        # e.g. Book ID for creating a Sheet in that book, Sheet ID for creating a Column in that sheet
        if opID == ID_ADD_BOOK:
            print "operation is to add a new book"
            dia = Dialog_Book(self, wx.ID_ANY)
            # the dialog contains an 'InfoPanel_Book' named 'pnl'
            result = dia.ShowModal()
            # dialog is exited using EndModal, and comes back here
            print "Modal dialog result:", result
            # test of pulling things out of the modal dialog
            self.newBookName = dia.pnl.tcBookName.GetValue()
            print "Name of new book, from the Modal:", self.newBookName
            self.newRecID = dia.pnl.newRecID
            print "record ID from the Modal:", self.newRecID
            dia.Destroy()
            if result == 1: # new record successfully created
                # create a new branch on the tree
#                self.bookBranchID = self.dsTree.AppendItem(self.dsRootID, self.newBookName)
                self.bookBranchID = self.dsTree.AppendItem(self.tree_item_clicked, self.newBookName)
                self.dsTree.SetPyData(self.bookBranchID, ('OutputBooks', self.newRecID))
                # select it
                self.dsTree.SelectItem(self.bookBranchID)
                #generates wxEVT_TREE_SEL_CHANGING and wxEVT_TREE_SEL_CHANGED events
                # wxEVT_TREE_SEL_CHANGED displays the information in the details panel
            return

        if opID == ID_ADD_SHEET:
            print "operation is to add a new sheet"
            dia = Dialog_Sheet(self, wx.ID_ANY, parentTableRec = treeItemPyData)
            # the dialog contains an 'InfoPanel_Sheet' named 'pnl'
            result = dia.ShowModal()
            # dialog is exited using EndModal, and comes back here
            print "Modal dialog result:", result
            # test of pulling things out of the modal dialog
            self.newSheetName = dia.pnl.tcSheetName.GetValue()
            print "Name of new sheet, from the Modal:", self.newSheetName
            self.newRecID = dia.pnl.newRecID
            print "record ID from the Modal:", self.newRecID
            dia.Destroy()
            if result == 1: # new record successfully created
                # create a new branch on the tree
                self.sheetBranchID = self.dsTree.AppendItem(self.tree_item_clicked, self.newSheetName)
                self.dsTree.SetPyData(self.sheetBranchID, ('OutputSheets', self.newRecID))
                # select it
                self.dsTree.SelectItem(self.sheetBranchID)
                #generates wxEVT_TREE_SEL_CHANGING and wxEVT_TREE_SEL_CHANGED events
                # wxEVT_TREE_SEL_CHANGED displays the information in the details panel
            return

        if opID == ID_ADD_COL:
            print "operation is to add a new column"
            dia = Dialog_Column(self, wx.ID_ANY, parentTableRec = treeItemPyData)
            # the dialog contains an 'InfoPanel_Column' named 'pnl'
            result = dia.ShowModal()
            # dialog is exited using EndModal, and comes back here
            print "Modal dialog result:", result
            # test of pulling things out of the modal dialog
            self.newColHead = dia.pnl.tcColHead.GetValue()
            print "Heading for new Column, from the Modal:", self.newColHead
            self.newRecID = dia.pnl.newRecID
            print "record ID from the Modal:", self.newRecID
            dia.Destroy()
            if result == 1: # new record successfully created
                # create a new branch on the tree
                self.colBranchID = self.dsTree.AppendItem(self.tree_item_clicked, self.newColHead)
                self.dsTree.SetPyData(self.colBranchID, ('OutputColumns', self.newRecID))
                # select it
                self.dsTree.SelectItem(self.colBranchID)
                #generates wxEVT_TREE_SEL_CHANGING and wxEVT_TREE_SEL_CHANGED events
                # wxEVT_TREE_SEL_CHANGED displays the information in the details panel
            return

        if opID == ID_MAKE_BOOK or opID == ID_MAKE_SHEET:
            print "operation is to make the dataset"
##
            # test if there is nothing to output
            # Book with no Sheets
            if treeItemPyData[0] == 'OutputBooks':
                stSQL = 'SELECT Count(ID) AS Ct FROM OutputSheets WHERE BookID = ?;'
                scidb.curD.execute(stSQL, (treeItemPyData[1],))
                rec = scidb.curD.fetchone()
                if rec['Ct'] == 0:
                    wx.MessageBox('Book has no Sheets. Nothing to output.', 'Info',
                        wx.OK | wx.ICON_INFORMATION)
                    return
                # Book has Sheets but check if they have no columns
                stSQL = 'SELECT Count(OutputColumns.ID) AS Ct ' \
                    'FROM OutputColumns LEFT JOIN OutputSheets ' \
                    'ON OutputColumns.WorksheetID = OutputSheets.ID ' \
                    'WHERE (((OutputSheets.BookID)=?));'
                scidb.curD.execute(stSQL, (treeItemPyData[1],))
                rec = scidb.curD.fetchone()
                if rec['Ct'] == 0:
                    wx.MessageBox('Book Sheets have no Columns. Nothing to output.', 'Info',
                        wx.OK | wx.ICON_INFORMATION)
                    return                
            # Sheet with no Columns
            if treeItemPyData[0] == 'OutputSheets':
                stSQL = 'SELECT Count(ID) AS Ct FROM OutputColumns WHERE WorksheetID = ?;'
                scidb.curD.execute(stSQL, (treeItemPyData[1],))
                rec = scidb.curD.fetchone()
                if rec['Ct'] == 0:
                    wx.MessageBox('Sheet has no Columns. Nothing to output.', 'Info',
                        wx.OK | wx.ICON_INFORMATION)
                    return
##
            dia = Dialog_MakeDataset(self, wx.ID_ANY, parentTableRec = treeItemPyData)
            result = dia.ShowModal()
            # dialog is exited using EndModal, and comes back here
            print "Modal dialog result:", result
            return
        
        wx.MessageBox('Not implemented yet', 'Info',
                    wx.OK | wx.ICON_INFORMATION)

    def onButton(self, event, strLabel):
        """"""
        print ' You clicked the button labeled "%s"' % strLabel

#    def onClick_BtnNotWorkingYet(self, event, strLabel):
#        wx.MessageBox('"Hello" is not implemented yet', 'Info', 
#            wx.OK | wx.ICON_INFORMATION)

class SetupDatasetsFrame(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title)
        self.InitUI()
        self.SetSize((750, 600))
#        self.Centre()
        self.Show(True)

    def InitUI(self):
        framePanel = SetupDatasetsPanel(self, wx.ID_ANY)

def main():
    app = wx.App(redirect=False)
    dsFrame = SetupDatasetsFrame(None, wx.ID_ANY, 'Set Up Datasets')
    app.MainLoop() 

if __name__ == '__main__':

    #Add support for when a program which uses multiprocessing has been frozen to produce a Windows executable
    # following line must be immediately after 'if __name__ == '__main__':'
    multiprocessing.freeze_support()
    # Create the queues
    taskQueue = multiprocessing.Queue()
    doneQueue = multiprocessing.Queue()

    Processes = [ ]
    # start the worker process here
#    process = multiprocessing.Process(target=MyFrame.worker, args=(taskQueue, doneQueue))
#    process.start()
#    Processes.append(process)

    main()
