import wx, sqlite3, datetime, copy, csv
import os, sys, re, cPickle, datetime
import scidb
import wx.lib.scrolledpanel as scrolled, wx.grid
import multiprocessing
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin
from wx.lib.wordwrap import wordwrap

try:
    import win32com.client
    hasCom = True
except ImportError:
    hasCom = False

try:
    from floatcanvas import NavCanvas, FloatCanvas, Resources
except ImportError: # if it's not there locally, try the wxPython lib.
    from wx.lib.floatcanvas import NavCanvas, FloatCanvas, Resources
import wx.lib.colourdb

class ndviDatesList(wx.ListCtrl, ListCtrlAutoWidthMixin):
    def __init__(self, *arg, **kw):
        wx.ListCtrl.__init__(self, *arg, **kw)
        ListCtrlAutoWidthMixin.__init__(self)
        self.setResizeColumn(0) # 1st column will take up any extra spaces
        self.InsertColumn(0, 'Dates')
        stSQL = 'SELECT Date FROM DataDates;'
        rows = scidb.curD.execute(stSQL).fetchall()
        for row in rows:
            self.Append((row['Date'],))

class ndviStationsList(wx.ListCtrl, ListCtrlAutoWidthMixin):
    def __init__(self, *arg, **kw):
        wx.ListCtrl.__init__(self, *arg, **kw)
        ListCtrlAutoWidthMixin.__init__(self)
        self.setResizeColumn(0) # 1st column will take up any extra spaces
        self.InsertColumn(0, 'Stations')
        stSQL = 'SELECT ID, StationName FROM Stations;'
        scidb.fillListctrlFromSQL(self, stSQL)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, lambda evt: self.onClick_StaList(evt))

    def onClick_StaList(self, event):
        currentItem = event.m_itemIndex
        i = self.GetItemData(currentItem)
        print 'stations list clicked: "', event.GetText(), '", record ID:', i
        print 'recID using selection: ', self.GetItemData(self.GetFocusedItem())


class NDVIPanel(wx.Panel):
    def __init__(self, parent, id):
        wx.Panel.__init__(self, parent, id)
        self.InitUI()

    def InitUI(self):
        #horizontal split means the split goes across
        #vertical split means the split goes up and down
        vSplit = wx.SplitterWindow(self, -1)
        self.ndviSetupPanel = scrolled.ScrolledPanel(vSplit, -1)
        self.InitNDVISetupPanel(self.ndviSetupPanel)
        
#        self.ndviSetupLabel = wx.StaticText(self.ndviSetupPanel, -1, "Set up NDVI calculations here")
        ndviInfoPanel = wx.Panel(vSplit, -1)
        ndviInfoPanel.SetBackgroundColour(wx.RED)
#        self.ndviInfoLabel = wx.StaticText(ndviInfoPanel, -1, "NDVI info will be here")

        hSplit = wx.SplitterWindow(ndviInfoPanel, -1)
        ndviOptsPanel = wx.Panel(hSplit, -1)
        optsSplit = wx.SplitterWindow(ndviOptsPanel, -1)
        ndviDatesPanel = wx.Panel(optsSplit, -1)
        self.InitDatesPanel(ndviDatesPanel)

        ndviStationsPanel = wx.Panel(optsSplit, -1)
        self.InitStationsPanel(ndviStationsPanel)
        
        optsSplit.SetMinimumPaneSize(100)
        optsSplit.SetSashGravity(0.5)
        # 'sashPosition=0' is supposed to split it down the middle, but the left panel is way smaller
        # see if further internal sizers fix this
        optsSplit.SplitVertically(ndviDatesPanel, ndviStationsPanel, sashPosition=0)
        # following doesn't help
        #optsSplit.SplitVertically(ndviDatesPanel, self.ndviStationsPanel, sashPosition=self.datesList.GetSize()[0]+10)
        optsSiz = wx.BoxSizer(wx.HORIZONTAL)
        optsSiz.Add(optsSplit, 1, wx.EXPAND)
        ndviOptsPanel.SetSizer(optsSiz)
        ndviOptsPanel.SetAutoLayout(1)
        
        previewPanel = wx.Panel(hSplit, -1)
        self.InitPreviewPanel(previewPanel)
#        self.previewPanel.SetBackgroundColour('#FFFF00')
#        self.pvwLabel = wx.StaticText(self.previewPanel, -1, "previews will be here")

        hSplit.SetMinimumPaneSize(20)
        hSplit.SetSashGravity(0.5)
        hSplit.SplitHorizontally(ndviOptsPanel, previewPanel)
        vSiz = wx.BoxSizer(wx.VERTICAL)
        vSiz.Add(hSplit, 1, wx.EXPAND)
        ndviInfoPanel.SetSizer(vSiz)

        vSplit.SetMinimumPaneSize(20)
        vSplit.SetSashGravity(0.5)
        vSplit.SplitVertically(self.ndviSetupPanel, ndviInfoPanel)
        hSiz = wx.BoxSizer(wx.HORIZONTAL)
        hSiz.Add(vSplit, 1, wx.EXPAND)
        self.SetSizer(hSiz)
        
#        EVT_ENTER_WINDOW(self, self.OnMessage(1, "Hello, world") )
#        EVT_LEAVE_WINDOW(self, self.OnMessage(0, "Goodbye, world") )

        print 'dates list size:', self.datesList.GetSize()
        # following doesn't help
        print "dates list width:", self.datesList.GetSize()[0]
        optsSplit.SetSashPosition(position=self.datesList.GetSize()[0]+10, redraw=True)

        return
    

    def InitNDVISetupPanel(self, pnl):
        self.LayoutNDVISetupPanel(pnl)
        
        # get existing or blank record
#        stSQL = "SELECT * FROM NDVIcalc WHERE ID = ?;"
#        rec = scidb.curD.execute(stSQL, (0,)).fetchone()
        stSQL = "SELECT * FROM NDVIcalc;"
        rec = scidb.curD.execute(stSQL).fetchone()
        if rec == None:
            print "no records yet in 'NDVIcalc'"
            self.calcDict = scidb.dictFromTableDefaults('NDVIcalc')
        else:
#            calcDict = copy.copy(rec) # this crashes
#        print 'scidb.curD.description:', scidb.curD.description
            self.calcDict = {}
            for recName in rec.keys():
                self.calcDict[recName] = rec[recName]
#        print "self.calcDict:", self.calcDict
        self.FillNDVISetupPanelFromCalcDict()

    def LayoutNDVISetupPanel(self, pnl):
        pnl.SetBackgroundColour(wx.WHITE)
        iLinespan = 5
        stpSiz = wx.GridBagSizer(1, 1)
        
        gRow = 0
        stpLabel = wx.StaticText(pnl, -1, 'Set up NDVI calculations here')
        stpSiz.Add(stpLabel, pos=(gRow, 0), span=(1, 2), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)

        stpSiz.Add(wx.StaticText(pnl, -1, 'Use panel:'),
                     pos=(gRow, 2), span=(1, 1), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)

        self.cbxGetPanel = wx.ComboBox(pnl, -1, style=wx.CB_READONLY)
        stpSiz.Add(self.cbxGetPanel, pos=(gRow, 3), span=(1, 1), flag=wx.LEFT, border=5)
        self.refresh_cbxPanelsChoices(-1)

        gRow += 1
        stpSiz.Add(wx.StaticLine(pnl), pos=(gRow, 0), span=(1, iLinespan), flag=wx.EXPAND)

        gRow += 1
        stpSiz.Add(wx.StaticText(pnl, -1, 'Name for this panel'),
                     pos=(gRow, 0), span=(1, 2), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)              
        self.tcCalcName = wx.TextCtrl(pnl)
        stpSiz.Add(self.tcCalcName, pos=(gRow, 2), span=(1, 3), 
            flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)

        # following is rarely used, not implemented yet
#        gRow += 1
#        self.ckChartFromRefDay = wx.CheckBox(pnl, label="Chart using")
#        stpSiz.Add(self.ckChartFromRefDay, pos=(gRow, 0), span=(1, 2), flag=wx.LEFT|wx.BOTTOM, border=5)
#        self.tcRefDay = wx.TextCtrl(pnl)
#        stpSiz.Add(self.tcRefDay, pos=(gRow, 2), span=(1, 1), 
#            flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)
#        stpSiz.Add(wx.StaticText(pnl, -1, 'as day 1'),
#                     pos=(gRow, 3), span=(1, 1), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        gRow += 1
        stpSiz.Add(wx.StaticLine(pnl), pos=(gRow, 0), span=(1, iLinespan), flag=wx.EXPAND)

        gRow += 1
        stpSiz.Add(wx.StaticText(pnl, -1, 'Reference station:'),
                     pos=(gRow, 0), span=(1, 2), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)

        stSQLStations = 'SELECT ID, StationName FROM Stations;'
        self.cbxRefStationID = wx.ComboBox(pnl, -1, style=wx.CB_READONLY)
        scidb.fillComboboxFromSQL(self.cbxRefStationID, stSQLStations)
        stpSiz.Add(self.cbxRefStationID, pos=(gRow, 2), span=(1, 3), flag=wx.LEFT, border=5)

        gRow += 1
        stpSiz.Add(wx.StaticText(pnl, -1, 'For the reference station:'),
                     pos=(gRow, 1), span=(1, 3), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)

        stSQLSeries = 'SELECT ID, DataSeriesDescription FROM DataSeries;'

        gRow += 1
        stpSiz.Add(wx.StaticText(pnl, -1, 'IR is in:'),
                     pos=(gRow, 0), span=(1, 2), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.cbxIRRefSeriesID = wx.ComboBox(pnl, -1, style=wx.CB_READONLY)
        scidb.fillComboboxFromSQL(self.cbxIRRefSeriesID, stSQLSeries)
        stpSiz.Add(self.cbxIRRefSeriesID, pos=(gRow, 2), span=(1, 3), flag=wx.LEFT, border=5)

        gRow += 1
        stpSiz.Add(wx.StaticText(pnl, -1, 'VIS is in:'),
                     pos=(gRow, 0), span=(1, 2), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.cbxVISRefSeriesID = wx.ComboBox(pnl, -1, style=wx.CB_READONLY)
        scidb.fillComboboxFromSQL(self.cbxVISRefSeriesID, stSQLSeries)
        stpSiz.Add(self.cbxVISRefSeriesID, pos=(gRow, 2), span=(1, 3), flag=wx.LEFT, border=5)

        gRow += 1
        stpSiz.Add(wx.StaticText(pnl, -1, 'For the other stations (selected to the right):'),
                     pos=(gRow, 1), span=(1, 4), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)

        gRow += 1
        stpSiz.Add(wx.StaticText(pnl, -1, 'IR is in:'),
                     pos=(gRow, 0), span=(1, 2), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.cbxIRDataSeriesID = wx.ComboBox(pnl, -1, style=wx.CB_READONLY)
        scidb.fillComboboxFromSQL(self.cbxIRDataSeriesID, stSQLSeries)
        stpSiz.Add(self.cbxIRDataSeriesID, pos=(gRow, 2), span=(1, 3), flag=wx.LEFT, border=5)

        gRow += 1
        stpSiz.Add(wx.StaticText(pnl, -1, 'VIS is in:'),
                     pos=(gRow, 0), span=(1, 2), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.cbxVisDataSeriesID = wx.ComboBox(pnl, -1, style=wx.CB_READONLY)
        scidb.fillComboboxFromSQL(self.cbxVisDataSeriesID, stSQLSeries)
        stpSiz.Add(self.cbxVisDataSeriesID, pos=(gRow, 2), span=(1, 3), flag=wx.LEFT, border=5)

        gRow += 1
        stpSiz.Add(wx.StaticLine(pnl), pos=(gRow, 0), span=(1, iLinespan), flag=wx.EXPAND)

        gRow += 1
        stAboutFns = 'Functions to process raw bands into IR and VIS signals. Use "i" and "v" for ' \
                        'raw IR- and VIS-containing bands respectively.'
        stWr = wordwrap(stAboutFns, 450, wx.ClientDC(pnl))
        stpSiz.Add(wx.StaticText(pnl, -1, stWr),
                     pos=(gRow, 0), span=(1, 5), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        gRow += 1
        stpSiz.Add(wx.StaticText(pnl, -1, 'IR:'),
                     pos=(gRow, 0), span=(1, 1), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.tcIRFunction = wx.TextCtrl(pnl)
        stpSiz.Add(self.tcIRFunction, pos=(gRow, 1), span=(1, 4), 
            flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)

        gRow += 1
        stpSiz.Add(wx.StaticText(pnl, -1, 'VIS:'),
                     pos=(gRow, 0), span=(1, 1), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.tcVISFunction = wx.TextCtrl(pnl)
        stpSiz.Add(self.tcVISFunction, pos=(gRow, 1), span=(1, 4), 
            flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)

        gRow += 1
        stpSiz.Add(wx.StaticLine(pnl), pos=(gRow, 0), span=(1, iLinespan), flag=wx.EXPAND)

        gRow += 1
        stpSiz.Add(wx.StaticText(pnl, -1, 'Cutoff, hours +/- solar noon:'),
                     pos=(gRow, 0), span=(1, 4), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.tcPlusMinusCutoffHours = wx.TextCtrl(pnl)
        stpSiz.Add(self.tcPlusMinusCutoffHours, pos=(gRow, 4), span=(1, 1), 
            flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)

        gRow += 1
        stpSiz.Add(wx.StaticLine(pnl), pos=(gRow, 0), span=(1, iLinespan), flag=wx.EXPAND)

        gRow += 1
        stpSiz.Add(wx.StaticText(pnl, -1, 'Only include readings from'),
                     pos=(gRow, 0), span=(1, 2), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.tcThresholdPctLow = wx.TextCtrl(pnl)
        stpSiz.Add(self.tcThresholdPctLow, pos=(gRow, 2), span=(1, 1), 
            flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)
        stpSiz.Add(wx.StaticText(pnl, -1, 'to'),
                     pos=(gRow, 3), span=(1, 1), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.tcThresholdPctHigh = wx.TextCtrl(pnl)
        stpSiz.Add(self.tcThresholdPctHigh, pos=(gRow, 4), span=(1, 1), 
            flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)

        gRow += 1
        stpSiz.Add(wx.StaticText(pnl, -1, 'percent of solar maximum on the clear day:'),
                     pos=(gRow, 0), span=(1, 3), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.tcClearDay = wx.TextCtrl(pnl)
        stpSiz.Add(self.tcClearDay, pos=(gRow, 3), span=(1, 2), 
            flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)

        gRow += 1
        stpSiz.Add(wx.StaticLine(pnl), pos=(gRow, 0), span=(1, iLinespan), flag=wx.EXPAND)

        gRow += 1
        self.ckUseOnlyValidNDVI = wx.CheckBox(pnl, label="Use only")
        stpSiz.Add(self.ckUseOnlyValidNDVI, pos=(gRow, 0), span=(1, 1), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.tcNDVIvalidMin = wx.TextCtrl(pnl)
        stpSiz.Add(self.tcNDVIvalidMin, pos=(gRow, 1), span=(1, 1), 
            flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)
        stpSiz.Add(wx.StaticText(pnl, -1, '<= NDVI <='),
            pos=(gRow, 2), span=(1, 1), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.tcNDVIvalidMax = wx.TextCtrl(pnl)
        stpSiz.Add(self.tcNDVIvalidMax, pos=(gRow, 3), span=(1, 1), 
            flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)

        gRow += 1
        stpSiz.Add(wx.StaticLine(pnl), pos=(gRow, 0), span=(1, iLinespan), flag=wx.EXPAND)
# ----->


        gRow += 1
        stpSiz.Add(wx.StaticText(pnl, -1, 'Output As:'),
                     pos=(gRow, 0), span=(1, 2), flag=wx.LEFT|wx.BOTTOM, border=5)

        iRBLeftBorderWd = 30
        gRow += 1
        self.rbExcel = wx.RadioButton(pnl, label='Excel workbook', style=wx.RB_GROUP)
        stpSiz.Add(self.rbExcel, pos=(gRow, 0), span=(1, 3), flag=wx.ALIGN_LEFT|wx.LEFT, border=iRBLeftBorderWd)
        self.rbExcel.Bind(wx.EVT_RADIOBUTTON, self.giveRBInfo)

        gRow += 1
        self.rbTabDelim = wx.RadioButton(pnl, label='Tab-delimited text')
        stpSiz.Add(self.rbTabDelim, pos=(gRow, 0), span=(1, 3), flag=wx.ALIGN_LEFT|wx.LEFT, border=iRBLeftBorderWd)
        self.rbTabDelim.Bind(wx.EVT_RADIOBUTTON, self.giveRBInfo)
        
        gRow += 1
        self.rbCommaDelim = wx.RadioButton(pnl, label='Comma-separated values ("CSV")')
        stpSiz.Add(self.rbCommaDelim, pos=(gRow, 0), span=(1, 3), flag=wx.ALIGN_LEFT|wx.LEFT, border=iRBLeftBorderWd)
        self.rbCommaDelim.Bind(wx.EVT_RADIOBUTTON, self.giveRBInfo)

        gRow += 1
        stpSiz.Add((0, 10), pos=(gRow, 0), span=(1, 3)) # some space

        gRow += 1
#        self.btnBrowseDir = wx.Button(self, label="Dir", size=(90, 28))
        self.btnBrowseDir = wx.Button(pnl, label="Dir", size=(-1, -1))
        self.btnBrowseDir.Bind(wx.EVT_BUTTON, lambda evt: self.onClick_BtnGetDir(evt))
        stpSiz.Add(self.btnBrowseDir, pos=(gRow, 0), flag=wx.LEFT, border=5)
        
        stpSiz.Add(wx.StaticText(pnl, -1, 'Base name, file or folder:'),
                     pos=(gRow, 1), span=(1, 1), flag=wx.ALIGN_RIGHT|wx.LEFT, border=5)

        self.tcBaseName = wx.TextCtrl(pnl, -1)
        stpSiz.Add(self.tcBaseName, pos=(gRow, 2), span=(1, 3),
            flag=wx.ALIGN_LEFT|wx.EXPAND, border=5)
        self.stItemName = 'Test_Base_Name' # for testing <-------- FIX THIS
        self.tcBaseName.SetValue(self.stItemName)

        gRow += 1
        self.tcDir = wx.TextCtrl(pnl, -1, style=wx.TE_MULTILINE)
        stpSiz.Add(self.tcDir, pos=(gRow, 0), span=(2, 5),
            flag=wx.ALIGN_LEFT|wx.LEFT|wx.BOTTOM|wx.EXPAND, border=5)
        gRow += 1 # space for the 2 grid rows for tcDir
        self.tcDir.SetValue('(save output in default directory)')

        
        gRow += 1
        stpSiz.Add(wx.StaticLine(pnl), pos=(gRow, 0), span=(1, 5), flag=wx.EXPAND)

        gRow += 1
        self.tcOutputOptInfo = wx.TextCtrl(pnl, -1, style=wx.TE_MULTILINE|wx.TE_READONLY)
        stpSiz.Add(self.tcOutputOptInfo, pos=(gRow, 0), span=(3, 5),
            flag=wx.ALIGN_LEFT|wx.TOP|wx.LEFT|wx.BOTTOM|wx.EXPAND, border=5)
        gRow += 1 # space for the three grid rows for tcOutputOptInfo
        gRow += 1

        self.giveRBInfo(-1) # have to explictly call this 1st time; -1 is dummy value for event
        
        gRow += 1
        stpSiz.Add(wx.StaticLine(pnl), pos=(gRow, 0), span=(1, 5), flag=wx.EXPAND)
        gRow += 1
        stpSiz.Add(wx.StaticLine(pnl), pos=(gRow, 0), span=(1, 5), flag=wx.EXPAND)

        gRow += 1
        sheetNoteBlocking1 = wx.StaticText(pnl, -1, 'NOTE: Making a dataset will block this application until complete.')
#        sheetNoteBlocking1.SetFont(bolded)
        stpSiz.Add(sheetNoteBlocking1, pos=(gRow, 0), span=(1, 5), flag=wx.TOP|wx.LEFT, border=5)
        gRow += 1
        sheetNoteBlocking2 = wx.StaticText(pnl, -1, ' A full dataset can take a long time.')
#        sheetNoteBlocking2.SetFont(bolded)
        stpSiz.Add(sheetNoteBlocking2, pos=(gRow, 0), span=(1, 5), flag=wx.LEFT|wx.BOTTOM, border=5)

        gRow += 1
        stpSiz.Add(wx.StaticLine(pnl), pos=(gRow, 0), span=(1, 5), flag=wx.EXPAND)
        gRow += 1
        stpSiz.Add(wx.StaticLine(pnl), pos=(gRow, 0), span=(1, 5), flag=wx.EXPAND)

        gRow += 1

        self.ckPreview = wx.CheckBox(pnl, label="Preview, Rows:")
        stpSiz.Add(self.ckPreview, pos=(gRow, 0), span=(1, 1),
            flag=wx.ALIGN_LEFT|wx.LEFT|wx.BOTTOM, border=5)
        self.ckPreview.SetValue(True)
        self.ckPreview.Bind(wx.EVT_CHECKBOX, self.onCkPreview)

        self.spinPvwRows = wx.SpinCtrl(pnl, -1, '', size=(50,-1))
        self.spinPvwRows.SetRange(1,100)
        self.spinPvwRows.SetValue(10)
        stpSiz.Add(self.spinPvwRows, pos=(gRow, 1), span=(1, 1),
            flag=wx.ALIGN_LEFT|wx.LEFT|wx.BOTTOM, border=5)

#        stpSiz.Add(wx.StaticText(self, -1, ' Rows'),
#                     pos=(gRow, 2), flag=wx.ALIGN_LEFT|wx.LEFT|wx.BOTTOM, border=5)

        self.btnMake = wx.Button(pnl, label="Make", size=(90, 28))
        self.btnMake.Bind(wx.EVT_BUTTON, lambda evt: self.onClick_BtnMake(evt))
        stpSiz.Add(self.btnMake, pos=(gRow, 3), flag=wx.LEFT|wx.BOTTOM, border=5)

        gRow += 1
        self.tcProgress = wx.TextCtrl(pnl, -1, style=wx.TE_MULTILINE|wx.TE_READONLY)
        stpSiz.Add(self.tcProgress, pos=(gRow, 0), span=(4, 5),
            flag=wx.ALIGN_LEFT|wx.TOP|wx.LEFT|wx.BOTTOM|wx.EXPAND, border=5)
        gRow += 1 # space for the 4 grid rows for tcProgress
        gRow += 1
        gRow += 1

        # offer some estimate diagnostics
        self.tcProgress.AppendText('Estimate for full dataset: ')
        fEstSecsPerQuery = 0.2
#        iNumRows = self.bkDict['CtOfDays'] * self.bkDict['NumberOfTimeSlicesPerDay']
#        if self.sourceTable == 'OutputSheets':
#            self.iTotRowEstimate = iNumRows
#            self.tcProgress.AppendText(str(self.iTotRowEstimate) + ' rows; ')
#            iNumQueries = self.shDict['CtAggCols'] + 1
#            fNumSecsWorking = iNumRows * iNumQueries * fEstSecsPerQuery
#            self.tcProgress.AppendText('working time, %d seconds ' % fNumSecsWorking)
#        else: # book
#            self.tcProgress.AppendText('%d rows in each of %d sheets' % (iNumRows, len(self.lShs)))
#            self.iTotRowEstimate = iNumRows * len(self.lShs)
#            self.tcProgress.AppendText(', for a total of %d rows; ' % self.iTotRowEstimate)
#            iTotQueries = 0
#            for shDict in self.lShs:
#                iTotQueries += (shDict['CtAggCols'] + 1)
#            fNumSecsWorking = iNumRows * iTotQueries * fEstSecsPerQuery
#            self.tcProgress.AppendText('Estimated working time for whole dataset, %d seconds ' % fNumSecsWorking)
        self.tcProgress.AppendText('(estimation not implemented yet)')

# <-----
        gRow += 1
        self.btnSavePnl = wx.Button(pnl, label="Save\npanel", size=(-1, -1))
        self.btnSavePnl.Bind(wx.EVT_BUTTON, lambda evt: self.onClick_BtnSavePnl(evt))
        stpSiz.Add(self.btnSavePnl, pos=(gRow, 0), flag=wx.LEFT|wx.BOTTOM, border=5)

        stpSiz.Add(wx.StaticText(pnl, -1, 'Tasks:'),
                     pos=(gRow, 1), span=(1, 1), flag=wx.ALIGN_RIGHT|wx.TOP|wx.LEFT|wx.BOTTOM, border=5)

        lTasks = ['Make this NDVI dataset','Copy the current panel, which you can then vary']
        self.cbxTasks = wx.ComboBox(pnl, -1, choices=lTasks, style=wx.CB_READONLY)
        self.cbxTasks.Bind(wx.EVT_COMBOBOX, self.onCbxTasks)
        stpSiz.Add(self.cbxTasks, pos=(gRow, 2), span=(1, 3), flag=wx.LEFT, border=5)

        pnl.SetSizer(stpSiz)
        pnl.SetAutoLayout(1)
        pnl.SetupScrolling()

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

    def onClick_BtnMake(self, event):
        """
        Make the dataset
        """
        pass
        return # for testing, stop here
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
        # get a count
        iNumRowsInDataset = scidb.countOfSheetRows(shDict['ID'])
        # use the row generator
        sheetRows = scidb.generateSheetRows(shDict['ID'])
        for dataRow in sheetRows:
            # yielded object is list with as many members as there are columns
            iRowCt += 1
            if iRowCt > iNumRowsToDo:
                break
            self.tcProgress.SetValue('Doing row %d of %d' % (iRowCt, iNumRowsInDataset))
            wx.Yield() # allow window updates to occur
            wr.writerow(dataRow)
            
        lMsg[1] = str(iRowCt)

        fOut.close()
        wx.MessageBox("".join(lMsg), 'Info',
            wx.OK | wx.ICON_INFORMATION)
        return # end of if CSV

    def FillNDVISetupPanelFromCalcDict(self):
        if self.calcDict['CalcName'] != None:
            self.tcCalcName.SetValue('%s' % self.calcDict['CalcName'])
        # following is rarely used, not implemented yet
#        self.ckChartFromRefDay.SetValue(self.calcDict['ChartFromRefDay'])
#        if self.calcDict['RefDay'] != None:
#            self.tcRefDay.SetValue('%s' % self.calcDict['RefDay'])
        if self.calcDict['RefStationID'] != None:
            scidb.setComboboxToClientData(self.cbxRefStationID, self.calcDict['RefStationID'])
        if self.calcDict['IRRefSeriesID'] != None:
            scidb.setComboboxToClientData(self.cbxIRRefSeriesID, self.calcDict['IRRefSeriesID'])
        if self.calcDict['VISRefSeriesID'] != None:
            scidb.setComboboxToClientData(self.cbxVISRefSeriesID, self.calcDict['VISRefSeriesID'])
        if self.calcDict['IRDataSeriesID'] != None:
            scidb.setComboboxToClientData(self.cbxIRDataSeriesID, self.calcDict['IRDataSeriesID'])
        if self.calcDict['VisDataSeriesID'] != None:
            scidb.setComboboxToClientData(self.cbxVisDataSeriesID, self.calcDict['VisDataSeriesID'])
        if self.calcDict['IRFunction'] != None:
            self.tcIRFunction.SetValue('%s' % self.calcDict['IRFunction'])
        if self.calcDict['VISFunction'] != None:
            self.tcVISFunction.SetValue('%s' % self.calcDict['VISFunction'])
        if self.calcDict['PlusMinusCutoffHours'] != None:
            self.tcPlusMinusCutoffHours.SetValue('%.1f' % self.calcDict['PlusMinusCutoffHours'])
        if self.calcDict['ThresholdPctLow'] != None:
            self.tcThresholdPctLow.SetValue('%d' % self.calcDict['ThresholdPctLow'])
        if self.calcDict['ThresholdPctHigh'] != None:
            self.tcThresholdPctHigh.SetValue('%d' % self.calcDict['ThresholdPctHigh'])
        if self.calcDict['ClearDay'] != None:
            self.tcClearDay.SetValue('%d' % self.calcDict['ClearDay'])
        self.ckUseOnlyValidNDVI.SetValue(self.calcDict['UseOnlyValidNDVI'])
        if self.calcDict['NDVIvalidMin'] != None:
            self.tcNDVIvalidMin.SetValue('%.2f' % self.calcDict['NDVIvalidMin'])
        if self.calcDict['NDVIvalidMax'] != None:
            self.tcNDVIvalidMax.SetValue('%.2f' % self.calcDict['NDVIvalidMax'])

    def InitDatesPanel(self, pnl):
        pnl.SetBackgroundColour('#0FFF0F')
        dtSiz = wx.GridBagSizer(0, 0)
        dtSiz.AddGrowableCol(0)
        
        gRow = 0
#        datesLabel = wx.StaticText(pnl, -1, "Dates")
#        dtSiz.Add(datesLabel, pos=(gRow, 0), span=(1, 1), flag=wx.TOP|wx.LEFT|wx.BOTTOM|wx.EXPAND, border=5)
        
#        gRow += 1
        self.datesList = ndviDatesList(pnl, style = wx.LC_REPORT)
        dtSiz.Add(self.datesList, pos=(gRow, 0), span=(1, 1), flag=wx.EXPAND, border=0)
        dtSiz.AddGrowableRow(gRow)
        pnl.SetSizer(dtSiz)
        pnl.SetAutoLayout(1)

    def InitStationsPanel(self, pnl):
        pnl.SetBackgroundColour('#FF0FFF')
#        stationsLabel = wx.StaticText(pnl, -1, "stations will be here")
        stSiz = wx.GridBagSizer(0, 0)
        stSiz.AddGrowableCol(0)
        
        gRow = 0
#        stationsLabel = wx.StaticText(pnl, -1, "Stations")
#        stSiz.Add(stationsLabel, pos=(gRow, 0), span=(1, 1), flag=wx.TOP|wx.LEFT|wx.BOTTOM|wx.EXPAND, border=5)
        
#        gRow += 1
        self.stationsList = ndviStationsList(pnl, style = wx.LC_REPORT)
        stSiz.Add(self.stationsList, pos=(gRow, 0), span=(1, 1), flag=wx.EXPAND, border=0)
        stSiz.AddGrowableRow(gRow)
        pnl.SetSizer(stSiz)
        pnl.SetAutoLayout(1)

    def InitPreviewPanel(self, pnl):
        pnl.SetBackgroundColour('#FFFFFF')
        pvSiz = wx.GridBagSizer(0, 0)
        pvSiz.AddGrowableCol(0)
        
        gRow = 0
        self.pvLabel = wx.StaticText(pnl, -1, "Select Ref station, IR series, then float over dates to preview")
        pvSiz.Add(self.pvLabel, pos=(gRow, 0), span=(1, 1), flag=wx.TOP|wx.LEFT|wx.BOTTOM|wx.EXPAND, border=5)
        
        gRow += 1
        # Add the FloatCanvas canvas
        self.NC = NavCanvas.NavCanvas(pnl,
             Debug = 0,
             BackgroundColor = "WHITE")
        self.Canvas = self.NC.Canvas # reference the contained FloatCanvas
        # test of drawing one line
#        self.UnBindAllMouseEvents()
#        self.Canvas.InitAll()
#        self.Canvas.Draw()
#        points = [(-100,-100),(100,100), (100,-100), (-100,100)]
#        self.Canvas.AddLine(points, LineWidth = 1, LineColor = 'BLUE')
#        self.Canvas.ZoomToBB() # this makes the drawing about 10% of the whole canvas, but
        # then the "Zoom To Fit" button correctly expands it to the whole space

        pvSiz.Add(self.NC, pos=(gRow, 0), span=(1, 1), flag=wx.EXPAND, border=0)
        pvSiz.AddGrowableRow(gRow)
        pnl.SetSizer(pvSiz)
        pnl.SetAutoLayout(1)

    def refresh_cbxPanelsChoices(self, event):
        self.cbxGetPanel.Clear()
        stSQLPanels = 'SELECT ID, CalcName FROM NDVIcalc;'
        scidb.fillComboboxFromSQL(self.cbxGetPanel, stSQLPanels)

    def onClick_BtnSavePnl(self, event):
        """
        """
        # clean up whitespace; remove leading/trailing & multiples
        stCalcName = " ".join(self.tcCalcName.GetValue().split())
        print "stCalcName:", stCalcName
        if stCalcName == '':
            wx.MessageBox('Need a Name for this panel', 'Missing',
                wx.OK | wx.ICON_INFORMATION)
            self.tcCalcName.SetValue(stCalcName)
            self.tcCalcName.SetFocus()
#            self.Scroll(0, 0) # at the top
            return
        # if Name is same as in the dictionary, assume edited; overwrite
        if stCalcName == self.calcDict['CalcName']:
            boolUpdatePanel = 1
        else:
            boolUpdatePanel = 0
        

    def onCbxTasks(self, event):
        print 'self.cbxTasks selected, choice: "', self.cbxTasks.GetValue(), '"'



class NDVIFrame(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title)
        self.InitUI()
        self.SetSize((750, 600))
#        self.Centre()
        self.Show(True)

    def InitUI(self):
        framePanel = NDVIPanel(self, wx.ID_ANY)
        self.DtList = framePanel.datesList
        self.DtList.Bind( wx.EVT_MOTION, self.onMouseMotion )
        self.pvLabel = framePanel.pvLabel
        self.NC = framePanel.NC
        self.Canvas = framePanel.Canvas
        self.CreateStatusBar()
        self.SetStatusText("Hello, world!")
        self.stDateToPreview = ''
        self.cbxRefStationID = framePanel.cbxRefStationID
        self.cbxIRRefSeriesID = framePanel.cbxIRRefSeriesID
        self.previewSeries = 5 # for testing, use IrUP
        self.previewStation = 1 # for testing, use P19

    def onMouseMotion( self, event ):
        index, flags = self.DtList.HitTest(event.GetPosition())
        if index == wx.NOT_FOUND:
            self.pvLabel.SetLabel('Select Ref station, IR series, then float over dates to preview')
            return
        if flags & wx.LIST_HITTEST_NOWHERE:
            self.pvLabel.SetLabel('Select Ref station, IR series, then float over dates to preview')
            return
        txtDate = self.DtList.GetItemText(index)
        if txtDate == self.stDateToPreview:
            return # no need to re-do one already done
        self.Canvas.InitAll()
        self.Canvas.Draw()
        self.stDateToPreview = txtDate
        self.SetStatusText("previewing " + self.stDateToPreview)
        print "date to preview:", self.stDateToPreview
        self.pvLabel.SetLabel('Generating preview for ' + self.stDateToPreview)
        
        # get the station ID, if selected
        staID = scidb.getComboboxIndex(self.cbxRefStationID)
        if staID == None:
            self.pvLabel.SetLabel('Select Reference Station, to preview dates')
            return
        # get the IR series ID, if selected
        serID = scidb.getComboboxIndex(self.cbxIRRefSeriesID)
        if serID == None:
            self.pvLabel.SetLabel('Select IR series for the Reference Station, to preview dates')
            return
        # get the hour offset from the station longitude
        longitude = scidb.stationLongitude(staID)
        if longitude == None:
            hrOffLon = 0
        else:
            hrOffLon = longitude / 15 # one hour for every 15 degrees of longitude
        # get the minute offet from the Equation of Time table
        stSQLm = """SELECT MinutesCorrection FROM EqnOfTime
            WHERE DayOfYear = strftime('%j','{sDt}');
            """.format(sDt=self.stDateToPreview)
        minOffEqTm = scidb.curD.execute(stSQLm).fetchone()['MinutesCorrection']

        self.SetStatusText("Getting data range for " + self.stDateToPreview)
        stSQLMinMax = """
            SELECT MIN(CAST(Data.Value AS FLOAT)) AS MinData,
            MAX(CAST(Data.Value AS FLOAT)) AS MaxData
            FROM ChannelSegments LEFT JOIN Data ON ChannelSegments.ChannelID = Data.ChannelID
            WHERE ChannelSegments.StationID = {iSt}  AND ChannelSegments.SeriesID = {iSe}
            AND Data.UTTimestamp >= DATETIME('{sDt}', '{fHo} hour', '{fEq} minute')
            AND Data.UTTimestamp < DATETIME('{sDt}', '1 day', '{fHo} hour', '{fEq} minute')
            AND Data.UTTimestamp >= ChannelSegments.SegmentBegin
            AND  Data.UTTimestamp <= COALESCE(ChannelSegments.SegmentEnd, DATETIME('now'))
        """.format(iSt=staID, iSe=serID, fHo=-hrOffLon, fEq=-minOffEqTm, sDt=self.stDateToPreview)
#            print stSQLMinMax
        MnMxRec = scidb.curD.execute(stSQLMinMax).fetchone()
        self.fDataMin = MnMxRec['MinData']
        self.fDataMax = MnMxRec['MaxData']
        print "Min", self.fDataMin, "Max", self.fDataMax
        self.totSecs = 60 * 60 * 24 # use standard day length
        if self.fDataMax == self.fDataMin:
            self.scaleY = 0
        else:
            self.scaleY = (0.618 * self.totSecs) / (self.fDataMax - self.fDataMin)
        print 'scaleY', self.scaleY
        self.SetStatusText("Getting data for " + self.stDateToPreview)
        stSQL = """SELECT
            strftime('%s', Data.UTTimestamp) - strftime('%s', DATETIME('{sDt}', '{fHo} hour', '{fEq} minute')) AS Secs,
            Data.Value * {fSy} AS Val
            FROM ChannelSegments LEFT JOIN Data ON ChannelSegments.ChannelID = Data.ChannelID
            WHERE ChannelSegments.StationID = {iSt}  AND ChannelSegments.SeriesID = {iSe}
            AND Data.UTTimestamp >= DATETIME('{sDt}', '{fHo} hour', '{fEq} minute')
            AND Data.UTTimestamp < DATETIME('{sDt}', '1 day', '{fHo} hour', '{fEq} minute')
            AND Data.UTTimestamp >= ChannelSegments.SegmentBegin
            AND  Data.UTTimestamp <= COALESCE(ChannelSegments.SegmentEnd, DATETIME('now'))
            ORDER BY Secs;
            """.format(iSt=staID, iSe=serID, fHo=-hrOffLon, fEq=-minOffEqTm, sDt=self.stDateToPreview, fSy=self.scaleY)
#        print stSQL
        ptRecs = scidb.curD.execute(stSQL).fetchall()
        if len(ptRecs) == 0:
            self.pvLabel.SetLabel('No data for for ' + self.stDateToPreview)
            stNoData = "No data for this time range"
            pt = (0,0)
            self.Canvas.AddScaledText(stNoData, pt, Size = 10, Color = 'BLACK', Position = "cc")
        else:
            pts = []
            for ptRec in ptRecs:
                pts.append((ptRec['Secs'], ptRec['Val']))
            self.Canvas.AddLine(pts, LineWidth = 1, LineColor = 'BLUE')
        self.Canvas.ZoomToBB()
            
    def OnMessage(self, on, msg):
        if not on:
            msg = ""
        self.SetStatusText(msg)



def main():
    app = wx.App(redirect=False)
    dsFrame = NDVIFrame(None, wx.ID_ANY, 'NDVI calculations')
    app.MainLoop() 

if __name__ == '__main__':
    main()
