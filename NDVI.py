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
        pvLabel = wx.StaticText(pnl, -1, "previews will be here")
        pvSiz.Add(pvLabel, pos=(gRow, 0), span=(1, 1), flag=wx.TOP|wx.LEFT|wx.BOTTOM|wx.EXPAND, border=5)
        
        gRow += 1
        # Add the FloatCanvas canvas
        NC = NavCanvas.NavCanvas(pnl,
             Debug = 0,
             BackgroundColor = "WHITE")
        self.Canvas = NC.Canvas # reference the contained FloatCanvas
        # test of drawing one line
#        self.UnBindAllMouseEvents()
#        self.Canvas.InitAll()
#        self.Canvas.Draw()
        points = [(-100,-100),(100,100), (100,-100), (-100,100)]
        self.Canvas.AddLine(points, LineWidth = 1, LineColor = 'BLUE')
        self.Canvas.ZoomToBB() # this makes the drawing about 10% of the whole canvas, but
        # then the "Zoom To Fit" button correctly expands it to the whole space

        pvSiz.Add(NC, pos=(gRow, 0), span=(1, 1), flag=wx.EXPAND, border=0)
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
#        self.Bind( wx.EVT_MOTION, self.OnMouseMotion )
#        framePanel.Bind( wx.EVT_MOTION, self.OnMouseMotion )
        self.DtList = framePanel.datesList
        self.DtList.Bind(wx.EVT_ENTER_WINDOW, self.onMouseOver)
        self.DtList.Bind(wx.EVT_LEAVE_WINDOW, self.onMouseLeave)
        self.DtList.Bind( wx.EVT_MOTION, self.onMouseMotion )
        self.CreateStatusBar()
        self.SetStatusText("Hello, world!")

    def onMouseOver(self, event):
        self.SetStatusText("Entered List")
#        # mouseover changes colour of button
#        self.butn1.SetBackgroundColour('Green')
        event.Skip()
        
    def onMouseLeave(self, event):
        self.SetStatusText("Exited List")
#        # mouse not over button, back to original colour
#        self.butn1.SetBackgroundColour(self.colour)
        event.Skip()

        
    def onMouseMotion( self, event ):
        frameClientPos = event.GetPosition()
        desktopPos = self.ClientToScreen( frameClientPos )  # Current cursor desktop coord
#        print '----  MyFrame::OnMouseMotion()     mouse is at: ', desktopPos
        print '----  onMouseMotion() mouse is at: ', frameClientPos

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
