import wx, sqlite3, datetime
import os, sys, re, cPickle
import scidb
import wx.lib.scrolledpanel as scrolled
import wx.lib.newevent

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
    def __init__(self, parent, id, title):
        wx.Dialog.__init__(self, parent, id, title)
        self.InitUI()
        self.SetSize((350, 300))
#        self.SetTitle("Add new Book") # overrides title passed above

    def InitUI(self):
#        pnl = InfoPanel_Book(self, wx.ID_ANY)
        self.pnl = InfoPanel_Book(self)
   
    def OnClose(self, event):
        self.Destroy()
        
class InfoPanel_DataSets(wx.Panel):
    def __init__(self, parent, id):
        wx.Panel.__init__(self, parent, id)
        self.InitUI()
        
    def InitUI(self):
        self.SetBackgroundColour(wx.WHITE) # this overrides color of enclosing panel
        self.infoLabel1 = wx.StaticText(self, -1, 'Right-click the "DataSets" tree to the left to add a Book')
        self.infoLabel2 = wx.StaticText(self, -1, "Within a Book, you'll add one or more Sheets")
        self.infoLabel3 = wx.StaticText(self, -1, "Within a Sheet, you'll set up the Columns")
        self.infoLabel4 = wx.StaticText(self, -1, "When enough information is entered, a preview will appear below.")
        self.infoLabel5 = wx.StaticText(self, -1, "You can go back and edit any level at any time")
        dsPnlSiz = wx.GridBagSizer(1, 1)
        dsPnlSiz.Add(self.infoLabel1, pos=(0, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=10)
        dsPnlSiz.Add(self.infoLabel2, pos=(1, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=10)
        dsPnlSiz.Add(self.infoLabel3, pos=(2, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=10)
        dsPnlSiz.Add(self.infoLabel4, pos=(3, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=10)
        dsPnlSiz.Add(self.infoLabel5, pos=(4, 0), flag=wx.LEFT|wx.BOTTOM, border=10)
        
        self.SetSizer(dsPnlSiz)

class InfoPanel_Book(scrolled.ScrolledPanel):
    def __init__(self, parent, treePyData = None):
        scrolled.ScrolledPanel.__init__(self, parent, -1)
#    def __init__(self, parent, id):
#        wx.Panel.__init__(self, parent, id)
        self.InitUI(treePyData)
        
        
    def InitUI(self, treePyData):
        self.treePyData = treePyData
        self.SetBackgroundColour(wx.WHITE) # this overrides color of enclosing panel
        bkPnlSiz = wx.GridBagSizer(1, 1)
        self.note1 = wx.StaticText(self, -1, 'Bold ')
        bolded = self.note1.GetFont() 
        bolded.SetWeight(wx.BOLD) 
        self.note1.SetFont(bolded)
        gRow = 0
        bkPnlSiz.Add(self.note1, pos=(gRow, 0), flag=wx.ALIGN_RIGHT|wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.note2 = wx.StaticText(self, -1, 'items are required')
        bkPnlSiz.Add(self.note2, pos=(gRow, 1), flag=wx.TOP|wx.RIGHT|wx.BOTTOM, border=5)

        gRow += 1
        bkPnlSiz.Add(wx.StaticLine(self), pos=(gRow, 0), span=(1, 3), flag=wx.EXPAND)
        
        gRow += 1
        self.bookNameLabel = wx.StaticText(self, -1, 'Book Name')
        self.bookNameLabel.SetFont(bolded)
        bkPnlSiz.Add(self.bookNameLabel, pos=(gRow, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.tcBookName = wx.TextCtrl(self)
        bkPnlSiz.Add(self.tcBookName, pos=(gRow, 1), span=(1, 1), 
            flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)

        gRow += 1
        self.bookNameHelp = wx.StaticText(self, -1, 'Book Name must be unique')
        bkPnlSiz.Add(self.bookNameHelp, pos=(gRow, 0), span=(1, 2), flag=wx.LEFT|wx.BOTTOM, border=5)

        gRow += 1
        bkPnlSiz.Add(wx.StaticLine(self), pos=(gRow, 0), span=(1, 2), flag=wx.EXPAND)

        gRow += 1
        self.longitudeLabel = wx.StaticText(self, -1, 'Longitude')
        self.longitudeLabel.SetFont(bolded)
        bkPnlSiz.Add(self.longitudeLabel, pos=(gRow, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.tcLongitude = wx.TextCtrl(self)
        bkPnlSiz.Add(self.tcLongitude, pos=(gRow, 1), span=(1, 1), 
            flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)

        gRow += 1
        self.longitudeHelp = wx.StaticText(self, -1, '(for calculating solar time)')
        bkPnlSiz.Add(self.longitudeHelp, pos=(gRow, 0), span=(1, 2), flag=wx.LEFT|wx.BOTTOM, border=5)

        gRow += 1
        bkPnlSiz.Add(wx.StaticLine(self), pos=(gRow, 0), span=(1, 2), flag=wx.EXPAND)

        gRow += 1
        self.hrOffsetLabel = wx.StaticText(self, -1, 'Hour Offset')
        self.hrOffsetLabel.SetFont(bolded)
        bkPnlSiz.Add(self.hrOffsetLabel, pos=(gRow, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.tcHrOffset = wx.TextCtrl(self)
        bkPnlSiz.Add(self.tcHrOffset, pos=(gRow, 1), span=(1, 1), 
            flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)

        gRow += 1
        self.hrOffsetHelp = wx.StaticText(self, -1, '(for calculating clock time)')
        bkPnlSiz.Add(self.hrOffsetHelp, pos=(gRow, 0), span=(1, 2), flag=wx.LEFT|wx.BOTTOM, border=5)

        gRow += 1
        bkPnlSiz.Add(wx.StaticLine(self), pos=(gRow, 0), span=(1, 2), flag=wx.EXPAND)

        gRow += 1
        self.timeSlicesLabel = wx.StaticText(self, -1, 'Time slices per day')
        self.timeSlicesLabel.SetFont(bolded)
        bkPnlSiz.Add(self.timeSlicesLabel, pos=(gRow, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.tcTimeSlices = wx.TextCtrl(self)
        bkPnlSiz.Add(self.tcTimeSlices, pos=(gRow, 1), span=(1, 1), 
            flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)

        gRow += 1
        self.timeSlicesHelp = wx.StaticText(self, -1, '(e.g. 1 for daily data, 24 for hourly data)')
        bkPnlSiz.Add(self.timeSlicesHelp, pos=(gRow, 0), span=(1, 2), flag=wx.LEFT|wx.BOTTOM, border=5)

        gRow += 1
        bkPnlSiz.Add(wx.StaticLine(self), pos=(gRow, 0), span=(1, 2), flag=wx.EXPAND)
        
        gRow += 1
        lstDates = scidb.getDatesList()
        self.dateLabelFrom = wx.StaticText(self, -1, 'From')
        bkPnlSiz.Add(self.dateLabelFrom, pos=(gRow, 0), span=(1, 1), flag=wx.ALIGN_RIGHT)
        self.cbxDateFrom = wx.ComboBox(self, -1, choices=lstDates, style=wx.CB_READONLY)
        bkPnlSiz.Add(self.cbxDateFrom, pos=(gRow, 1), span=(1, 1), flag=wx.LEFT, border=5)

        gRow += 1
        self.dateLabelTo = wx.StaticText(self, -1, 'To')
        bkPnlSiz.Add(self.dateLabelTo, pos=(gRow, 0), span=(1, 1), flag=wx.ALIGN_RIGHT)
        self.cbxDateTo = wx.ComboBox(self, -1, choices=lstDates, style=wx.CB_READONLY)
        bkPnlSiz.Add(self.cbxDateTo, pos=(gRow, 1), span=(1, 1), flag=wx.LEFT, border=5)

        gRow += 1
        self.dateOptLabel = wx.StaticText(self, -1, 'Optional, to limit date range')
        bkPnlSiz.Add(self.dateOptLabel, pos=(gRow, 0), span=(1, 2), flag=wx.LEFT|wx.BOTTOM, border=5)

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
        self.btnSave.Bind(wx.EVT_BUTTON, lambda evt, str=self.btnSave.GetLabel(): self.onClick_BtnSave(evt, str))
        bkPnlSiz.Add(self.btnSave, pos=(gRow, 0), flag=wx.LEFT|wx.BOTTOM, border=5)
        self.btnCancel = wx.Button(self, label="Cancel", size=(90, 28))
        self.btnCancel.Bind(wx.EVT_BUTTON, lambda evt, str=self.btnCancel.GetLabel(): self.onClick_BtnCancel(evt, str))
        bkPnlSiz.Add(self.btnCancel, pos=(gRow, 1), flag=wx.LEFT|wx.BOTTOM, border=5)

        if treePyData != None:
            print "treePyData:", treePyData
            self.fillBookPanelControls(treePyData)

        else:
            print "treePyData == None"

        self.SetSizer(bkPnlSiz)
        self.SetAutoLayout(1)
        self.SetupScrolling()

    def fillBookPanelControls(treePyData):
        # treePyData is the PyData from the tree item selected, a 2-tuple: ([Table Name], [Record ID in that table])
#        stSQL = """
#        SELECT BookName, Longitude, HourOffset,
#        OutputDataStart, OutputDataEnd, NumberOfTimeSlicesPerDay,
#        PutAllOutputRowsInOneSheet, BlankRowBetweenDataBlocks
#        FROM OutputBooks WHERE ID = ?
#        """
        stSQL = "SELECT * FROM ? WHERE ID=?"
        scidb.curD.execute(stSQL, treePyData)
        rec = scidb.curD.fetchone()
        self.tcBookName.SetValue(rec['BookName'])
        self.tcLongitude.SetValue(rec['Longitude'])
        self.tcHrOffset.SetValue(rec['HourOffset'])
        self.tcTimeSlices.SetValue(rec['NumberOfTimeSlicesPerDay'])
        if rec['OutputDataStart'] != None:
            self.cbxDateFrom.SetValue(rec['OutputDataStart'])
        else:
            self.cbxDateFrom.SetValue(None)
        if rec['OutputDataEnd'] != None:
            self.cbxDateTo.SetValue(rec['OutputDataEnd'])
        else:
            self.cbxDateTo.SetValue(None)
        if rec['PutAllOutputRowsInOneSheet'] == 1:
            self.ckSheetsTogether.SetValue(1)
        else:
            self.ckSheetsTogether.SetValue(0)
        if rec['BlankRowBetweenDataBlocks'] == 1:
            self.ckSpaceBetwBlocks.SetValue(1)
        else:
            self.ckSpaceBetwBlocks.SetValue(0)

    def onClick_BtnSave(self, event, strLabel):
        """"""
        wx.MessageBox('"Save" is not implemented yet', 'Info', 
            wx.OK | wx.ICON_INFORMATION)
        try:
            stSQL = """
                INSERT INTO OutputBooks
                (BookName, Longitude, HourOffset,
                OutputDataStart, OutputDataEnd, NumberOfTimeSlicesPerDay,
                PutAllOutputRowsInOneSheet, BlankRowBetweenDataBlocks)
                VALUES (?,?,?,?,?,?,?,?);
                """
            scidb.curD.execute(stSQL, (self.tcBookName.GetValue(), self.tcLongitude.GetValue(),
                    self.tcHrOffset.GetValue(),
                    self.cbxDateFrom.GetValue(), self.cbxDateTo.GetValue(),
                    self.tcTimeSlices.GetValue(),
                    self.ckSheetsTogether.GetValue(), self.ckSpaceBetwBlocks.GetValue()))
            scidb.datConn.commit()
            # get record ID of new record
            recID = scidb.curD.lastrowid
            # post an event to tell the DS tree to add a branch to itself
#            CreateNewBranchEvent, EVT_FLAG_CREATE_NEW_BRANCH = wx.lib.newevent.NewCommandEvent()
#            wx.PostEvent(framePanel.dsTree, CreateNewBranchEvent(TableName='OutputBooks', ID=recID))

        except sqlite3.IntegrityError: # duplicate name or required field missing
            print "could not add Book record to DB table"
            wx.MessageBox('Error creating book', 'Info', 
                wx.OK | wx.ICON_INFORMATION)

        parObject = self.GetParent()
        if parObject.GetClassName() == "wxDialog":
#            parObject.Destroy() # changes made, exit this dialog
            pass

        

    def onClick_BtnCancel(self, event, strLabel):
        """
        If this frame is shown in a Dialog, the Book is being created. Exit with no changes.
        If this frame is shown in the main form, restore it from the saved DB record
        """
        parObject = self.GetParent()
        if parObject.GetClassName() == "wxDialog":
            # for testing, try sending a custom event to the datasets tree
#            CreateNewBranchEvent, EVT_FLAG_CREATE_NEW_BRANCH = wx.lib.newevent.NewCommandEvent()
            #create the event
#            evt = CreateNewBranchEvent(TableName='(none)', ID=0)
            #post the event
#            wx.PostEvent(self, evt)
            parObject.EndModal(0)
#            parObject.Destroy() # if just in the creation dialog, exit with no changes to the DB
        else:
            wx.MessageBox('Undoing any edits', 'Info', 
                wx.OK | wx.ICON_INFORMATION)
            self.fillBookPanelControls(self.treePyData)

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
            bookDict[bookRec["ID"]] = [bookRec["BookName"], self.bookBranchID]

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
        
#        self.detailsLabel.SetLabel(self.dsTree.GetItemText(item))
#        print "ItemData:", self.dsTree.GetItemData(item)
        ckPyData = self.dsTree.GetPyData(item)
        print "PyData:", ckPyData
        if ckPyData[1] == 0:
            self.detailsPanel.DestroyChildren()
            dsInfoPnl = InfoPanel_DataSets(self.detailsPanel, wx.ID_ANY)
            self.detSiz.Add(dsInfoPnl, 1, wx.EXPAND)
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
            # write others for Sheet and Column

            ### 4. Launcher registers menu handlers with EVT_MENU, on the menu. ###
            wx.EVT_MENU( menu, id, self.MenuSelectionCb )

        ### 5. Launcher displays menu with call to PopupMenu, invoked on the source component, passing event's GetPoint. ###
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
        if opID == ID_ADD_BOOK:
            print "operation is to add a new book"
            dia = Dialog_Book(self, wx.ID_ANY, 'Add a new Book')
            # the dialog contains an 'InfoPanel_Book' named 'pnl'
            result = dia.ShowModal()
            # dialog is exited using EndModal, and comes back here
            print "Modal dialog result:", result
            # test of pulling things out of the modal dialog
#            childFrame = self.FindWindowByName('pnl')
#            print "dir of the Modal:", dir(dia)
            print "children of the Modal:" , dia.GetChildren()
            print "Text from the Modal:", dia.pnl.bookNameLabel.GetLabelText()
            dia.Destroy()

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
