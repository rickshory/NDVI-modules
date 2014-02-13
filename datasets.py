import wx, sqlite3, datetime, copy
import os, sys, re, cPickle
import scidb
import wx.lib.scrolledpanel as scrolled

ID_ADD_BOOK = 101
ID_ADD_SHEET = 201
ID_DEL_BOOK = 202
ID_ADD_COL = 301
ID_DEL_SHEET = 302
ID_DEL_COL = 402

treePopMenuItems = {ID_ADD_BOOK:'Add a Book',
                    ID_ADD_SHEET:'Add a Sheet to this Book', ID_DEL_BOOK:'Delete this Book',
                    ID_ADD_COL:'Add a Column to this Sheet', ID_DEL_SHEET:'Delete this Sheet',
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
        else: # in the details panel to view/edit the information for an existing record
            # selected tree item is the node to view/edit
            self.sourceTable = treePyData[0] # should be 'OutputSheets'
            self.recID = treePyData[1] # the record ID in that table
            self.parentTable = 'OutputBooks' # the parent table
            stSQL = "SELECT BookID FROM OutputSheets WHERE ID = ?;"
            scidb.curD.execute(stSQL, (self.recID,))
            rec = scidb.curD.fetchone()
            self.parentRecID = rec['BookID'] # the foreign key ID in the parent table

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

#        parObjClass = self.GetParent().GetClassName()
#        print "Parent object class:", parObjClass
#        if parObjClass == 'wxDialog':
#            print "in the Dialog, don't try to set up values"
#        else:
        if self.recID:
            print "Source Table:", self.sourceTable, ", Record ID:", self.recID
            self.fillSheetPanelControls()
        else:
            print "no recID in Sheet panel, will not initialize values"
        self.SetSizer(shPnlSiz)
        self.SetAutoLayout(1)
        self.SetupScrolling()

    def fillSheetPanelControls(self):
#        stSQL = """
#        SELECT BookID,
#        WorksheetName, DataSetNickname, ListingOrder
#        FROM OutputSheets WHERE ID = ?
#        """
        stSQL = "SELECT * FROM OutputSheets WHERE ID=?"
        scidb.curD.execute(stSQL, (self.recID,))
        rec = scidb.curD.fetchone()
        self.tcSheetName.SetValue(rec['WorksheetName'])
        self.tcNickname.SetValue(rec['DataSetNickname'])
        self.tcListingOrder.SetValue('%d' % rec['ListingOrder'])

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
            stSQL = "SELECT MAX(OutputSheets.ListingOrder) AS MaxLstOrd FROM OutputSheets WHERE BookID = ?;"
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
            wx.MessageBox('Undoing any edits', 'Undo', 
                wx.OK | wx.ICON_INFORMATION)
            self.fillSheetPanelControls()
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
        else: # in the details panel to view/edit the information for an existing record
            # selected tree item is the node to view/edit
            self.sourceTable = treePyData[0] # should be 'OutputColumns'
            self.recID = treePyData[1] # the record ID in that table
            self.parentTable = 'OutputSheets' # the parent table
            stSQL = "SELECT WorksheetID FROM OutputColumns WHERE ID = ?;"
            scidb.curD.execute(stSQL, (self.recID,))
            rec = scidb.curD.fetchone()
            self.parentRecID = rec['WorksheetID'] # the foreign key ID in the parent table
    
        print "Initializing InfoPanel_Column ->>>>"
        print "treePyData:", treePyData
        print "self.sourceTable:", self.sourceTable
        print "self.recID:", self.recID
        print "self.parentTable:", self.parentTable
        print "self.parentRecID:", self.parentRecID
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
        
#        CREATE TABLE IF NOT EXISTS "OutputColumns" (
#        "ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL UNIQUE ,
#        "WorksheetID" INTEGER NOT NULL ,
#        "ColumnHeading" VARCHAR(20) NOT NULL,
#        "ColType" VARCHAR(10) NOT NULL,
#        "TimeSystem"  VARCHAR(10) DEFAULT 'Clock Time',
#        "TimeIsInterval" BOOL NOT NULL DEFAULT 0,
#        "IntervalIsFrom" DATETIME,
#        "Constant" VARCHAR(10),
#        "Formula" VARCHAR(1000),
#        "AggType" VARCHAR(5),
#        "AggStationID" INTEGER,
#        "AggDataSeriesID" INTEGER,
#        "ContentsFormat" VARCHAR(20),
#        "ListingOrder" INTEGER NOT NULL,

        if self.parentClassName == "wxDialog": # in the Dialog, create a new DB record
            self.ColDict = dict(ID = None, WorksheetID = None, ColumnHeading = None, ColType = None,
                TimeSystem = None, TimeIsInterval = None, IntervalIsFrom = None,
                Constant = None, Formula = None,
                AggType = None, AggStationID = None, AggDataSeriesID = None,
                ContentsFormat = None, ListingOrder = None)

        else: # an existing record
            stSQL = "SELECT * FROM OutputColumns WHERE ID = ?;"
            scidb.curD.execute(stSQL, (self.recID,))
            rec = scidb.curD.fetchone()
#            ColDict = copy.copy(rec) # this crashes
            self.ColDict = {}
            for recName in rec.keys():
                self.ColDict[recName] = rec[recName]
        print "ColDict:", self.ColDict
              
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
        self.onSelColType(-1) # have to explictly call this 1st time

        gRow += 1
        colPnlSiz.Add(self.colDetailPnl, pos=(gRow, 0), span=(1, 2), flag=wx.EXPAND)
        
        gRow += 1
        colPnlSiz.Add(wx.StaticLine(self), pos=(gRow, 0), span=(1, 3), flag=wx.EXPAND)

# rewrite for Column    
        gRow += 1
        self.btnSave = wx.Button(self, label="Save", size=(90, 28))
        self.btnSave.Bind(wx.EVT_BUTTON, lambda evt: self.onClick_BtnSave(evt))
        colPnlSiz.Add(self.btnSave, pos=(gRow, 0), flag=wx.LEFT|wx.BOTTOM, border=5)
        self.btnCancel = wx.Button(self, label="Cancel", size=(90, 28))
        self.btnCancel.Bind(wx.EVT_BUTTON, lambda evt: self.onClick_BtnCancel(evt))
        colPnlSiz.Add(self.btnCancel, pos=(gRow, 1), flag=wx.LEFT|wx.BOTTOM, border=5)

#        parObjClass = self.GetParent().GetClassName()
#        print "Parent object class:", parObjClass
#        if parObjClass == 'wxDialog':
#            print "in the Dialog, don't try to set up values"
#        else:
        if self.recID:
            print "Source Table:", self.sourceTable, ", Record ID:", self.recID
#            self.fillSheetPanelControls()
        else:
            print "no recID in Sheet panel, will not initialize values"
        self.SetSizer(colPnlSiz)
        self.SetAutoLayout(1)
        self.SetupScrolling()

    def onSelColType(self, event):
        """
        Shows the relevant fields based on Column Type
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
        if colTyp == 'Formula':
            fmlLabel = wx.StaticText(self.colDetailPnl, -1, 'Formula')
            fmlLabel.SetFont(self.bolded)
            colDetailSiz.Add(fmlLabel, pos=(gRow, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.colDetailPnl.SetSizer(colDetailSiz)
        self.colDetailPnl.SetAutoLayout(1)
        self.colDetailPnl.Layout()
        self.Layout()


# rewrite for Column    
    def onClick_BtnSave(self, event):
        # finish rewriting this for Sheets
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

# rewrite for Column    
        try:
            iLstOrd = int(self.tcListingOrder.GetValue())
        except:
            # autocreate, 1 higher than previously existing
            print "self.parentRecID, to use in ListingOrder query:",  self.parentRecID
            stSQL = "SELECT MAX(OutputSheets.ListingOrder) AS MaxLstOrd FROM OutputSheets WHERE BookID = ?;"
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

# rewrite for Column    
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
# rewrite for Column    
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
            wx.MessageBox('Undoing any edits', 'Undo', 
                wx.OK | wx.ICON_INFORMATION)
            self.fillSheetPanelControls()
        return

# rewrite for Column    

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
        
        previewPanel = wx.Panel(hSplit, -1)
        wx.StaticText(previewPanel, -1, "This will be where you preview the dataset as a grid.")
        hSplit.SplitHorizontally(setupPanel, previewPanel)

        vSiz = wx.BoxSizer(wx.VERTICAL)
        vSiz.Add(hSplit, 1, wx.EXPAND)
        self.SetSizer(vSiz)

    def OnSelChanged(self, event):
        print "OnSelChanged"
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
                self.colBranchID = self.dsTree.AppendItem(self.tree_item_clicked, self.newSheetName)
                self.dsTree.SetPyData(self.colBranchID, ('OutputColumns', self.newRecID))
                # select it
                self.dsTree.SelectItem(self.colBranchID)
                #generates wxEVT_TREE_SEL_CHANGING and wxEVT_TREE_SEL_CHANGED events
                # wxEVT_TREE_SEL_CHANGED displays the information in the details panel
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
    main()
