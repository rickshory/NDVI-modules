import wx, sqlite3, datetime, copy, csv, shutil
import os, sys, re, cPickle, datetime, time, math
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

sFmt = '%Y-%m-%d %H:%M:%S'
boolMakingDataset = False

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
        hSplit = wx.SplitterWindow(vSplit, -1)
        optsSplit = wx.SplitterWindow(hSplit, -1)

        ndviDatesPanel = wx.Panel(optsSplit, -1)
        self.InitDatesPanel(ndviDatesPanel)

        ndviStationsPanel = wx.Panel(optsSplit, -1)
        self.InitStationsPanel(ndviStationsPanel)
        optsSplit.SplitVertically(ndviDatesPanel, ndviStationsPanel, sashPosition=100)
        optsSplit.SetMinimumPaneSize(100)
        optsSplit.SetSashGravity(0.5)
        
        previewPanel = wx.Panel(hSplit, -1)
        self.InitPreviewPanel(previewPanel)

        hSplit.SplitHorizontally(optsSplit, previewPanel)
        hSplit.SetMinimumPaneSize(100)
        hSplit.SetSashGravity(0.5)
        
        self.ndviSetupPanel = scrolled.ScrolledPanel(vSplit, -1)
        self.InitNDVISetupPanel(self.ndviSetupPanel)

        vSplit.SplitVertically(self.ndviSetupPanel, hSplit, sashPosition=600)
        vSplit.SetMinimumPaneSize(100)
        vSplit.SetSashGravity(0.5)

        OverallSizer = wx.BoxSizer(wx.HORIZONTAL)
        OverallSizer.Add(vSplit, 1, wx.EXPAND)
        self.SetSizer(OverallSizer)    

    def InitNDVISetupPanel(self, pnl):
        self.LayoutNDVISetupPanel(pnl)
        
        # get existing or blank record
#        stSQL = "SELECT * FROM NDVIcalc WHERE ID = ?;"
#        rec = scidb.curD.execute(stSQL, (0,)).fetchone()
#        stSQL = "SELECT * FROM NDVIcalc;"
#        rec = scidb.curD.execute(stSQL).fetchone()
#        if rec == None:
#            print "no records yet in 'NDVIcalc'"
        self.calcDict = scidb.dictFromTableDefaults('NDVIcalc')
#        else:
#            calcDict = copy.copy(rec) # this crashes
#        print 'scidb.curD.description:', scidb.curD.description
#            self.calcDict = {}
#            for recName in rec.keys():
#                self.calcDict[recName] = rec[recName]
#        print "self.calcDict:", self.calcDict
        self.FillNDVISetupPanelFromCalcDict()

    def LayoutNDVISetupPanel(self, pnl):
        pnl.SetBackgroundColour(wx.WHITE)
        iLinespan = 5
        stpSiz = wx.GridBagSizer(1, 1)
        
        gRow = 0
        stpLabel = wx.StaticText(pnl, -1, 'Set up NDVI calculations here')
        stpSiz.Add(stpLabel, pos=(gRow, 0), span=(1, 2), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)

        gRow += 1
        stpSiz.Add(wx.StaticText(pnl, -1, 'Retrieve panel:'),
                     pos=(gRow, 0), span=(1, 1), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)

        self.cbxGetPanel = wx.ComboBox(pnl, -1, style=wx.CB_READONLY)
        stpSiz.Add(self.cbxGetPanel, pos=(gRow, 1), span=(1, 3), flag=wx.LEFT, border=5)
        self.cbxGetPanel.Bind(wx.EVT_COMBOBOX, lambda evt: self.onCbxRetrievePanel(evt))
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
                     pos=(gRow, 0), span=(1, 1), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)

        self.ckUseRef = wx.CheckBox(pnl, label="Use Reference")
        stpSiz.Add(self.ckUseRef, pos=(gRow, 1), span=(1, 1),
            flag=wx.ALIGN_LEFT|wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.ckUseRef.SetValue(True)

        gRow += 1

        stSQLStations = 'SELECT ID, StationName FROM Stations;'
        self.cbxRefStationID = wx.ComboBox(pnl, -1, style=wx.CB_READONLY)
        scidb.fillComboboxFromSQL(self.cbxRefStationID, stSQLStations)
        stpSiz.Add(self.cbxRefStationID, pos=(gRow, 0), span=(1, 4), flag=wx.LEFT, border=5)

        gRow += 1
        stpSiz.Add(wx.StaticText(pnl, -1, 'For the reference station:'),
                     pos=(gRow, 0), span=(1, 3), flag=wx.LEFT, border=30)

        stSQLSeries = 'SELECT ID, DataSeriesDescription FROM DataSeries;'

        gRow += 1
        stpSiz.Add(wx.StaticText(pnl, -1, 'IR is in:'),
                     pos=(gRow, 0), span=(1, 1), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.cbxIRRefSeriesID = wx.ComboBox(pnl, -1, style=wx.CB_READONLY)
        scidb.fillComboboxFromSQL(self.cbxIRRefSeriesID, stSQLSeries)
        stpSiz.Add(self.cbxIRRefSeriesID, pos=(gRow, 1), span=(1, 3), flag=wx.LEFT, border=5)

        gRow += 1
        stpSiz.Add(wx.StaticText(pnl, -1, 'VIS is in:'),
                     pos=(gRow, 0), span=(1, 1), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.cbxVISRefSeriesID = wx.ComboBox(pnl, -1, style=wx.CB_READONLY)
        scidb.fillComboboxFromSQL(self.cbxVISRefSeriesID, stSQLSeries)
        stpSiz.Add(self.cbxVISRefSeriesID, pos=(gRow, 1), span=(1, 3), flag=wx.LEFT, border=5)

        gRow += 1
        stpSiz.Add(wx.StaticText(pnl, -1, 'For the other stations (selected to the right):'),
                     pos=(gRow, 0), span=(1, 4), flag=wx.LEFT, border=30)

        gRow += 1
        stpSiz.Add(wx.StaticText(pnl, -1, 'IR is in:'),
                     pos=(gRow, 0), span=(1, 1), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.cbxIRDataSeriesID = wx.ComboBox(pnl, -1, style=wx.CB_READONLY)
        scidb.fillComboboxFromSQL(self.cbxIRDataSeriesID, stSQLSeries)
        stpSiz.Add(self.cbxIRDataSeriesID, pos=(gRow, 1), span=(1, 3), flag=wx.LEFT, border=5)

        gRow += 1
        stpSiz.Add(wx.StaticText(pnl, -1, 'VIS is in:'),
                     pos=(gRow, 0), span=(1, 1), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.cbxVisDataSeriesID = wx.ComboBox(pnl, -1, style=wx.CB_READONLY)
        scidb.fillComboboxFromSQL(self.cbxVisDataSeriesID, stSQLSeries)
        stpSiz.Add(self.cbxVisDataSeriesID, pos=(gRow, 1), span=(1, 3), flag=wx.LEFT, border=5)

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
                     pos=(gRow, 0), span=(1, 2), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.tcPlusMinusCutoffHours = wx.TextCtrl(pnl)
        stpSiz.Add(self.tcPlusMinusCutoffHours, pos=(gRow, 2), span=(1, 1), 
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
                     pos=(gRow, 0), span=(1, 2), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.tcClearDay = wx.TextCtrl(pnl)
        stpSiz.Add(self.tcClearDay, pos=(gRow, 2), span=(1, 2),
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

        gRow += 1
        self.ckIncludeSummaries = wx.CheckBox(pnl,
            label="Create daily summaries. (Excel output will include charts)")
        stpSiz.Add(self.ckIncludeSummaries, pos=(gRow, 0), span=(1, 4),
            flag=wx.ALIGN_LEFT|wx.LEFT|wx.BOTTOM, border=5)
        self.ckIncludeSummaries.SetValue(False)

        gRow += 1
        stpSiz.Add(wx.StaticLine(pnl), pos=(gRow, 0), span=(1, iLinespan), flag=wx.EXPAND)

        gRow += 1
        self.ckIncludeSAS = wx.CheckBox(pnl,
            label="Also output data for SAS")
        stpSiz.Add(self.ckIncludeSAS, pos=(gRow, 0), span=(1, 4),
            flag=wx.ALIGN_LEFT|wx.LEFT|wx.BOTTOM, border=5)
        self.ckIncludeSAS.SetValue(False)

        gRow += 1
        stpSiz.Add(wx.StaticLine(pnl), pos=(gRow, 0), span=(1, iLinespan), flag=wx.EXPAND)

        gRow += 1
        self.ckNormalize = wx.CheckBox(pnl,
            label="Normalize NDVI into range 0-to-1, i.e. to view relative change")
        stpSiz.Add(self.ckNormalize, pos=(gRow, 0), span=(1, 4),
            flag=wx.ALIGN_LEFT|wx.LEFT|wx.BOTTOM, border=5)
        self.ckNormalize.SetValue(False)

        gRow += 1
        stpSiz.Add(wx.StaticLine(pnl), pos=(gRow, 0), span=(1, iLinespan), flag=wx.EXPAND)

        gRow += 1
        stpSiz.Add(wx.StaticText(pnl, -1, 'Output As:'),
                     pos=(gRow, 0), span=(1, 2), flag=wx.LEFT|wx.BOTTOM, border=5)
        
        stAboutOutput = ' Excel uses the Base Name for a file, the other options create a ' \
            'set of files in the Base Name folder. With Excel, you will see the dataset as ' \
            'it builds. Other options do not show as the files build on disk.'
        stWrO = wordwrap(stAboutOutput, 450, wx.ClientDC(pnl))
        stpSiz.Add(wx.StaticText(pnl, -1, stWrO),
            pos=(gRow, 2), span=(4, 3), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)

        iRBLeftBorderWd = 20
        gRow += 1
        self.rbExcel = wx.RadioButton(pnl, label='Excel workbook', style=wx.RB_GROUP)
        stpSiz.Add(self.rbExcel, pos=(gRow, 0), span=(1, 2), flag=wx.ALIGN_LEFT|wx.LEFT, border=iRBLeftBorderWd)

        gRow += 1
        self.rbTabDelim = wx.RadioButton(pnl, label='Tab-delimited text')
        stpSiz.Add(self.rbTabDelim, pos=(gRow, 0), span=(1, 2), flag=wx.ALIGN_LEFT|wx.LEFT, border=iRBLeftBorderWd)
        
        gRow += 1
        self.rbCommaDelim = wx.RadioButton(pnl, label='Comma-separated values ("CSV")')
        stpSiz.Add(self.rbCommaDelim, pos=(gRow, 0), span=(1, 2), flag=wx.ALIGN_LEFT|wx.LEFT, border=iRBLeftBorderWd)

        gRow += 1
        stpSiz.Add((0, 10), pos=(gRow, 0), span=(1, 3)) # some space

        gRow += 1
#        self.btnBrowseDir = wx.Button(self, label="Dir", size=(90, 28))
        self.btnBrowseDir = wx.Button(pnl, label="Dir", size=(-1, -1))
        self.btnBrowseDir.Bind(wx.EVT_BUTTON, lambda evt: self.onClick_BtnGetDir(evt))
        stpSiz.Add(self.btnBrowseDir, pos=(gRow, 0), flag=wx.LEFT, border=5)
        
        stpSiz.Add(wx.StaticText(pnl, -1, 'Base Name, file or folder:'),
                     pos=(gRow, 1), span=(1, 1), flag=wx.ALIGN_RIGHT|wx.LEFT, border=5)

        self.tcBaseName = wx.TextCtrl(pnl, -1)
        stpSiz.Add(self.tcBaseName, pos=(gRow, 2), span=(1, 3),
            flag=wx.ALIGN_LEFT|wx.EXPAND, border=5)

        gRow += 1
        self.tcDir = wx.TextCtrl(pnl, -1, style=wx.TE_MULTILINE)
        stpSiz.Add(self.tcDir, pos=(gRow, 0), span=(2, 5),
            flag=wx.ALIGN_LEFT|wx.LEFT|wx.BOTTOM|wx.EXPAND, border=5)
        gRow += 1 # space for the 2 grid rows for tcDir
        self.tcDir.SetValue('(save output in default directory)')

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

        gRow += 1
        self.tcProgress = wx.TextCtrl(pnl, -1, style=wx.TE_MULTILINE|wx.TE_READONLY)
        stpSiz.Add(self.tcProgress, pos=(gRow, 0), span=(4, 5),
            flag=wx.ALIGN_LEFT|wx.TOP|wx.LEFT|wx.BOTTOM|wx.EXPAND, border=5)
        gRow += 1 # space for the 4 grid rows for tcProgress
        gRow += 1
        gRow += 1

        # offer some estimate diagnostics
        self.tcProgress.AppendText('Time estimate for full dataset: ')
        fEstSecsPerQuery = 0.2
        # possibly call an estimation function here

        self.tcProgress.AppendText('(estimation not implemented yet)')
        gRow += 1
        self.btnSavePnl = wx.Button(pnl, label="Save\npanel", size=(-1, -1))
        self.btnSavePnl.Bind(wx.EVT_BUTTON, lambda evt: self.onClick_BtnSavePnl(evt))
        stpSiz.Add(self.btnSavePnl, pos=(gRow, 0), flag=wx.LEFT|wx.BOTTOM, border=5)

        stpSiz.Add(wx.StaticText(pnl, -1, 'Tasks:'),
                     pos=(gRow, 1), span=(1, 1), flag=wx.ALIGN_RIGHT|wx.TOP|wx.LEFT|wx.BOTTOM, border=5)

        lTasks = ['Make this NDVI dataset','Copy the current panel, which you can then vary']
        self.cbxTasks = wx.ComboBox(pnl, -1, choices=lTasks, style=wx.CB_READONLY)
        self.cbxTasks.Bind(wx.EVT_COMBOBOX, lambda evt: self.onCbxTasks(evt))
        stpSiz.Add(self.cbxTasks, pos=(gRow, 2), span=(1, 3), flag=wx.LEFT, border=5)

        pnl.SetSizer(stpSiz)
        pnl.SetAutoLayout(1)
        pnl.SetupScrolling()

    def onCkPreview(self, evt):
        if self.ckPreview.GetValue():
            self.spinPvwRows.Enable(True)
        else:
            self.spinPvwRows.Enable(False)

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

    def FillNDVISetupPanelFromCalcDict(self):
        """
        Fills the NDVI Setup panel from calcDict.
        Must explicitly clear a panel control if corresponding dictionary item is None because
        the panel may already have controls filled in from previous work.
        If all comboboxes in the panel correspond the dictionary items, maybe use a form like this:
            for object in self.parent.GetChildren(): 
                if type(object) == wx._controls.ComboBox: 
                    object.SetSelection(-1)
        """
        if self.calcDict['CalcName'] == None:
            self.tcCalcName.SetValue('')
        else:
            self.tcCalcName.SetValue('%s' % self.calcDict['CalcName'])
        # following is rarely used, not implemented yet
#        self.ckChartFromRefDay.SetValue(self.calcDict['ChartFromRefDay'])
#        if self.calcDict['RefDay'] != None:
#            self.tcRefDay.SetValue('%s' % self.calcDict['RefDay'])
        if self.calcDict['RefStationID'] == None:
            self.cbxRefStationID.SetSelection(-1)
        else:
            scidb.setComboboxToClientData(self.cbxRefStationID, self.calcDict['RefStationID'])
        if self.calcDict['IRRefSeriesID'] == None:
            self.cbxIRRefSeriesID.SetSelection(-1)
        else:
            scidb.setComboboxToClientData(self.cbxIRRefSeriesID, self.calcDict['IRRefSeriesID'])
        if self.calcDict['VISRefSeriesID'] == None:
            self.cbxVISRefSeriesID.SetSelection(-1)
        else:
            scidb.setComboboxToClientData(self.cbxVISRefSeriesID, self.calcDict['VISRefSeriesID'])
        self.ckUseRef.SetValue(self.calcDict['UseRef'])
        if self.calcDict['IRDataSeriesID'] == None:
            self.cbxIRDataSeriesID.SetSelection(-1)
        else:
            scidb.setComboboxToClientData(self.cbxIRDataSeriesID, self.calcDict['IRDataSeriesID'])
        if self.calcDict['VisDataSeriesID'] == None:
            self.cbxVisDataSeriesID.SetSelection(-1)
        else:
            scidb.setComboboxToClientData(self.cbxVisDataSeriesID, self.calcDict['VisDataSeriesID'])
        if self.calcDict['IRFunction'] == None:
            self.tcIRFunction.SetValue('=i')
        else:
            self.tcIRFunction.SetValue('%s' % self.calcDict['IRFunction'])
        if self.calcDict['VISFunction'] == None:
            self.tcVISFunction.SetValue('=v')
        else:
            self.tcVISFunction.SetValue('%s' % self.calcDict['VISFunction'])
        if self.calcDict['PlusMinusCutoffHours'] == None:
            self.tcPlusMinusCutoffHours.SetValue('2')
        else:
            self.tcPlusMinusCutoffHours.SetValue('%.1f' % self.calcDict['PlusMinusCutoffHours'])
        # Opt1ClrDayVsSetTholds ignored, always use percent thresholds of clear day
        if self.calcDict['ClearDay'] == None:
            self.tcClearDay.SetValue('')
        else:
            self.tcClearDay.SetValue('%s' % self.calcDict['ClearDay'])
        if self.calcDict['ThresholdPctLow'] == None:
            self.tcThresholdPctLow.SetValue('75')
        else:
            self.tcThresholdPctLow.SetValue('%d' % self.calcDict['ThresholdPctLow'])
        if self.calcDict['ThresholdPctHigh'] == None:
            self.tcThresholdPctHigh.SetValue('125')
        else:
            self.tcThresholdPctHigh.SetValue('%d' % self.calcDict['ThresholdPctHigh'])
        # not implemented: IRRefCutoff, VISRefCutoff, IRDatCutoff, VISDatCutoff
        self.ckUseOnlyValidNDVI.SetValue(self.calcDict['UseOnlyValidNDVI'])
        if self.calcDict['NDVIvalidMin'] == None:
            self.tcNDVIvalidMin.SetValue('-1')
        else:
            self.tcNDVIvalidMin.SetValue('%.2f' % self.calcDict['NDVIvalidMin'])
        if self.calcDict['NDVIvalidMax'] == None:
            self.tcNDVIvalidMax.SetValue('1')
        else:
            self.tcNDVIvalidMax.SetValue('%.2f' % self.calcDict['NDVIvalidMax'])
        self.ckIncludeSummaries.SetValue(self.calcDict['CreateSummaries'])
        self.ckIncludeSAS.SetValue(self.calcDict['OutputSAS'])
        self.ckNormalize.SetValue(self.calcDict['Normalize'])
        # set radio buttons, default false
        self.rbExcel.SetValue(0)
        self.rbTabDelim.SetValue(0)
        self.rbCommaDelim.SetValue(0)
        if self.calcDict['OutputFormat'] == 1:
            self.rbExcel.SetValue(1)
        if self.calcDict['OutputFormat'] == 2:
            self.rbTabDelim.SetValue(1)
        if self.calcDict['OutputFormat'] == 3:
            self.rbCommaDelim.SetValue(1)
        if self.calcDict['OutputBaseName'] == None:
            self.tcBaseName.SetValue('')
        else:
            self.tcBaseName.SetValue('%s' % self.calcDict['OutputBaseName'])
        if self.calcDict['OutputFolder'] == None:
            self.tcDir.SetValue('(save output in default directory)')
        else:
            self.tcDir.SetValue('%s' % self.calcDict['OutputFolder'])


    def InitDatesPanel(self, pnl):
        pnl.SetBackgroundColour('#0FFF0F')
        dtSiz = wx.GridBagSizer(0, 0)
        dtSiz.AddGrowableCol(0)
        
        gRow = 0
#        datesLabel = wx.StaticText(pnl, -1, "Dates")
#        dtSiz.Add(datesLabel, pos=(gRow, 0), span=(1, 1), flag=wx.TOP|wx.LEFT|wx.BOTTOM|wx.EXPAND, border=5)
        
#        gRow += 1
        self.datesList = ndviDatesList(pnl, -1, style = wx.LC_REPORT)
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
        self.stationsList = ndviStationsList(pnl, -1, style = wx.LC_REPORT)
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
        self.SavePanel()

    def SavePanel(self):
        self.FillDictFromNDVISetupPanel()
#        print 'self.calcDict:', self.calcDict
        print 'existing record ID:', self.calcDict['ID']
        self.calcNameToValidate = self.calcDict['CalcName']
        self.callsValidation = 'save' # flag for which fn calls validation
        if not self.validateCalcName():
            return
        # save the basic NDVI panel data
        recID = scidb.dictIntoTable_InsertOrReplace('NDVIcalc', self.calcDict)
        self.calcDict['ID'] = recID
        print 'new record ID:', self.calcDict['ID']
        self.refresh_cbxPanelsChoices(-1)
        # update the corresponding Dates and Stations from the selection lists
        # for Dates; clear any old, get new from list, and insert in DB
        stSQLDelDates = 'DELETE FROM NDVIcalcDates WHERE CalcID = ?'
        scidb.curD.execute(stSQLDelDates, (recID,))
        lSelectedDates = scidb.getListCtrlSelectionsAsTextList(self.datesList)
        print 'selected dates', lSelectedDates
        stSQLInsertDates = 'INSERT INTO NDVIcalcDates(CalcID, CalcDate) VALUES(?, ?)'
        lInsertDates = [(recID, d) for d in lSelectedDates]
        scidb.datConn.execute("BEGIN DEFERRED TRANSACTION") # much faster
        scidb.curD.executemany(stSQLInsertDates, lInsertDates)
        scidb.datConn.execute("COMMIT TRANSACTION")
        # for Stations; clear any old, get new from list, and insert in DB
        stSQLDelStas = 'DELETE FROM NDVIcalcStations WHERE CalcID = ?'
        scidb.curD.execute(stSQLDelStas, (recID,))
        lSelectedStationKeys = scidb.getListCtrlSelectionsAsKeysList(self.stationsList)
        print 'selected station keys', lSelectedStationKeys
        stSQLInsertStas = 'INSERT INTO NDVIcalcStations(CalcID, StationID) VALUES(?, ?)'
        lInsertStas = [(recID, s) for s in lSelectedStationKeys]
        scidb.datConn.execute("BEGIN DEFERRED TRANSACTION") # much faster
        scidb.curD.executemany(stSQLInsertStas, lInsertStas)
        scidb.datConn.execute("COMMIT TRANSACTION")

    def validateCalcName(self):
        """
        Called both on normal Save of panel, and when Duplicating a panel
        """
        if self.calcNameToValidate == None:
            wx.MessageBox('Need a Name for this Panel', 'Missing',
                wx.OK | wx.ICON_INFORMATION)
            if self.callsValidation == 'save': # flag for which fn called validation
                # called in normal Save from main panel
                self.tcCalcName.SetValue('') 
                self.tcCalcName.SetFocus()
#            self.Scroll(0, 0) # at the top
            return 0

        # check length
        maxLen = scidb.lenOfVarcharTableField('NDVIcalc', 'CalcName')
        if maxLen < 1:
            wx.MessageBox('Error %d getting [NDVIcalc].[CalcName] field length.' % maxLen, 'Error',
                wx.OK | wx.ICON_INFORMATION)
            return 0
        if len(self.calcNameToValidate) > maxLen:
            if self.callsValidation == 'save':
                wx.MessageBox('Max length for Panel name is %d characters.\n\nIf trimmed version is acceptable, retry.' % maxLen, 'Invalid',
                    wx.OK | wx.ICON_INFORMATION)
                self.calcNameToValidate = self.calcNameToValidate[:(maxLen)]
                self.tcCalcName.SetValue(self.calcNameToValidate)
                self.tcCalcName.SetFocus()
#                self.Scroll(0, 0) # scroll to the top
            if self.callsValidation == 'copy':
                wx.MessageBox('Max length for Panel name is %d characters.' % maxLen, 'Invalid',
                    wx.OK | wx.ICON_INFORMATION)
            return 0

        # check for existing CalcName
        stSQLCk = 'SELECT ID FROM NDVIcalc WHERE CalcName = ?'
        rec = scidb.curD.execute(stSQLCk, (self.calcNameToValidate, )).fetchone()
        if rec != None:
            if self.callsValidation == 'copy':
                # if there is any record at all, disallow attempt to copy onto same name
                wx.MessageBox('There is already a panel named "' + self.calcNameToValidate + '"', 'Duplicate',
                    wx.OK | wx.ICON_INFORMATION)
                return 0
            if rec['ID'] != self.calcDict['ID']:
                wx.MessageBox('There is already another panel named "' + self.calcNameToValidate + '"', 'Duplicate',
                    wx.OK | wx.ICON_INFORMATION)
                if self.callsValidation == 'save':
                    self.tcCalcName.SetValue(self.calcNameToValidate)
                    self.tcCalcName.SetFocus()
                    self.Scroll(0, 0) # at the top
                return 0
        return 1

    def FillDictFromNDVISetupPanel(self):
        self.calcDict['CalcName'] = scidb.getTextFromTC(self.tcCalcName)
        self.calcDict['RefStationID'] = scidb.getComboboxIndex(self.cbxRefStationID)
        self.calcDict['IRRefSeriesID'] = scidb.getComboboxIndex(self.cbxIRRefSeriesID)
        self.calcDict['VISRefSeriesID'] = scidb.getComboboxIndex(self.cbxVISRefSeriesID)
        self.calcDict['UseRef'] = scidb.getBoolFromCB(self.ckUseRef)
        self.calcDict['IRDataSeriesID'] = scidb.getComboboxIndex(self.cbxIRDataSeriesID)
        self.calcDict['VisDataSeriesID'] = scidb.getComboboxIndex(self.cbxVisDataSeriesID)
        self.calcDict['IRFunction'] = scidb.getTextFromTC(self.tcIRFunction, default = '=i')
        self.calcDict['VISFunction'] = scidb.getTextFromTC(self.tcVISFunction, default = '=v')
        self.calcDict['PlusMinusCutoffHours'] = scidb.getFloatFromTC(self.tcPlusMinusCutoffHours, default = 2)
        self.calcDict['ClearDay'] = scidb.getDateFromTC(self.tcClearDay) # if DateTime format, retrieve record will fail
        self.calcDict['ThresholdPctLow'] = scidb.getIntFromTC(self.tcThresholdPctLow, default = 75)
        self.calcDict['ThresholdPctHigh'] = scidb.getIntFromTC(self.tcThresholdPctHigh, default = 125)
        # not implemented: IRRefCutoff, VISRefCutoff, IRDatCutoff, VISDatCutoff
        self.calcDict['UseOnlyValidNDVI'] = scidb.getBoolFromCB(self.ckUseOnlyValidNDVI)
        self.calcDict['NDVIvalidMin'] = scidb.getFloatFromTC(self.tcNDVIvalidMin, default = -1)
        self.calcDict['NDVIvalidMax'] = scidb.getFloatFromTC(self.tcNDVIvalidMax, default = 1)
        self.calcDict['CreateSummaries'] = scidb.getBoolFromCB(self.ckIncludeSummaries)
        self.calcDict['OutputSAS'] = scidb.getBoolFromCB(self.ckIncludeSAS)
        self.calcDict['Normalize'] = scidb.getBoolFromCB(self.ckNormalize)
        # get output format from radio buttons
        if self.rbExcel.GetValue():
            self.calcDict['OutputFormat'] = 1
        if self.rbTabDelim.GetValue():
            self.calcDict['OutputFormat'] = 2
        if self.rbCommaDelim.GetValue():
            self.calcDict['OutputFormat'] = 3
        self.calcDict['OutputBaseName'] = scidb.getTextFromTC(self.tcBaseName)
        # <<--- maybe check for illegal file/folder name here
        stS = self.tcDir.GetValue()
        if stS == '(save output in default directory)':
            self.calcDict['OutputFolder'] = None
        else:
            if os.path.exists(stS):
                self.calcDict['OutputFolder'] = stS
            else:
                self.calcDict['OutputFolder'] = None

    def SaveDatesAndStations(self):
        """
        Saves the selcted Dates and Stations for the relevent Panel
        """
        print self.calcDict('ID')
        recID = self.calcDict('ID')
        
    def onCbxRetrievePanel(self, event):
        k = scidb.getComboboxIndex(self.cbxGetPanel)
        if self.calcDict['ID'] != None:
            self.SavePanel() # attempt to save panel, will catch errors
#        print 'self.cbxGetPanel selected, key:', k
        self.calcDict = scidb.dictFromTableID('NDVIcalc', k)
        self.retrievePanelFromDict()

    def retrievePanelFromDict(self):
        k = self.calcDict['ID']
        print 'in retrievePanelFromDict, k=', k
        self.FillNDVISetupPanelFromCalcDict()

        # retrieve stored Dates for this panel
        stSQLDtSels = 'SELECT CalcDate FROM NDVIcalcDates WHERE CalcID = ? ORDER BY CalcDate;'
        DtRecs = scidb.curD.execute(stSQLDtSels, (k, )).fetchall()
        lDts = [dtRec['CalcDate'].strftime('%Y-%m-%d') for dtRec in DtRecs]
#        print 'lDts', lDts
        # go through the list and select/deselect
        for i in range(self.datesList.GetItemCount()):
            if self.datesList.GetItemText(i) in lDts:
                # select item
                self.datesList.SetItemState(i, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
            else:
                # deselect item
                self.datesList.SetItemState(i, 0, wx.LIST_STATE_SELECTED)

        # retrieve stored Stations for this panel
        stSQLStaSels = 'SELECT StationID FROM NDVIcalcStations WHERE CalcID = ? ORDER BY StationID;'
        StaRecs = scidb.curD.execute(stSQLStaSels, (k, )).fetchall()
        lStas = [staRec['StationID'] for staRec in StaRecs]
        # go through the list and select/deselect
        for i in range(self.stationsList.GetItemCount()):
            if self.stationsList.GetItemData(i) in lStas:
                self.stationsList.SetItemState(i, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
            else:
                self.stationsList.SetItemState(i, 0, wx.LIST_STATE_SELECTED)

    def onCbxTasks(self, event):
#        print 'self.cbxTasks selected, choice: "', self.cbxTasks.GetValue(), '"'
        iCmd = self.cbxTasks.GetSelection()
        if iCmd == 0: # make this dataset
            boolMakingDataset = True
            self.createDataSet()
            boolMakingDataset = False
        if iCmd == 1: # duplicate the current panel
            boolMakingDataset = True
            self.replicateCurrentPanel()
            boolMakingDataset = False


    def replicateCurrentPanel(self):
        if self.calcDict['ID'] == None:
            stMsg = 'This is a new empty panel.\nIf you really want to copy it, Save it first.'
            dlg = wx.MessageDialog(self, stMsg, 'Empty')
            result = dlg.ShowModal()
            dlg.Destroy()
            return
        self.SavePanel() # attempt to save panel, will catch errors
        dlg = wx.TextEntryDialog(None, "Name for the new copy of this panel.", "New Name", " ")
        answer = dlg.ShowModal()
        if answer == wx.ID_OK:

            # clean up whitespace; remove leading/trailing & multiples
            stS = " ".join(dlg.GetValue().split())
            if stS == '':
                self.calcNameToValidate = None
            else:
                self.calcNameToValidate = stS
#            self.calcNameToValidate = dlg.GetValue()
        else:
            self.calcNameToValidate = None
        dlg.Destroy()
        self.callsValidation = 'copy' # flag for which fn calls validation
        if not self.validateCalcName():
            return
        # insert any more validation here
        self.calcDict['CalcName'] = self.calcNameToValidate # substitute the validated name
        prevRecID = self.calcDict['ID'] # remember
        self.calcDict['ID'] = None # so it will save as a new record
        recID = scidb.dictIntoTable_InsertOrReplace('NDVIcalc', self.calcDict) # store the new record
        stSQLdupDates = 'INSERT INTO NDVIcalcDates (CalcID, CalcDate) ' \
                        'SELECT ? AS NewCalcID, CalcDate FROM NDVIcalcDates ' \
                        'WHERE CalcID = ?'
        scidb.curD.execute(stSQLdupDates, (recID, prevRecID))

        stSQLdupStations = 'INSERT INTO NDVIcalcStations (CalcID, StationID) ' \
                        'SELECT ? AS NewCalcID, StationID FROM NDVIcalcStations ' \
                        'WHERE CalcID = ?'
        scidb.curD.execute(stSQLdupStations, (recID, prevRecID))
        self.calcDict['ID'] = recID
        self.retrievePanelFromDict()
        self.refresh_cbxPanelsChoices(-1)

        dlg = wx.MessageDialog(self, 'You will now be viewing the copy, which you can edit', 'Panel Copied')
        result = dlg.ShowModal()
        dlg.Destroy()
            

    def createDataSet(self):
        """
        Creates NDVI datasets based on options selected in the form
        """
        # first, a lot of validity checking
        if self.calcDict['ID'] == None:
            wx.MessageBox('This is a new empty panel.\nIf you really want ' \
                'to use it, Save it first.', 'Empty',
                wx.OK | wx.ICON_INFORMATION)
            return
        self.SavePanel() # attempt to save panel, will catch
                        #  errors including missing/invalid CalcName
        # displaysaved panel, including any automatic correction/formatting
        self.FillNDVISetupPanelFromCalcDict()
        # check that at least one date is selected
        stSQL = 'SELECT CalcDate FROM NDVIcalcDates WHERE CalcID = ? ORDER BY CalcDate'
        recs = scidb.curD.execute(stSQL, (self.calcDict['ID'],)).fetchall()
        if len(recs) == 0:
            wx.MessageBox('Please select at least one date you want data for.', 'Missing',
                wx.OK | wx.ICON_INFORMATION)
            return
        # if OK, get dates list
        lDates = [r['CalcDate'] for r in recs]
        
        # check that at least one station selected
        stSQL = 'SELECT StationID FROM NDVIcalcStations WHERE CalcID = ? ORDER BY StationID'
        recs = scidb.curD.execute(stSQL, (self.calcDict['ID'],)).fetchall()
        if len(recs) == 0:
            wx.MessageBox('Please select at least one station you want data for.', 'Missing',
                wx.OK | wx.ICON_INFORMATION)
            return
        # if OK, get stations list
        lStaIDs = [r['StationID'] for r in recs]

        # if UseRef, check that reference Station, IR & Vis series are selected
        if self.calcDict['UseRef'] == 1:
            if self.calcDict['RefStationID'] == None:
                wx.MessageBox('Please select the Reference station.', 'Missing',
                    wx.OK | wx.ICON_INFORMATION)
                self.cbxRefStationID.SetFocus()
                return
            if self.calcDict['IRRefSeriesID'] == None:
                wx.MessageBox('Please select the Series that includes IR for the reference station.', 'Missing',
                    wx.OK | wx.ICON_INFORMATION)
                self.cbxIRRefSeriesID.SetFocus()
                return
            if self.calcDict['VISRefSeriesID'] == None:
                wx.MessageBox('Please select the Series that includes Visible for the reference station.', 'Missing',
                    wx.OK | wx.ICON_INFORMATION)
                self.cbxVISRefSeriesID.SetFocus()
                return

        # check that IR data series is selected
        if self.calcDict['IRDataSeriesID'] == None:
            wx.MessageBox('Please select the Series that includes IR for the data stations.', 'Missing',
                wx.OK | wx.ICON_INFORMATION)
            self.cbxIRDataSeriesID.SetFocus()
            return

        # check that VIS data series is selected
        if self.calcDict['VisDataSeriesID'] == None:
            wx.MessageBox('Please select the Series that includes Visible for the data stations.', 'Missing',
                wx.OK | wx.ICON_INFORMATION)
            self.cbxVisDataSeriesID.SetFocus()
            return

        # if UseOnlyValidNDVI, check that min & max are entered, and min is less than max
        if self.calcDict['UseOnlyValidNDVI'] == 1:
            if self.calcDict['NDVIvalidMin'] == None:
                wx.MessageBox('Please enter the minimum for NDVI (or un-check ' \
                        '"Use only ... <= NDVI <= ...").', 'Missing',
                    wx.OK | wx.ICON_INFORMATION)
                self.tcNDVIvalidMin.SetFocus()
                return
            if self.calcDict['NDVIvalidMax'] == None:
                wx.MessageBox('Please enter the maximum for NDVI (or un-check ' \
                        '"Use only ... <= NDVI <= ...").', 'Missing',
                    wx.OK | wx.ICON_INFORMATION)
                self.tcNDVIvalidMax.SetFocus()
                return
            if self.calcDict['NDVIvalidMax'] <= self.calcDict['NDVIvalidMin']:
                wx.MessageBox('Maximim NDVI cutoff must be greater than ' \
                        'minimum.', 'Invalid',
                    wx.OK | wx.ICON_INFORMATION)
                self.tcNDVIvalidMax.SetFocus()
                return

        # Check that clear day has been entered
        if self.calcDict['ClearDay'] == None:
            wx.MessageBox('Please enter a date that was clear ' \
                'during the cutoff hours +/- solar noon.\n' \
                'After you select a Reference station and IR series, you can ' \
                'float over the Dates list to preview daily irradiance traces. ' \
                'Clear days have a bell-shaped curve.\nIf curves are not ' \
                'centered, make sure you have Longitude entered correctly using ' \
                'the Stations module.', 'Missing',
                wx.OK | wx.ICON_INFORMATION)
            self.tcClearDay.SetFocus()
            return

        # check if everything is OK for Excel output
        if self.calcDict['OutputFormat'] == 1: # radio button for Excel format
#            print 'in Excel validation'
            # verify we can create Excel files at all
            if hasCom == False: # we tested for this at the top of this module
                wx.MessageBox(' This operating system cannot make Excel files.\n' \
                    ' Choose another option under "Output As:"', 'Info',
                    wx.OK | wx.ICON_INFORMATION)
                return
#            print 'passed validation for being able to make Excel files'
            # check for invalid worksheet names
            stStationIDs = ",".join(str(n) for n in lStaIDs)
#            print 'Station IDs to check', stStationIDs
            stSQL = """SELECT StationName,
            SpreadsheetName(StationName) AS ValidName
            FROM Stations WHERE ID IN ({sSs})
            AND StationName != ValidName;
            """.format(sSs=stStationIDs)
#            print stSQL
            recs = scidb.curD.execute(stSQL).fetchall()
#            print 'number of invalid Station names found', len(recs)
            if len(recs) > 0:
                wx.MessageBox(' Excel output uses Station names for worksheet names. \n' \
                    ' Some of these either contain invalid characters or are too long ' \
                    '(>25 characters).\n The names, and validated versions, will be ' \
                    'output as a spreadsheet. Change them using the "Stations" module.', 'Info',
                    wx.OK | wx.ICON_INFORMATION)
                if scidb.outputRecsAsSpreadsheet(recs) == 0:
                    wx.MessageBox(' Excel output failed. Look at system window for bad sheet names.', 'Error',
                    wx.OK | wx.ICON_INFORMATION)
                    # at least print them
                    for rec in recs:
                        for recName in rec.keys():
                            print recName, rec[recName]
#                wx.MessageBox(' Excel output not implemented yet', 'Under Construction',
#                    wx.OK | wx.ICON_INFORMATION)
                return
            # done with verification of Excel format, set up functions
            # (think of a way to pre-test them)
            # tidy up, assure only one equal sign in front
            iFormula = '=' +  self.calcDict['IRFunction'].strip('=').strip()
            # e.g. '=i-(0.21*v)'
            # use relative reference in final spreadsheet,
            # the raw IR band will be -4 columns to the left relative to the IR fn we are creating
            # the raw Vis band will be -3 columns left of the created IR fn
            # replace 'i' with 'RC[-4]'; replace 'v' with 'RC[-3]'
            xlIRFn = iFormula.replace('i','RC[-4]').replace('v','RC[-3]')
            vFormula = '=' +  self.calcDict['VISFunction'].strip('=').strip()
            # the raw IR band will be -5 columns left of the created Vis fn
            # the raw Vis band will be -4 columns left of the created Vis fn
            # replace 'i' with 'RC[-5]'; replace 'v' with 'RC[-4]'
            xlVisFn = vFormula.replace('i','RC[-5]').replace('v','RC[-4]')
            # NDVI = (IR - VIS)/(IR + VIS)
            if self.calcDict['UseRef'] == 1:
                # NDVI = ((IRdata/IRref) - (VISdata/VISref))/((IRdata/IRref) + (VISdata/VISref))
                xlNDVIFn = '=((RC[-2]/RC[-4]) - (RC[-1]/RC[-3]))/' \
                            '((RC[-2]/RC[-4]) + (RC[-1]/RC[-3]))'
            else: # not using reference
                # NDVI = ((IRdata) - (VISdata))/((IRdata) + (VISdata))
                xlNDVIFn = '=((RC[-2]) - (RC[-1]))/((RC[-2]) + (RC[-1]))'
        if self.calcDict['OutputFormat'] in (2, 3): # one of the text output formats
            # assign IR and VIS formulas to DB functions, so can use them in SQLite queries
            print "self.calcDict['IRFunction']", self.calcDict['IRFunction']
            print "self.calcDict['VISFunction']", self.calcDict['VISFunction']
            iFormula = self.calcDict['IRFunction'].strip('=').strip()
            try: # assign the infrared-band formula
                scidb.assignDBFn(iFormula, 'getIR')
                # test the formula on the database
                try:
                    scidb.curD.execute('SELECT getIR(1,1) AS test').fetchall()
                except:
                    wx.MessageBox('IR formula is not valid. For text output, make sure this has correct Python syntax.', 'Error',
                            wx.OK | wx.ICON_INFORMATION)
                    self.tcIRFunction.SetFocus()
                    return
            except:
                wx.MessageBox('IR formula is not valid. For text output, make sure this has correct Python syntax.', 'Error',
                        wx.OK | wx.ICON_INFORMATION)
                self.tcIRFunction.SetFocus()
                return

            vFormula = self.calcDict['VISFunction'].strip('=').strip()
            try: # assign the visible-band formula
                scidb.assignDBFn(vFormula, 'getVis')
                # test the formula on the database
                try:
                    scidb.curD.execute('SELECT getVis(1,1) AS test').fetchall()
                except:
                    wx.MessageBox('VIS formula is not valid. For text output, make sure this has correct Python syntax.', 'Error',
                            wx.OK | wx.ICON_INFORMATION)
                    self.tcVISFunction.SetFocus()
                    return
            except:
                wx.MessageBox('VIS formula is not valid. For text output, make sure this has correct Python syntax.', 'Error',
                        wx.OK | wx.ICON_INFORMATION)
                self.tcVISFunction.SetFocus()
                return

        # have user verify folder
        stDir = self.calcDict['OutputFolder']
        if (stDir == None) or (not os.path.exists(stDir)):
            stDir = os.path.expanduser('~') # user doesn't like default? choose one
            stMsg = ' No valid save folder is chosen. File(s) will be saved in:' \
                    '\n\n%s\n\n If you want to use a different folder, Cancel here and choose ' \
                    'a folder.' % (stDir,)
            dlg = wx.MessageDialog(self, stMsg, 'Default Folder', wx.OK | wx.CANCEL | wx.ICON_INFORMATION)
            result = dlg.ShowModal()
            dlg.Destroy()
            if result != wx.ID_OK:
                self.onClick_BtnGetDir(-1)
                return

            self.calcDict['OutputFolder'] = stDir

        if self.calcDict['OutputBaseName'] == None:
            wx.MessageBox('Need a "Base Name", which will be the file name for Excel output, or ' \
                'the folder name for text output.', 'Missing',
                        wx.OK | wx.ICON_INFORMATION)
            self.tcBaseName.SetFocus()
            return

        stSavePath = os.path.join(stDir, self.calcDict['OutputBaseName'])
        # if Excel output, stSavePath will be the source of filenames for whole workbooks
        # if text output, stSavePath will be the folder name that sets of files are created in
        print "stSavePath:", stSavePath

        if self.calcDict['OutputFormat'] in (2, 3): # one of the text output formats
            # check if the folder exists and is empty
            try: # error if folder does not exist
                L = os.listdir(stSavePath)
                if L != []:
                    stMsg = ' The folder to save files in is not empty:\n\n%s\n\n Do you want to ' \
                        'clear it? If you do not, new files will overwrite files of the same name and ' \
                        'it may be confusing which previously existed. If any files are open, output will ' \
                        'crash.\n\n Clear this folder?' % (stSavePath,)
                    dlg = wx.MessageDialog(self, stMsg, 'Non-Empty Folder', wx.YES_NO | wx.ICON_QUESTION)
                    result = dlg.ShowModal()
                    dlg.Destroy()
        #            print "result of Yes/No dialog:", result
                    if result == wx.ID_YES:
                        try:
                            shutil.rmtree(stSavePath)
                        except:
                            wx.MessageBox("Can't clear folder. Are files open?", 'Info',
                                wx.OK | wx.ICON_INFORMATION)
                            return
                        wx.Yield() # allow window updates to occur
                        # sometimes a race condition causes the following to fail
                        try:
                            os.mkdir(stSavePath)
                        except:
                            wx.MessageBox("Can't re-create folder. Try again.", 'Info',
                                wx.OK | wx.ICON_INFORMATION)
                            return
                            
            except: # folder does not exist, create it
                os.mkdir(stSavePath)

        # validation complete, enter any more above
#        print ">>>>validation complete"

        # remember start time
        dtJobStarted = datetime.datetime.now()
        print 'dtJobStarted', dtJobStarted
        # get values used by most options:

        # get column header strings
        if self.calcDict['UseRef'] == 1:
            stIRRefTxt = self.cbxIRRefSeriesID.GetStringSelection()
            stVISRefTxt = self.cbxVISRefSeriesID.GetStringSelection()
            # get reference high/low cutoffs here, to use for all stations
            # will get data cutoffs later for each station
            fIRRefLowCutoff, fIRRefHighCutoff = scidb.GetHighLowCutoffs(dtClearDay = self.calcDict['ClearDay'],
                iStationID = self.calcDict['RefStationID'],
                iSeriesID = self.calcDict['IRRefSeriesID'],
                fPlusMinusHoursCutoff = self.calcDict['PlusMinusCutoffHours'],
                fPercentOfMaxLow = self.calcDict['ThresholdPctLow'],
                fPercentOfMaxHigh = self.calcDict['ThresholdPctHigh'])
            fVISRefLowCutoff, fVISRefHighCutoff = scidb.GetHighLowCutoffs(dtClearDay = self.calcDict['ClearDay'],
                iStationID = self.calcDict['RefStationID'],
                iSeriesID = self.calcDict['VISRefSeriesID'],
                fPlusMinusHoursCutoff = self.calcDict['PlusMinusCutoffHours'],
                fPercentOfMaxLow = self.calcDict['ThresholdPctLow'],
                fPercentOfMaxHigh = self.calcDict['ThresholdPctHigh'])
        else:
            stIRRefTxt = 'no_IR'
            stVISRefTxt = 'no_Vis'
        stIRDatTxt = self.cbxIRDataSeriesID.GetStringSelection()
        stVISDatTxt = self.cbxVisDataSeriesID.GetStringSelection()
        # check
#        if self.calcDict['UseRef'] == 1:
#            print 'stIRRefTxt', stIRRefTxt
#            print 'stVISRefTxt', stVISRefTxt
#            print 'IR cutoffs', fIRRefLowCutoff, fIRRefHighCutoff
#            print 'vis cutoffs', fVISRefLowCutoff, fVISRefHighCutoff
#        print 'stIRDatTxt', stIRDatTxt
#        print 'stVISDatTxt', stVISDatTxt
        
        iShNumSAS = 0
        iRowSAS = 0
        iNumStationsDone = 0
        if self.calcDict['OutputFormat'] == 1: #Excel output format
            stWkBookPath = stSavePath + '.xlsx'
            if hasCom == False: # we tested for this at the top of this module
                wx.MessageBox('This operating system cannot make Excel files', 'Info',
                    wx.OK | wx.ICON_INFORMATION)
                return

            if os.path.isfile(stWkBookPath):
                stMsg = 'File:\n\n' + stWkBookPath + '\n\n already exists. Overwrite?'
                dlg = wx.MessageDialog(self, stMsg, 'File Exists', wx.YES_NO | wx.ICON_QUESTION)
                result = dlg.ShowModal()
                dlg.Destroy()
    #            print "result of Yes/No dialog:", result
                if result == wx.ID_YES:
                    try:
                        os.remove(stWkBookPath)
                    except:
                        wx.MessageBox("Can't delete old file. Is it still open?", 'Info',
                            wx.OK | wx.ICON_INFORMATION)
                        return
                else:
                    return
            if self.calcDict['OutputSAS'] == 1:
                stSASBookPath = stSavePath + '_SAS.xlsx'
                if os.path.isfile(stSASBookPath):
                    stMsg = 'The SAS workbook, file:\n\n' + stSASBookPath + '\n\n already exists. Overwrite?'
                    dlg = wx.MessageDialog(self, stMsg, 'File Exists', wx.YES_NO | wx.ICON_QUESTION)
                    result = dlg.ShowModal()
                    dlg.Destroy()
        #            print "result of Yes/No dialog:", result
                    if result == wx.ID_YES:
                        try:
                            os.remove(stSASBookPath)
                        except:
                            wx.MessageBox("Can't delete old file. Is it still open?", 'Info',
                                wx.OK | wx.ICON_INFORMATION)
                            return
                    else:
                        return
                
            try:
                oXL = win32com.client.Dispatch("Excel.Application")
                oXL.Visible = 1
            except:
                wx.MessageBox('Excel is not on this computer', 'Info',
                    wx.OK | wx.ICON_INFORMATION)
                return
            wx.Yield() # allow window updates to occur
            bXL = oXL.Workbooks.Add()
            wx.Yield()
            #remove any extra sheets
            while bXL.Sheets.Count > 1:
        #                    print "Workbook has this many sheets:", bXL.Sheets.Count
                bXL.Sheets(1).Delete()
            shXL = bXL.Sheets(1)
            # track whether a new sheet is needed, because there must always be at least 1
            boolNewBlankSheet = True
            if self.calcDict['CreateSummaries'] == 1:
                boolNewBlankSummarySheet = False
            wx.Yield()
            # before we go any further, try saving file
            try:
                bXL.SaveAs(stWkBookPath) # make sure there's nothing invalid about the filename
            except:
                wx.MessageBox('Can not save file:\n\n"' + stWkBookPath + '"', 'Info',
                    wx.OK | wx.ICON_INFORMATION)
                return
            wx.Yield()
            self.tcProgress.SetValue(' Creating Excel file "' + stWkBookPath + '"\n')
            wx.Yield()
            
            if self.calcDict['OutputSAS'] == 1:
                bXL_SAS = oXL.Workbooks.Add()
                wx.Yield()
                #remove any extra sheets
                while bXL_SAS.Sheets.Count > 1:
            #                    print "Workbook has this many sheets:", bXL.Sheets.Count
                    bXL_SAS.Sheets(1).Delete()
                shXL_SAS = bXL_SAS.Sheets(1)
                # track whether a new sheet is needed, because there must always be at least 1
                boolNewBlankSASSheet = True
                # before we go any further, try saving file
                try:
                    bXL_SAS.SaveAs(stSASBookPath) # make sure there's nothing invalid about the filename
                except:
                    wx.MessageBox('Can not save SAS file:\n\n"' + stSASBookPath + '"', 'Info',
                        wx.OK | wx.ICON_INFORMATION)
                    return
                wx.Yield()

        for iStID in lStaIDs:
            stSQL = 'SELECT StationName FROM Stations WHERE ID = ?'
            stDataStation = scidb.curD.execute(stSQL, (iStID,)).fetchone()['StationName']
            fIRDatLowCutoff, fIRDatHighCutoff = scidb.GetHighLowCutoffs(dtClearDay = self.calcDict['ClearDay'],
                iStationID = iStID,
                iSeriesID = self.calcDict['IRDataSeriesID'],
                fPlusMinusHoursCutoff = self.calcDict['PlusMinusCutoffHours'],
                fPercentOfMaxLow = self.calcDict['ThresholdPctLow'],
                fPercentOfMaxHigh = self.calcDict['ThresholdPctHigh'])
            fVISDatLowCutoff, fVISDatHighCutoff = scidb.GetHighLowCutoffs(dtClearDay = self.calcDict['ClearDay'],
                iStationID = iStID,
                iSeriesID = self.calcDict['VisDataSeriesID'],
                fPlusMinusHoursCutoff = self.calcDict['PlusMinusCutoffHours'],
                fPercentOfMaxLow = self.calcDict['ThresholdPctLow'],
                fPercentOfMaxHigh = self.calcDict['ThresholdPctHigh'])
            print 'stDataStation', stDataStation, 'cutoffs', fIRDatLowCutoff, fIRDatHighCutoff, fVISDatLowCutoff, fVISDatHighCutoff
            if self.calcDict['OutputFormat'] == 1: # Excel output format
                if boolNewBlankSheet == False:
#                    self.tcOutputOptInfo.SetValue(self.tcOutputOptInfo.GetValue() + 'Sheet "' + shXL.Name + '"\n')
#                    print 'existing sheet', shXL.Name
#                    sPrevShNm = shXL.Name
                    shXL = bXL.Sheets.Add() # this works, and is the expected new sheet 1st in the book
                    print 'after new sheet create', shXL.Name # this works
                    #shXL.Move(After=bXL.Sheets(sPrevShNm)) # this moves sheet to a new book, then crashes
#                    oXL.Worksheets.Add(After=oXL.Sheets(sPrevShNm)) # creats sheet, but 1st in the book
#                    #worksheets.Add(After=worksheets(worksheets.Count)) # creats sheet, but 1st in the book 
#                    shXL = oXL.ActiveSheet
                    shXL = bXL.ActiveSheet
#                    print 'after new sheet create', shXL.Name
                    boolNewBlankSheet = True
                shXL.Name = stDataStation
                print 'after new sheet rename', shXL.Name
                boolNewlyNamedWorksheet = True
                iSSRow = 1
                if self.calcDict['CreateSummaries'] == 1:
                    if boolNewBlankSummarySheet == False:
                        shXLSummary = bXL.Sheets.Add() # adds at front of workbook
                        # shXLSummary = bXL.ActiveSheet # is this needed?
                        boolNewBlankSummarySheet = True
                    shXLSummary.Name = stDataStation + ' Summary'
                    iSSummaryRow = 1
                    # column headings are definite at this point, put them in
                    shXLSummary.Cells(iSSummaryRow,1).Value = 'Date'
                    shXLSummary.Cells(iSSummaryRow,2).Value = 'Avg'
                    shXLSummary.Cells(iSSummaryRow,3).Value = 'StDev'
                    shXLSummary.Cells(iSSummaryRow,4).Value = 'Count'
                    shXLSummary.Cells(iSSummaryRow,5).Value = 'Use?'
                    shXLSummary.Cells(iSSummaryRow,6).Value = 'NDVI'
                    shXLSummary.Cells(iSSummaryRow,7).Value = 'SEM'
                    iSSummaryRow += 1
                    iFirstRowInBlock = iSSRow + 1 # sheet row will be 1 higher when headers added

                if self.calcDict['OutputSAS'] == 1:
                    if boolNewBlankSASSheet == False:
                        shXL_SAS = bXL_SAS.Sheets.Add() # adds at front of workbook
                        boolNewBlankSASSheet = True
                    shXL_SAS.Name = stDataStation
                    iSASRow = 1
                    # column headings are definite at this point, put them in
                    shXL_SAS.Cells(iSASRow,1).Value = 'Date'
                    shXL_SAS.Cells(iSASRow,2).Value = 'RefDay'
                    shXL_SAS.Cells(iSASRow,3).Value = 'VI'
                    iSASRow += 1
                    
            if self.calcDict['OutputFormat'] in (2, 3): # one of the text output formats
                if self.calcDict['OutputFormat'] == 2:
                    stFilePath = os.path.join(stSavePath, stDataStation) + '.txt'
                if self.calcDict['OutputFormat'] == 3:
                    stFilePath = os.path.join(stSavePath, stDataStation) + '.csv'
                try: # before we go any further
                    # make sure there's nothing invalid about the filename
                    fOut = open(stFilePath, 'wb') 
                except:
                    wx.MessageBox(' Can not create file:\n\n' + stFilePath, 'Info',
                        wx.OK | wx.ICON_INFORMATION)
                    return
                if self.calcDict['CreateSummaries'] == 1:
                    if self.calcDict['OutputFormat'] == 2:
                        stFilePathSummary = os.path.join(stSavePath, stDataStation) + '_Summary.txt'
                    if self.calcDict['OutputFormat'] == 3:
                        stFilePathSummary = os.path.join(stSavePath, stDataStation) + '_Summary.csv'
                    try: # before we go any further
                        # make sure there's nothing invalid about the filename
                        fOutSummary = open(stFilePathSummary, 'wb') 
                    except:
                        wx.MessageBox(' Can not create file:\n\n' + stFilePathSummary, 'Info',
                            wx.OK | wx.ICON_INFORMATION)
                        return

                if self.calcDict['OutputSAS'] == 1:
                    if self.calcDict['OutputFormat'] == 2:
                        stFilePathSAS = os.path.join(stSavePath, stDataStation) + '_SAS.txt'
                    if self.calcDict['OutputFormat'] == 3:
                        stFilePathSAS = os.path.join(stSavePath, stDataStation) + '_SAS.csv'
                    try: # before we go any further
                        # make sure there's nothing invalid about the filename
                        fOutSAS = open(stFilePathSAS, 'wb') 
                    except:
                        wx.MessageBox(' Can not create file:\n\n' + stFilePathSAS, 'Info',
                            wx.OK | wx.ICON_INFORMATION)
                        return

                if self.calcDict['OutputFormat'] == 2:
                    cDl='\t' # tab delimited
                if self.calcDict['OutputFormat'] == 3:
                    cDl=',' # comma-separated
                wr = csv.writer(fOut, delimiter=cDl, quotechar='"', quoting=csv.QUOTE_MINIMAL)
                if  self.calcDict['CreateSummaries'] == 1:
                    wrSummary = csv.writer(fOutSummary, delimiter=cDl, quotechar='"', quoting=csv.QUOTE_MINIMAL)
                if self.calcDict['OutputSAS'] == 1:
                    wrSAS = csv.writer(fOutSAS, delimiter=cDl, quotechar='"', quoting=csv.QUOTE_MINIMAL)
                
                isNewTextFile = 1

            iNumStationsDone += 1
            iNumDatesDone = 0
            for dDt in lDates:
                iNumDatesDone += 1
                self.tcProgress.SetValue('Doing station %d of %d , day %d of %d' % (iNumStationsDone,
                        len(lStaIDs), iNumDatesDone, len(lDates)))
                self.tcProgress.AppendText(', elapsed time: ' +
                        scidb.timeIntervalAsStandardString(dtJobStarted,
                        datetime.datetime.now()))
                print 'elapsed time: ', scidb.timeIntervalAsStandardString(dtJobStarted,
                        datetime.datetime.now())
                if self.calcDict['UseRef'] == 1:
                    numItems = scidb.GetDaySpectralData(dateCur = dDt,
                        fPlusMinusCutoff = self.calcDict['PlusMinusCutoffHours'],
                        iRefStation = self.calcDict['RefStationID'],
                        iIRRefSeries = self.calcDict['IRRefSeriesID'],
                        iVisRefSeries = self.calcDict['VISRefSeriesID'],
                        iDataStation = iStID,
                        iIRDataSeries = self.calcDict['IRDataSeriesID'],
                        iVisDataSeries = self.calcDict['VisDataSeriesID'])
                    stSQL = """DELETE FROM tmpSpectralData
                    WHERE IRRef < {irl} OR IRRef > {irh}
                    OR VISRef < {vrl} OR VISRef > {vrh}
                    OR IRData < {idl} OR IRData > {idh}
                    OR VISData < {vdl} OR VISData > {vdh}
                    """.format(irl=fIRRefLowCutoff, irh=fIRRefHighCutoff,
                               vrl=fVISRefLowCutoff, vrh=fVISRefHighCutoff,
                               idl=fIRDatLowCutoff, idh=fIRDatHighCutoff,
                               vdl=fVISDatLowCutoff, vdh=fVISDatHighCutoff)
                    scidb.curD.execute(stSQL)
                    print dDt, 'before/after threshold deletions', numItems, scidb.countTableFieldItems('tmpSpectralData','ID')
                    if self.calcDict['OutputFormat'] in (2, 3):
                        # fill explicit numbers into the other fields in the table
                        stSQL = """
                        UPDATE tmpSpectralData
                        SET rir = getIR(IRRef, VISRef), rvi = getVis(IRRef, VISRef),
                        dir = getIR(IRData, VISData), dvi = getVis(IRData, VISData);
                        """
                        scidb.curD.execute(stSQL)
                        stSQL = """
                        UPDATE tmpSpectralData
                        SET ndvi = ((dir/rir) - (dvi/rvi))/((dir/rir) + (dvi/rvi));
                        """
                        scidb.curD.execute(stSQL)
                else: # not using reference
                    numItems = scidb.GetDaySpectralData(dateCur = dDt,
                        fPlusMinusCutoff = self.calcDict['PlusMinusCutoffHours'],
                        iDataStation = iStID,
                        iIRDataSeries = self.calcDict['IRDataSeriesID'],
                        iVisDataSeries = self.calcDict['VisDataSeriesID'])
                    stSQL = """DELETE FROM tmpSpectralData
                    WHERE IRData < {idl} OR IRData > {idh}
                    OR VISData < {vdl} OR VISData > {vdh}
                    """.format(idl=fIRDatLowCutoff, idh=fIRDatHighCutoff,
                               vdl=fVISDatLowCutoff, vdh=fVISDatHighCutoff)
                    scidb.curD.execute(stSQL)
                    print dDt, 'before/after threshold deletions', numItems, scidb.countTableFieldItems('tmpSpectralData','ID')
                    if self.calcDict['OutputFormat'] in (2, 3):
                        # fill explicit numbers into the other fields in the table
                        stSQL = """
                        UPDATE tmpSpectralData
                        SET dir = getIR(IRData, VISData), dvi = getVis(IRData, VISData);
                        """
                        scidb.curD.execute(stSQL)
                        stSQL = """
                        UPDATE tmpSpectralData
                        SET ndvi = (dir - dvi)/(dir + dvi);
                        """
                        scidb.curD.execute(stSQL)
                # done with useRef, we now have NDVI calculated either with a reference or without
                if self.calcDict['UseOnlyValidNDVI'] == 1:
                    stSQL = """DELETE FROM tmpSpectralData
                    WHERE ndvi < {min} OR ndvi > {max};
                    """.format(min=self.calcDict['NDVIvalidMin'], max=self.calcDict['NDVIvalidMax'])
                    scidb.curD.execute(stSQL)
                
                # got complete data for this date into tmpSpectralData
                wx.Yield() # allow window updates to occur
                # get numbers, whether we use them directly or substitute spreadsheet formulas
                stSQL = """SELECT Timestamp, IRRef AS "{rIR}_Ref", VISRef AS "{rVI}_Ref",
                IRData AS "{dIR}_Data", VISData AS "{dDA}_Data",
                rir AS "IR ref", rvi AS "VIS ref", dir AS "IR data", dvi AS "VIS data", ndvi AS "NDVI"
                FROM tmpSpectralData ORDER BY Timestamp
                """.format(rIR=stIRRefTxt, rVI=stVISRefTxt, dIR=stIRDatTxt, dDA=stVISDatTxt)
                recs = scidb.curD.execute(stSQL).fetchall()
                for rec in recs:
                    if self.calcDict['OutputFormat'] == 1: # Excel output format
                        iSSCol = 1
                        if boolNewlyNamedWorksheet: # insert the column headings
                            lColHeads = [Nm for Nm in rec.keys()]
                            for colHd in lColHeads:
                                shXL.Cells(iSSRow,iSSCol).Value = colHd
                                iSSCol += 1
                            iSSRow += 1
                            iSSCol = 1
                            boolNewlyNamedWorksheet = False
                            boolNewBlankSheet = False
                            if self.calcDict['CreateSummaries'] == 1:
                                iFirstRowInBlock = iSSRow
                        # process each record
                        for colHd in lColHeads:
                            shXL.Cells(iSSRow,iSSCol).Value = rec[colHd]
                            iSSCol += 1
                        if self.calcDict['UseRef'] == 1:
                            shXL.Cells(iSSRow,6).FormulaR1C1 = xlIRFn
                            shXL.Cells(iSSRow,7).FormulaR1C1 = xlVisFn
                        shXL.Cells(iSSRow,8).FormulaR1C1 = xlIRFn
                        shXL.Cells(iSSRow,9).FormulaR1C1 = xlVisFn
                        shXL.Cells(iSSRow,10).FormulaR1C1 = xlNDVIFn
                        if self.calcDict['OutputSAS'] == 1:
                            shXL_SAS.Cells(iSASRow,1).Value = dDt
                            shXL_SAS.Cells(iSASRow,2).Value = dDt.strftime('%j')
                            wx.Yield()
                            # use Excel copy/paste to assure we get the correct values
                            shXL.Cells(iSSRow,10).Copy()
                            shXL_SAS.Cells(iSASRow,3).PasteSpecial(Paste=-4163)
                            iSASRow += 1
                        iSSRow += 1

                    if self.calcDict['OutputFormat'] in (2, 3):
                        if isNewTextFile == 1: # write the column headings
                            lColHeads = [Nm for Nm in rec.keys()]
                            wr.writerow(lColHeads)
                            isNewTextFile = 0
                            if self.calcDict['OutputSAS'] == 1:
                                isNewSummaryFile = 1 # flag for later
                                isNewSASFile = 1
                        lRow = [rec[colHd] for colHd in lColHeads]
                        wr.writerow(lRow)

                if self.calcDict['CreateSummaries'] == 1:
                    if self.calcDict['OutputFormat'] == 1: # Excel output format
                        if iSSRow >= iFirstRowInBlock:
                            iLastRowInBlock = iSSRow
                            shXLSummary.Cells(iSSummaryRow,1).Value = dDt
                            params = (shXL.Name, iFirstRowInBlock, iLastRowInBlock)
                            shXLSummary.Cells(iSSummaryRow,2).Formula = "=AVERAGE('%s'!J%i:J%i)" % params
                            shXLSummary.Cells(iSSummaryRow,3).Formula = "=STDEV.S('%s'!J%i:J%i)" % params
                            shXLSummary.Cells(iSSummaryRow,4).Formula = "=COUNT('%s'!J%i:J%i)" % params
                            shXLSummary.Cells(iSSummaryRow,5).Formula = '=IF(D%i<=1,"N0","YES")' % (iSSummaryRow,)
                            shXLSummary.Cells(iSSummaryRow,6).Formula = '=IF(D{n}<=1,"",B{n})'.format(n=iSSummaryRow)
                            shXLSummary.Cells(iSSummaryRow,7).Formula = '=IF(D{n}<=1,"",C{n}/SQRT(D{n}%))'.format(n=iSSummaryRow)
                            iSSummaryRow += 1
                            iFirstRowInBlock = iLastRowInBlock + 1
                        
                    if self.calcDict['OutputFormat'] in (2, 3):
                        stSQL = """SELECT '{dT}' AS "Date",
                        AVG(ndvi) AS "Avg",
                        StDev(ndvi) AS "StDev",
                        COUNT(ndvi) AS "Count"
                        FROM tmpSpectralData
                        GROUP BY "Date";""".format(dT=dDt)
                        recs = scidb.curD.execute(stSQL).fetchall()
                        for rec in recs:
                            if isNewSummaryFile == 1: # write the column headings
                                lColHeadsSummary = [Nm for Nm in rec.keys()]
                                # add conditional & calculated columns
                                lColHeadsSummary.extend(['Use?', 'NDVI', 'SEM'])
                                wrSummary.writerow(lColHeadsSummary)
                                isNewSummaryFile = 0
                            lRow = []
                            for colHd in lColHeadsSummary:
                                try: # append the recordset items normally
                                    lRow.append(rec[colHd])
                                except:
                                    pass
                            # add on the extra items
                            if rec['Count'] <= 1:
                                lRow.append('NO')
                            else:
                                lRow.append('YES')
                                lRow.append(rec['Avg'])
                                stdErrOfTheMean = rec['StDev'] / (math.sqrt(rec['Count']))
                                lRow.append(stdErrOfTheMean)
                            wrSummary.writerow(lRow)

                if self.calcDict['OutputSAS'] == 1:
                    stSQL = """SELECT strftime('%d-%m-%Y',Timestamp)AS "Date",
                    strftime('%j',Timestamp) AS RefDay,
                    ndvi AS VI FROM tmpSpectralData
                    ORDER BY Timestamp;"""
                    recs = scidb.curD.execute(stSQL).fetchall()
                    for rec in recs:
                        if self.calcDict['OutputFormat'] in (2, 3):
                            if isNewSASFile == 1: # write the column headings
                                lColHeadsSAS = [Nm for Nm in rec.keys()]
                                wrSAS.writerow(lColHeadsSAS)
                                isNewSASFile = 0
                            lRow = [rec[colHd] for colHd in lColHeadsSAS]
                            wrSAS.writerow(lRow)
                        
                # done with this date
                wx.Yield() # allow window updates to occur
            # done with dates for this station
            if self.calcDict['OutputFormat'] == 1: # Excel output format
                shXL.Columns.AutoFit()
                if self.calcDict['CreateSummaries'] == 1:
                    boolNewBlankSummarySheet = False # flag to create a new one for the next Station
                    if self.calcDict['Normalize'] == 1:
                        # place these headers
                        shXLSummary.Cells(1,8).Value = 'minNDVI'
                        shXLSummary.Cells(1,9).Formula = '=MIN(F2:F%i)' % (iSSummaryRow-1,)
                        shXLSummary.Cells(1,10).Value = 'maxNDVI'
                        shXLSummary.Cells(1,11).Formula = '=MAX(F2:F%i)' % (iSSummaryRow-1,)
                        shXLSummary.Cells(1,12).Value = 'relative NDVI'
                        for nR in range(2, iSSummaryRow): # enter the normalization formulas
                            shXLSummary.Cells(nR,12).Formula = '=if(D{n}<=1,"",(F{n}-I1)/(K1-I1))'.format(n=nR)
                    shXLSummary.Columns.AutoFit()
                    wx.Yield()
                    # if iSSummaryRow > 1: insert chart
                if self.calcDict['OutputSAS'] == 1:
                    boolNewBlankSASSheet = False # flag to create a new one for the next Station
                    if self.calcDict['Normalize'] == 1 and iSASRow > 3:
                        # adjust SAS values to relative NDVI
                        if self.calcDict['CreateSummaries'] == 1:
                            # normalize based on averages in Summary
                            time.sleep(1) # allow time for Excel to calculate values
                            fMinNDVI = shXLSummary.Cells(1,9).Value
                            fMaxNDVI = shXLSummary.Cells(1,11).Value
                        else: # normalize SAS values directly
                            lVI = []
                            for iV in range (2, iSASRow-1):
                                lVI.append(float(shXL_SAS.Cells(iV,3).Value))
                            fMinNDVI = min(lVI)
                            fMaxNDVI = max(lVI)
                        fRangeNDVI = fMaxNDVI - fMinNDVI
                        # if range is 0 then Max=Min, or all zero, or some other error; adjustment has no meaning
                        #  formula would give divide-by-zero error anyway
                        if fRangeNDVI != 0:
                            for iV in range (2, iSASRow-1):
                                fV = shXL_SAS.Cells(iV,3).Value
                                fV = (fV - fMinNDVI) / fRangeNDVI
                                shXL_SAS.Cells(iV,3).Value = fV
                    shXL_SAS.Columns.AutoFit()
                    bXL_SAS.Save()
                    
                bXL.Save()
            if self.calcDict['OutputFormat'] in (2, 3): # one of the text output formats
                fOut.close()
                if self.calcDict['CreateSummaries'] == 1:
                    fOutSummary.close()
                if self.calcDict['OutputSAS'] == 1:
                    fOutSAS.close()
                if self.calcDict['Normalize'] == 1: # re-open files to add/edit
                    if self.calcDict['CreateSummaries'] == 1:
                        lSummary = [] # list-of-lists to edit and write back
                        lNDVI = [] # list of the NDVI values, to extract min/max
                        with open(stFilePathSummary, 'rb') as fInSummary:
                            rrSummary = csv.reader(fInSummary, delimiter=cDl, quotechar='"')
                            for lRow in rrSummary:
                                if len(lSummary) == 0: # the header row
                                    lRow.extend(['minNDVI','','maxNDVI','','relative NDVI'])
                                else:
                                    try: # if no data for this date, there is no item 5
                                        lNDVI.append(float(lRow[5]))
                                    except:
                                        pass
                                lSummary.append(lRow)
                        fNDVImin = min(lNDVI)
                        fNDVImax = max(lNDVI)
                        fNDVIRange = fNDVImax - fNDVImin
                        if fNDVIRange != 0:
                            with open(stFilePathSummary, 'wb') as fOutSummary:
                                wrSummary = csv.writer(fOutSummary, delimiter=cDl, quotechar='"', quoting=csv.QUOTE_MINIMAL)
                                for lRow in lSummary:
                                    if lRow[0] == 'Date': # the header row
                                        lRow[8] = fNDVImin
                                        lRow[10] = fNDVImax
                                    else:
                                        try: # if no data for this date, there is no item 5
                                            fNDVIrel = (float(lRow[5])-fNDVImin)/fNDVIRange
                                            lRow.extend(['','','','',fNDVIrel])
                                        except:
                                            pass
                                    wrSummary.writerow(lRow)
                # still normalizing
                if self.calcDict['OutputSAS'] == 1:
                    lSAS = [] # list-of-lists to edit and write back
                    lNDVI = [] # list of the NDVI values, to extract min/max
                    with open(stFilePathSAS, 'rb') as fInSAS:
                        rrSAS = csv.reader(fInSAS, delimiter=cDl, quotechar='"')
                        for lRow in rrSAS:
                            if len(lSAS) > 0: # beyond the header row
                                if self.calcDict['CreateSummaries'] != 1:
                                    # if no summary, collect these values
                                    lNDVI.append(float(lRow[2]))
                            lSAS.append(lRow)
                    if self.calcDict['CreateSummaries'] != 1:
                        # if summary, use the values we already had, otherwise calculate from SAS
                        fNDVImin = min(lNDVI)
                        fNDVImax = max(lNDVI)
                        fNDVIRange = fNDVImax - fNDVImin
                    if fNDVIRange != 0:
                        with open(stFilePathSAS, 'wb') as fOutSAS:
                            wrSAS = csv.writer(fOutSAS, delimiter=cDl, quotechar='"', quoting=csv.QUOTE_MINIMAL)
                            for lRow in lSAS:
                                if lRow[0] == 'Date': # the header row
                                    pass
                                else: # adjust the value
                                    fNDVIrel = (float(lRow[2])-fNDVImin)/fNDVIRange
                                    lRow[2] = fNDVIrel
                                wrSAS.writerow(lRow)

        # insert metadata: 'Metadata for this job', starting timestamp, elapsed time, source DB
        # calcDict, including drilldown into logger and sensor information
        # see InsertMetadataIntoCurrentSheet fn in Access DB
        wx.Yield() # allow window updates to occur
        self.tcProgress.SetValue('Creating metadata for this job')
        self.tcProgress.AppendText(', elapsed time: ' +
                scidb.timeIntervalAsStandardString(dtJobStarted,
                datetime.datetime.now()))
        wx.Yield()
        # create metadata as a list-of-lists, so can be output either as a file or an Excel worksheet
        lMetaData = []
        lMetaData.append(['job started', dtJobStarted])
        insertFinishTimeAt = len(lMetaData) # index in lMetaData to insert final time data, after everything else is done
        sDBPath = '(not known)'
        recs = scidb.curD.execute("PRAGMA database_list").fetchall()
        for rec in recs:
            if rec['name'] == 'main':
                sDBPath = rec['file']
        lMetaData.append(['source database file', sDBPath])
        lMetaData.append(['name of this panel', self.calcDict['CalcName']])
        minDay = min(lDates)
        maxDay = max(lDates)
        stSQLSta = """SELECT Stations.StationName, Stations.LongitudeDecDegrees AS StaLon,
                FieldSites.SiteName, FieldSites.LongitudeDecDegrees AS SiteLon,
                DataChannels.LoggerID, Loggers.LoggerSerialNumber,
                InstrumentSpecs.InstrumentSpec
                FROM ((((Stations LEFT JOIN FieldSites ON Stations.SiteID = FieldSites.ID)
                LEFT JOIN ChannelSegments ON Stations.ID = ChannelSegments.StationID)
                LEFT JOIN DataChannels ON ChannelSegments.ChannelID = DataChannels.ID)
                LEFT JOIN Loggers ON DataChannels.LoggerID = Loggers.ID)
                LEFT JOIN InstrumentSpecs ON Loggers.InstrumentSpecID = InstrumentSpecs.ID
                WHERE Stations.ID = ?
                AND ((ChannelSegments.SegmentBegin <= ?) 
                OR (COALESCE(ChannelSegments.SegmentEnd, datetime("now")) >= ?))
                GROUP BY Stations.StationName,  Stations.LongitudeDecDegrees,
                FieldSites.SiteName, FieldSites.LongitudeDecDegrees,
                DataChannels.LoggerID, Loggers.LoggerSerialNumber,
                InstrumentSpecs.InstrumentSpec;"""
#        stSQLSta = 'SELECT StationName as TNm FROM Stations WHERE ID = ?'
        stSQLSerRef = """SELECT DataSeries.DataSeriesDescription, DataChannels.SensorID,
                Sensors.SensorSerialNumber, DeviceSpecs.DeviceSpec,
                DataTypes.TypeText, DataUnits.UnitsText,
                ChannelSegments.SegmentBegin, ChannelSegments.SegmentEnd
                FROM ((((((DataSeries LEFT JOIN ChannelSegments ON DataSeries.ID = ChannelSegments.SeriesID)
                LEFT JOIN DataChannels ON ChannelSegments.ChannelID = DataChannels.ID)
                LEFT JOIN Sensors ON DataChannels.SensorID = Sensors.ID)
                LEFT JOIN DeviceSpecs ON Sensors.DeviceSpecID = DeviceSpecs.ID)
                LEFT JOIN DataTypes ON DataChannels.DataTypeID = DataTypes.ID)
                LEFT JOIN DataUnits ON DataChannels.DataUnitsID = DataUnits.ID)
                WHERE DataSeries.ID = ? AND ChannelSegments.StationID = ?
                AND ((ChannelSegments.SegmentBegin <= ?) 
                OR (COALESCE(ChannelSegments.SegmentEnd, datetime("now")) >= ?));"""
        stSQLSerDat = 'SELECT DataSeriesDescription as RNm FROM DataSeries WHERE ID = ?'
        if self.calcDict['UseRef'] != 1:
            lMetaData.append(['Use a reference station?', 'No'])
        else:
            lMetaData.append(['Use a reference station?', 'Yes'])
            lMetaData.append(['Reference station record ID', self.calcDict['RefStationID']])
            params = (self.calcDict['RefStationID'], minDay, maxDay )
            recs = scidb.curD.execute(stSQLSta, params).fetchall()
            iRecs = len(recs) # maybe give time ranges if more than one
            for rec in recs: # usually just one
                lMetaData.append(['Reference station name', rec['StationName']])
                if rec['StaLon'] == None:
                    lMetaData.append(['Longitude', rec['SiteLon'], 'referenced from Site', rec['SiteName']])
                else:
                    lMetaData.append(['Reference station longitude', rec['StaLon']])
                lMetaData.append(['Reference logger record ID', rec['LoggerID']])
                if rec['LoggerSerialNumber'] != None: 
                    lMetaData.append(['Reference logger serial number', rec['LoggerSerialNumber']])
                lRow = ['Reference instrument specification']
                if rec['InstrumentSpec'] != None:
                    lRow.append(rec['InstrumentSpec'])
                else:
                    lRow.append('(none given)')
                lMetaData.append(lRow)
            lMetaData.append(['Reference IR series record ID', self.calcDict['IRRefSeriesID']])
            params = (self.calcDict['IRRefSeriesID'], self.calcDict['RefStationID'], minDay, maxDay)
            recs = scidb.curD.execute(stSQLSerRef, params).fetchall()
            iNumRecs = len(recs) # give time ranges if more than one
            for rec in recs: # usually just one
                lMetaData.append(['Reference IR series name', rec['DataSeriesDescription']])
                lMetaData.append(['Reference IR series device record ID', rec['SensorID']])
                if rec['SensorSerialNumber'] != None:
                    lMetaData.append(['Reference IR device serial number', rec['SensorSerialNumber']])
                lRow = ['Reference IR device specification']
                if rec['DeviceSpec'] != None:
                    lRow.append(rec['DeviceSpec'])
                else:
                    lRow.append('(none given)')
                lMetaData.append(lRow)
                lRow = ['Reference IR device data type']
                if rec['TypeText'] != None:
                    lRow.append(rec['TypeText'])
                else:
                    lRow.append('(none given)')
                lMetaData.append(lRow)
                lRow = ['Reference IR device data units']
                if rec['UnitsText'] != None:
                    lRow.append(rec['UnitsText'])
                else:
                    lRow.append('(none given)')
                lMetaData.append(lRow)

            lMetaData.append(['Reference Vis series record ID', self.calcDict['VISRefSeriesID']])
            params = (self.calcDict['VISRefSeriesID'], self.calcDict['RefStationID'], minDay, maxDay)
            recs = scidb.curD.execute(stSQLSerRef, params).fetchall()
            iNumRecs = len(recs) # give time ranges if more than one
            for rec in recs: # usually just one
                lMetaData.append(['Reference Vis series name', rec['DataSeriesDescription']])
                lMetaData.append(['Reference Vis series device record ID', rec['SensorID']])
                if rec['SensorSerialNumber'] != None:
                    lMetaData.append(['Reference Vis device serial number', rec['SensorSerialNumber']])
                lRow = ['Reference Vis device specification']
                if rec['DeviceSpec'] != None:
                    lRow.append(rec['DeviceSpec'])
                else:
                    lRow.append('(none given)')
                lMetaData.append(lRow)
                lRow = ['Reference Vis device data type']
                if rec['TypeText'] != None:
                    lRow.append(rec['TypeText'])
                else:
                    lRow.append('(none given)')
                lMetaData.append(lRow)
                lRow = ['Reference Vis device data units']
                if rec['UnitsText'] != None:
                    lRow.append(rec['UnitsText'])
                else:
                    lRow.append('(none given)')
                lMetaData.append(lRow)
        lMetaData.append(['For Data Stations:'])
        lMetaData.append(['IR series record ID', self.calcDict['IRDataSeriesID']])
        lMetaData.append(['IR series name',
                scidb.curD.execute(stSQLSerDat, (self.calcDict['IRDataSeriesID'],)).fetchone()['RNm']])
        lMetaData.append(['Vis series record ID', self.calcDict['VisDataSeriesID']])
        lMetaData.append(['Vis series name',
                scidb.curD.execute(stSQLSerDat, (self.calcDict['VisDataSeriesID'],)).fetchone()['RNm']])
        lMetaData.append(['Formula for getting IR for NDVI based on raw IR (i) and Vis (v):'])
        lMetaData.append(['', self.calcDict['IRFunction']])
        lMetaData.append(['Formula for getting Vis for NDVI based on raw IR (i) and Vis (v):'])
        lMetaData.append(['', self.calcDict['VISFunction']])
        lMetaData.append(['Hours before/after solar noon, to include data for',
                self.calcDict['PlusMinusCutoffHours']])
        lMetaData.append(['Date of clear day, to use for high/low cutoffs',
                self.calcDict['ClearDay']])
        lMetaData.append(['Ignore data < this percent of clear day maximum',
                self.calcDict['ThresholdPctLow']])
        lMetaData.append(['Ignore data > this percent of clear day maximum',
                self.calcDict['ThresholdPctHigh']])
        if self.calcDict['UseOnlyValidNDVI'] == 0:
            lMetaData.append(['Eliminate NDVI beyond thresholds', 'No, use all'])
        else:
            lMetaData.append(['Use only NDVI between:'])
            lMetaData.append(['Minimum', self.calcDict['NDVIvalidMin']])
            lMetaData.append(['Maximum', self.calcDict['NDVIvalidMax']])
        lRow = ['Create NDVI summaries by date']
        if self.calcDict['CreateSummaries'] == 1:
            lRow.append('Yes')
        else:
            lRow.append('No')
        lMetaData.append(lRow)
        lRow = ['Create tabulated output for SAS']
        if self.calcDict['OutputSAS'] == 1:
            lRow.append('Yes')
        else:
            lRow.append('No')
        lMetaData.append(lRow)
        lRow = ['Create NDVI normalized into range 0-to-1']
        if self.calcDict['Normalize'] == 1:
            lRow.append('Yes')
        else:
            lRow.append('No')
        lMetaData.append(lRow)

        lRow = ['Output format']
        if self.calcDict['OutputFormat'] == 1:
            lRow.append('Excel spreadsheets')
        if self.calcDict['OutputFormat'] == 2:
            lRow.append('Tab-delimited text')
        if self.calcDict['OutputFormat'] == 3:
            lRow.append('Comma-seperated values')
        lMetaData.append(lRow)

        lRow = ['Folder to save output into']
        if self.calcDict['OutputFolder'] != None:
            lRow.append(self.calcDict['OutputFolder'])
        else:
            lRow.append('(none given, use default)')
        lMetaData.append(lRow)

        lRow = ['Base name (filenames if Excel, folder if otherwise)']
        if self.calcDict['OutputBaseName'] != None:
            lRow.append(self.calcDict['OutputBaseName'])
        else:
            lRow.append('(none given, use default)')
        lMetaData.append(lRow)


        lMetaData.append(['Data for Stations:', 'ID', 'Name', 'LoggerID',
                'Serial Num', 'Instrument type'])
        for iStID in lStaIDs:
            params = (iStID, minDay, maxDay)
            recs = scidb.curD.execute(stSQLSta, params).fetchall()
            iNumRecs = len(recs) # maybe give time ranges if there are more than one
            for rec in recs: # usually just one
                lRow = []
                lRow.append('')
                lRow.append(iStID)
                lRow.append(rec['StationName'])
                lRow.append(rec['LoggerID'])
                if rec['LoggerSerialNumber'] == None:
                    lRow.append('(none)')
                else:
                    lRow.append(rec['LoggerSerialNumber'])
                if rec['InstrumentSpec'] == None:
                    lRow.append('(not given)')
                else:
                    lRow.append(rec['InstrumentSpec'])
                lMetaData.append(lRow)
        lMetaData.append(['Data for Dates:'])
        for dDt in lDates:
            lMetaData.append(['', dDt]) # make correct format
        # put these in last, to be as accurate as possible on the times
        lMetaData.insert(insertFinishTimeAt, ['total elapsed time', scidb.timeIntervalAsStandardString(dtJobStarted,
                        datetime.datetime.now())])
        # insert at same position, bumps up the previous one
        lMetaData.insert(insertFinishTimeAt, ['job completed', datetime.datetime.now()])

        if self.calcDict['OutputFormat'] == 1: # Excel output format
            shXLMetadata = bXL.Sheets.Add() # creates new sheet 1st in the book
            shXLMetadata.Name = 'Metadata'
            iSSRow = 0
            for lRow in lMetaData:
                iSSRow += 1
                iSSCol = 0
                for item in lRow:
                    iSSCol += 1
                    shXLMetadata.Cells(iSSRow,iSSCol).Value = item
            shXLMetadata.Columns.AutoFit()
            bXL.Save()

        if self.calcDict['OutputFormat'] in (2, 3): # one of the text formats
            if self.calcDict['OutputFormat'] == 2:
                stFilePath = os.path.join(stSavePath, 'metadata') + '.txt'
            if self.calcDict['OutputFormat'] == 3:
                stFilePath = os.path.join(stSavePath, 'metadata') + '.csv'
            try: # before we go any further
                # make sure there's nothing invalid about the filename
                fOutMetadata = open(stFilePath, 'wb') 
            except:
                wx.MessageBox(' Can not create file:\n\n' + stFilePath, 'Info',
                    wx.OK | wx.ICON_INFORMATION)
                return
            wr = csv.writer(fOutMetadata, delimiter=cDl, quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for lRow in lMetaData:
                wr.writerow(lRow)
            fOutMetadata.close()

        self.tcProgress.AppendText('\n Job completed')
        print "Job Done"

class NDVIFrame(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title)
        self.InitUI()
        self.SetSize((1050, 600))
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
        self.stDateToPreview = ''
        self.cbxRefStationID = framePanel.cbxRefStationID
        self.cbxIRRefSeriesID = framePanel.cbxIRRefSeriesID

    def onMouseMotion( self, event ):
        if boolMakingDataset:
            return
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
        longitude = scidb.GetStationLongitude(staID)
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
