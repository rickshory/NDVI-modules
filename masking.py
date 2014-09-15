import wx, sqlite3, datetime, copy, csv
import os, sys, re, cPickle
import scidb
import wx.lib.scrolledpanel as scrolled, wx.grid
import multiprocessing
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin
from wx.lib.wordwrap import wordwrap
import wx.combo, wx.calendar

try:
    from floatcanvas import NavCanvas, FloatCanvas, Resources
except ImportError: # if it's not there locally, try the wxPython lib.
    from wx.lib.floatcanvas import NavCanvas, FloatCanvas, Resources
import wx.lib.colourdb

try:
    import numpy as N
except ImportError:
    raise ImportError("I could not import numpy")

ID_MASKING_SETUP_PANEL = wx.NewId()
ID_MASKING_PREVIEW_PANEL = wx.NewId()
ID_CHAN_TEXT = wx.NewId()
ID_CHAN_LIST = wx.NewId()
ID_START_TIME = wx.NewId()
ID_END_TIME = wx.NewId()

CkMaskingPreviewEventType = wx.NewEventType()
EVT_CK_MASKING_PREVIEW = wx.PyEventBinder(CkMaskingPreviewEventType, 1)

sFmt = '%Y-%m-%d %H:%M:%S'
# global floats for scaling canvas x/y data
gXRange = 1.0 # defaults
gYRange = 1.0

def ScaleCanvas(center):
    """
    function that returns a scaling vector to scale y and x relative to each other
    """
    # center gets ignored in this case
    # returns a vector that multiplies X and Y
#    return [200,1] # rule of thumb
#    s = gYRange, gXRange
#    return s # try this
    return N.array( (gYRange, gXRange), N.float)


class CkMaskingPreviewEvent(wx.PyCommandEvent):
    def __init__(self, evtType, id):
        wx.PyCommandEvent.__init__(self, evtType, id)
        self.ck = None

    def SetMyCk(self, ck):
        self.ck = ck

    def GetMyCk(self):
        return self.ck


class MyApp(wx.App):
    def OnInit(self):
        self.dsFrame = maskingFrame(None, wx.ID_ANY, 'Data Masking')
        self.SetTopWindow(self.dsFrame)
        self.dsFrame.Show()
        self.Bind(EVT_CK_MASKING_PREVIEW, self.CkMaskingPreview)
        self.dsFrame.statusBar.SetStatusText('Select Data Channel, and Start and End timestamps')
        return True

    def CkMaskingPreview(self, event):
        # This is the general purpose function that tests whether
        # ChannelID, Start and End times are valid, and if so initates a preview.
        # It is called by any change to the channel selector, or
        # KillFocus of any of the timestamp fields
        event_id = event.GetId()
        ck = event.GetMyCk() # retrieve parameters list
        print "in CkMaskingPreview; event Check:", ck # may not use this
        self.dsFrame.statusBar.SetStatusText('in CkMaskingPreview event handler')
        event_id=ck[2]
        if event_id == ID_START_TIME:
            print "ID_START_TIME Event reached CkMaskingPreview"

        if event_id == ID_END_TIME:
            print "ID_END_TIME Event reached CkMaskingPreview"

        if event_id == ID_CHAN_LIST: # does not hit here
            print "ID_CHAN_LIST Event reached CkMaskingPreview"

        tpFrame = self.GetTopWindow()
        # validate timestamps
        txStartTime = tpFrame.FindWindowById(ID_START_TIME)
        stDTStart = txStartTime.GetValue()
        if stDTStart.strip() == '':
            boolStartIsValid = True # empty is valid, meaning 'everything before'
            stDTStart = '' # distinguish from explict date
            txStartTime.SetValue(stDTStart)
        else:
            dtStart = wx.DateTime() # Uninitialized datetime
            boolStartIsValid = dtStart.ParseDateTime(stDTStart)
#            print "boolStartIsValid", boolStartIsValid
            if boolStartIsValid != -1:
                # remember the timestamp and write it back to the control in standard format
                stDTStart = dtStart.Format(sFmt)
                txStartTime.SetValue(stDTStart)

        txEndTime = tpFrame.FindWindowById(ID_END_TIME)
        stDTEnd = txEndTime.GetValue()
        if stDTEnd.strip() == '':
            boolEndIsValid = True # empty is valid, meaning 'everything after
            stDTEnd = '' # distinguish from explict date
            txEndTime.SetValue(stDTEnd)
        else:
            dtEnd = wx.DateTime() # Uninitialized datetime
            boolEndIsValid = dtEnd.ParseDateTime(stDTEnd)
            if boolEndIsValid != -1:
                # remember the timestamp and write it back to the control in standard format
                stDTEnd = dtEnd.Format(sFmt)
                txEndTime.SetValue(stDTEnd)

        # get ChannelID, if selected
        txChanText = tpFrame.FindWindowById(ID_CHAN_TEXT)
        msPnl = tpFrame.FindWindowById(ID_MASKING_SETUP_PANEL)
        pUp = msPnl.chanPopup # popup is an attibute of the panel, though the panel is not its parent
        ls = pUp.GetControl() # direct handle to the popup's control, which is the listCtrl
        # to retrieve the hidden key number stored in the popup list row (e.g. a DB record ID):
        curItem = pUp.curitem
        if curItem == -1:
            ChanID = 0 # something to flag invalid
        else:
            ChanID = ls.GetItemData(curItem)
        if ChanID == 0:
            self.dsFrame.statusBar.SetStatusText('Select a Data Channel for a masking preview')
            return
        else:
            self.dsFrame.statusBar.SetStatusText('Data Channel ' + str(ChanID) + ' selected')
            # the selection may happen without filling the textbox; explicitly fill textbox
            stItem = ls.GetItemText(curItem)
            txChanText.SetValue(stItem)
#            print "Current list item", ls.GetItemText(curItem)
        if boolStartIsValid == -1:
            self.dsFrame.statusBar.SetStatusText('Start time is not valid')
            return
        if boolEndIsValid == -1:
            self.dsFrame.statusBar.SetStatusText('End time is not valid')
            return
        self.dsFrame.statusBar.SetStatusText('Creating preview for ' + stItem)
        pvPnl = tpFrame.FindWindowById(ID_MASKING_PREVIEW_PANEL)
        # start is valid or we would not be to this point
        if stDTStart == '': # this distinguishes blank meaning "all before"
            # get the earliest timestamp for this channel
            stSQLmin = """SELECT MIN(UTTimestamp) AS DataFirst FROM Data 
                WHERE Data.ChannelID = {iCh};
                """.format(iCh=ChanID)
            stUseStart = scidb.curD.execute(stSQLmin).fetchone()['DataFirst']
        else:
            stUseStart = stDTStart
        print "stUseStart", stUseStart

        # end is valid or we would not be to this point
        if stDTEnd == '': # this distinguishes blank meaning "all after"
            # get the latest timestamp for this channel
            stSQLmax = """SELECT MAX(UTTimestamp) AS DataLast FROM Data 
                WHERE Data.ChannelID = {iCh};
                """.format(iCh=ChanID)
            stUseEnd = scidb.curD.execute(stSQLmax).fetchone()['DataLast']
        else:
            stUseEnd = stDTEnd
        print "stUseEnd", stUseEnd
        stSQLMinMax = """SELECT MIN(CAST(Data.Value AS FLOAT)) AS MinData,
            MAX(CAST(Data.Value AS FLOAT)) AS MaxData
            FROM Data
            WHERE Data.ChannelID = {iCh}
            AND Data.UTTimestamp >= '{sDs}'
            AND Data.UTTimestamp <= '{sDe}';
            """.format(iCh=ChanID, sDs=stUseStart, sDe=stUseEnd)
        MnMxRec = scidb.curD.execute(stSQLMinMax).fetchone()
        fDataMin = MnMxRec['MinData']
        fDataMax = MnMxRec['MaxData']
        print "Min", fDataMin, "Max", fDataMax
        totSecs = (datetime.datetime.strptime(stUseEnd, sFmt)-datetime.datetime.strptime(stUseStart, sFmt)).total_seconds()
        print 'totSecs', totSecs
        if fDataMax == fDataMin:
            scaleY = 0
        else:
            scaleY = (totSecs * 0.618) / (fDataMax - fDataMin)

        stSQLUsed = """SELECT DATETIME(Data.UTTimestamp) AS UTTime, 
            strftime('%s', Data.UTTimestamp) - strftime('%s', '{sDs}') AS Secs,
            Data.Value * {fSy} AS Val
            FROM Data
            WHERE Data.ChannelID = {iCh} 
            AND Data.UTTimestamp >= '{sDs}'
            AND Data.UTTimestamp <= '{sDe}'
            AND Data.Use = 1
            ORDER BY UTTime;
            """.format(iCh=ChanID, sDs=stUseStart, sDe=stUseEnd, fSy=scaleY)
        ptRecs = scidb.curD.execute(stSQLUsed).fetchall()
#        if len(ptRecs) == 0:
##            self.pvLabel.SetLabel('No data for for ' + self.stDateToPreview)
#            return
        ptsUsed = []
        for ptRec in ptRecs:
#                print ptRec['Secs'], ptRec['Value']
            ptsUsed.append((ptRec['Secs'], ptRec['Val']))
        iLU = len(ptsUsed)
        stSQLMasked = """SELECT DATETIME(Data.UTTimestamp) AS UTTime, 
            strftime('%s', Data.UTTimestamp) - strftime('%s', '{sDs}') AS Secs,
            Data.Value * {fSy} AS Val
            FROM Data
            WHERE Data.ChannelID = {iCh} 
            AND Data.UTTimestamp >= '{sDs}'
            AND Data.UTTimestamp <= '{sDe}'
            AND Data.Use = 0
            ORDER BY UTTime;
            """.format(iCh=ChanID, sDs=stUseStart, sDe=stUseEnd, fSy=scaleY)
        ptRecs = scidb.curD.execute(stSQLMasked).fetchall()
#        if len(ptRecs) == 0:
##            self.pvLabel.SetLabel('No data for for ' + self.stDateToPreview)
#            return
        ptsMasked = []
        for ptRec in ptRecs:
#                print ptRec['Secs'], ptRec['Value']
            ptsMasked.append((ptRec['Secs'], ptRec['Val']))
        iLM = len(ptsMasked)
        print "Points used:", len(ptsUsed)
        print "Points masked:", len(ptsMasked)
        if iLU + iLM == 0:
#            self.pvLabel.SetLabel('No data for for ' + self.stDateToPreview)
            return
            
#        self.UnBindAllMouseEvents()
        pvPnl.Canvas.InitAll()
        pvPnl.Canvas.Draw()
#        pvPnl.Canvas.SetProjectionFun(ScaleCanvas)
#        pvPnl.Canvas.AddLine(pts, LineWidth = 1, LineColor = 'BLUE')
        if iLU > 0:
            pvPnl.Canvas.AddPointSet(ptsUsed, Color = 'BLUE', Diameter = 1)
        if iLM > 0:
            pvPnl.Canvas.AddPointSet(ptsMasked, Color = 'RED', Diameter = 1)
        pvPnl.Canvas.ZoomToBB() # this makes the drawing about 10% of the whole canvas, but
        # then the "Zoom To Fit" button correctly expands it to the whole space

#----------------------------------------------------------------------
# This class is used to provide an interface between a ComboCtrl and the
# ListCtrl that is used as the popoup for the combo widget.

class ListCtrlComboPopup(wx.ListCtrl, wx.combo.ComboPopup):

    def __init__(self):
        
        # Since we are using multiple inheritance, and don't know yet
        # which window is to be the parent, we'll do 2-phase create of
        # the ListCtrl instead, and call its Create method later in
        # our Create method.  (See Create below.)
        self.PostCreate(wx.PreListCtrl())

        # Also init the ComboPopup base class.
        wx.combo.ComboPopup.__init__(self)
#        self.UseAltPopupWindow()
#        wx.ComboPopup.__init__(self)
        self.lc = None

    def AddItem(self, tuple):
        # do some reasonable thing
# generalized from this:
#       if self.lc.GetColumnCount() == 0:           
#            self.lc.InsertColumn(0, 'State')
#            self.lc.InsertColumn(1, 'Capital')
#            self.lc.SetColumnWidth(0, 140)
#            self.lc.SetColumnWidth(1, 153)
            
#        i = self.lc.GetItemCount()
#        self.lc.InsertStringItem(i, tuple[1])
#        self.lc.SetStringItem(i, 1, tuple[2])
#        self.lc.SetItemData(i, tuple[0])

        # expects 1st item of tuple to be a numeric key
        if self.lc.GetColumnCount() == 0: # add columns
            for n in range(len(tuple)):
                if n == 0:
                    pass
                else:
                    self.lc.InsertColumn(n-1, 'Col'+str(n))
                    self.lc.SetColumnWidth(n-1, 100) # reasonable default width of 100
        i = self.lc.GetItemCount() # so new item will add at end
        for n in range(len(tuple)):
            if n == 0:
                key = tuple[n] # store for later
            else:
                try:
                    if n == 1: #1st visible column
                        self.lc.InsertStringItem(i, str(tuple[n] or ''))
                    else: # any additional visible columns
                        self.lc.SetStringItem(i, n-1, str(tuple[n] or ''))
                except:
                    pass # most likely, have run out of columns
        # attach the key
        try:
            k = int(key)
        except:
            k = 0 # may be meaningless, but valid
        try:
            self.lc.SetItemData(i, k)
        except:
            return # one tuple of only 1 item may land here

    
    def OnMotion(self, evt):
        item, flags = self.lc.HitTest(evt.GetPosition())
        if item >= 0:
            self.lc.Select(item)
            self.curitem = item

    def OnLeftDown(self, evt):
        self.value = self.curitem
        self.Dismiss()


    # The following methods are those that are overridable from the
    # ComboPopup base class.  Most of them are not required, but all
    # are shown here for demonstration purposes.

    # This is called immediately after construction finishes.  You can
    # use self.GetCombo if needed to get to the ComboCtrl instance.
    def Init(self):
        self.value = -1
        self.curitem = -1

    # Create the popup child control.  Return true for success.
    def Create(self, parent):
        self.lc = wx.ListCtrl(parent, ID_CHAN_LIST, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.SIMPLE_BORDER)
        # list will be filled by other functions
        self.lc.Bind(wx.EVT_MOTION, self.OnMotion)
        self.lc.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        return True

    # Return the widget that is to be used for the popup
    def GetControl(self):
        return self.lc

    # Called just prior to displaying the popup, you can use it to
    # 'select' the current item.
    def SetStringValue(self, val):
        idx = self.lc.FindItem(-1, val)
        if idx != wx.NOT_FOUND:
            self.lc.Select(idx)

#    def SetValueWithEvent(self, val, withEvent=True):
#        idx = self.lc.FindItem(-1, val)
#        if idx != wx.NOT_FOUND:
#            self.lc.Select(idx)

    # Return a string representation of the current item.
    def GetStringValue(self):
        if self.value >= 0:
            return self.lc.GetItemText(self.value)
        return ""

    # Called immediately after the popup is shown
    def OnPopup(self):
        wx.combo.ComboPopup.OnPopup(self)

    # Called when popup is dismissed
    def OnDismiss(self):
        # Reach up to the App in order to post the
        # EVT_TEXT event because the popup (self) does not have a
        # parent so events will not propagate up from it.
        app = wx.GetApp()
        topFrame = app.GetTopWindow()
        txbChanText = topFrame.FindWindowById(ID_CHAN_TEXT)
#        print "txbChanText", txbChanText.GetValue()
        evt = wx.PyCommandEvent(wx.EVT_TEXT.typeId, ID_CHAN_TEXT) 
        evt.SetEventObject(txbChanText)
        wx.PostEvent(txbChanText, evt)

        # Create the custom Check Masking Preview event
        CPevt = CkMaskingPreviewEvent(CkMaskingPreviewEventType, -1)
        # set a parameter
        CPevt.SetMyCk(['Channel', 'OnDismiss', ID_CHAN_TEXT])
        # Post the event
        self.GetEventHandler().ProcessEvent(CPevt)

        wx.combo.ComboPopup.OnDismiss(self)

    # This is called to custom paint in the combo control itself
    # (ie. not the popup).  Default implementation draws value as
    # string.
    def PaintComboControl(self, dc, rect):
        wx.combo.ComboPopup.PaintComboControl(self, dc, rect)

    # Receives key events from the parent ComboCtrl.  Events not
    # handled should be skipped, as usual.
    def OnComboKeyEvent(self, event):
        wx.combo.ComboPopup.OnComboKeyEvent(self, event)

    # Implement if you need to support special action when user
    # double-clicks on the parent wxComboCtrl.
    def OnComboDoubleClick(self):
        wx.combo.ComboPopup.OnComboDoubleClick(self)

    # Return final size of popup. Called on every popup, just prior to OnPopup.
    # minWidth = preferred minimum width for window
    # prefHeight = preferred height. Only applies if > 0,
    # maxHeight = max height for window, as limited by screen size
    #   and should only be rounded down, if necessary.
    def GetAdjustedSize(self, minWidth, prefHeight, maxHeight):
        minWidth = 0
        for n in range(self.lc.GetColumnCount()):
            minWidth += self.lc.GetColumnWidth(n)
        # add a little space for vert scrollbar or horiz scrollbar will appear
        minWidth += 20
        print "minWidth", minWidth
        return wx.combo.ComboPopup.GetAdjustedSize(self, minWidth, prefHeight, maxHeight)

    # Return true if you want delay the call to Create until the popup
    # is shown for the first time. It is more efficient, but note that
    # it is often more convenient to have the control created
    # immediately.
    # Default returns false.
    def LazyCreate(self):
        return wx.combo.ComboPopup.LazyCreate(self)

class maskingPanel(wx.Panel):
    def __init__(self, parent, id):
        wx.Panel.__init__(self, parent, id)
        self.InitUI()

    def InitUI(self):
        #horizontal split means the split goes across
        #vertical split means the split goes up and down
        hSplit = wx.SplitterWindow(self, -1)
        self.maskingSetupPanel = scrolled.ScrolledPanel(hSplit, ID_MASKING_SETUP_PANEL)
        self.InitMaskingSetupPanel(self.maskingSetupPanel)        
#        self.maskingSetupLabel = wx.StaticText(self.maskingSetupPanel, -1, "Set up Masking here")

        self.maskingPreviewPanel = wx.Panel(hSplit, ID_MASKING_PREVIEW_PANEL)
        self.maskingPreviewPanel.SetBackgroundColour(wx.WHITE)
#        self.maskingPreviewLabel = wx.StaticText(self.maskingPreviewPanel, -1, "Preview will be here")
        self.InitPreviewPanel(self.maskingPreviewPanel)
#        hSplit.SetMinimumPaneSize(20)
        hSplit.SetSashGravity(0.5)
        hSplit.SplitHorizontally(self.maskingSetupPanel, self.maskingPreviewPanel)
        vSiz = wx.BoxSizer(wx.VERTICAL)
        vSiz.Add(hSplit, 1, wx.EXPAND)
        self.SetSizer(vSiz)
        return
    
    def InitMaskingSetupPanel(self, pnl):
        self.LayoutMaskingSetupPanel(pnl)

    def LayoutMaskingSetupPanel(self, pnl):

        pnl.SetBackgroundColour(wx.WHITE)
        iLinespan = 5
        stpSiz = wx.GridBagSizer(1, 1)
        
        gRow = 0
        stpLabel = wx.StaticText(pnl, -1, 'Set up Masking here')
        stpSiz.Add(stpLabel, pos=(gRow, 0), span=(1, 2), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)

        gRow += 1
        stpSiz.Add(wx.StaticLine(pnl), pos=(gRow, 0), span=(1, iLinespan), flag=wx.EXPAND)
        
        gRow += 1
        stpSiz.Add(wx.StaticText(pnl, -1, 'Narrow Logger(s) to Station:'),
                     pos=(gRow, 0), span=(1, 2), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)

        stSQLStations = 'SELECT ID, StationName FROM Stations;'
        pnl.cbxStationID = wx.ComboBox(pnl, -1, style=wx.CB_READONLY)
        scidb.fillComboboxFromSQL(pnl.cbxStationID, stSQLStations)
        stpSiz.Add(pnl.cbxStationID, pos=(gRow, 2), span=(1, 3), flag=wx.LEFT, border=5)

        gRow += 1
        stpSiz.Add(wx.StaticText(pnl, -1, 'Narrow Channel choices to Logger:'),
                     pos=(gRow, 0), span=(1, 2), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)

        stSQLLoggers = 'SELECT ID, LoggerSerialNumber FROM Loggers;'
        pnl.cbxLoggerID = wx.ComboBox(pnl, -1, style=wx.CB_READONLY)
        scidb.fillComboboxFromSQL(pnl.cbxLoggerID, stSQLLoggers)
        stpSiz.Add(pnl.cbxLoggerID, pos=(gRow, 2), span=(1, 3), flag=wx.LEFT, border=5)

        gRow += 1
        stpSiz.Add(wx.StaticLine(pnl), pos=(gRow, 0), span=(1, iLinespan), flag=wx.EXPAND)

        gRow += 1
        stpSiz.Add(wx.StaticText(pnl, -1, 'Data Channel:'),
                     pos=(gRow, 0), span=(1, 2), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)

        pnl.cbxChanID = wx.combo.ComboCtrl(pnl, ID_CHAN_TEXT, "", style=wx.CB_READONLY | wx.TE_PROCESS_ENTER)
        pnl.chanPopup = ListCtrlComboPopup()
#        pnl.chanPopup.id = ID_CHAN_LIST
        # It is important to call SetPopupControl() as soon as possible
        pnl.cbxChanID.SetPopupControl(pnl.chanPopup)
        stpSiz.Add(pnl.cbxChanID, pos=(gRow, 2), span=(1, 7), flag=wx.LEFT, border=5)
        stSQLChan = "SELECT DataChannels.ID, " \
            "( DataChannels.Column || ',' ||  Loggers.LoggerSerialNumber || ',' ||  " \
            "Sensors.SensorSerialNumber || ',' ||  DataTypes.TypeText || ',' ||  " \
            "DataUnits.UnitsText || ',' ||  DataChannels.UTC_Offset) AS Channel, " \
            "DataSeries.DataSeriesDescription AS Series, ChannelSegments.SegmentBegin AS Begin " \
            "FROM (((((DataChannels LEFT JOIN Loggers ON DataChannels.LoggerID = Loggers.ID) " \
            "LEFT JOIN Sensors ON DataChannels.SensorID = Sensors.ID) " \
            "LEFT JOIN DataTypes ON DataChannels.DataTypeID = DataTypes.ID) " \
            "LEFT JOIN DataUnits ON DataChannels.DataUnitsID = DataUnits.ID) " \
            "LEFT JOIN ChannelSegments ON DataChannels.ID = ChannelSegments.ChannelID) " \
            "LEFT JOIN DataSeries ON ChannelSegments.SeriesID = DataSeries.ID;"
        scidb.fillComboCtrlPopupFromSQL(pnl.chanPopup, stSQLChan, [300, 180, 140])
#        pnl.chanPopup.AddItem(("a",None,3,4,5,6,7)) # test AddItem w /every imaginable error

        gRow += 1
        stpSiz.Add(wx.StaticLine(pnl), pos=(gRow, 0), span=(1, iLinespan), flag=wx.EXPAND)

        gRow += 1
        stpSiz.Add(wx.StaticText(pnl, -1, 'Universal Time'),
                     pos=(gRow, 1), span=(1, 2), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)

        gRow += 1
        stpSiz.Add(wx.StaticText(pnl, -1, 'Start'),
                     pos=(gRow, 0), span=(1, 1), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.tcDTStart = wx.TextCtrl(pnl, ID_START_TIME, style=wx.TE_PROCESS_ENTER)
        self.tcDTStart.Bind(wx.EVT_TEXT_ENTER, self.OnEnterKey)
        self.tcDTStart.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)
        stpSiz.Add(self.tcDTStart, pos=(gRow, 1), span=(1, 3), 
            flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)
        # for testing
        self.tcDTStart.SetValue('2010-06-13 5am')

        gRow += 1
        stpSiz.Add(wx.StaticText(pnl, -1, 'End'),
                     pos=(gRow, 0), span=(1, 1), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.tcDTEnd = wx.TextCtrl(pnl, ID_END_TIME, style=wx.TE_PROCESS_ENTER)
        self.tcDTEnd.Bind(wx.EVT_TEXT_ENTER, self.OnEnterKey)
        self.tcDTEnd.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)
        stpSiz.Add(self.tcDTEnd, pos=(gRow, 1), span=(1, 3), 
            flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)
        # for testing
        self.tcDTEnd.SetValue('2010-06-14 5pm')

        gRow += 1
        self.ckButton = wx.Button(pnl, -1, 'Test')
        self.Bind(wx.EVT_BUTTON,  self.OnTest, id=self.ckButton.GetId())
        stpSiz.Add(self.ckButton, pos=(gRow, 4), span=(1, 1), 
            flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)

        pnl.SetSizer(stpSiz)
        pnl.SetAutoLayout(1)
        pnl.SetupScrolling()

    def OnKillFocus(self, event):
        # send an event on to the general Check Masking Preview function
        CPevt = CkMaskingPreviewEvent(CkMaskingPreviewEventType, -1)
        CPevt.SetMyCk(['TimeStamp', 'OnKillFocus', event.GetId()])
        self.GetEventHandler().ProcessEvent(CPevt)

    def OnEnterKey(self, event):
        print 'event reached OnEnterKey'
        print 'in OnEnterKey handler, eventID', event.GetId()


    def OnTest(self, event):
        print 'event reached button class of OnText button'
        print self.tcDTStart.GetLineText(0)
        stTryDtStart = self.tcDTStart.GetLineText(0)
        self.dtStart = wx.DateTime() # Uninitialized datetime
        dtStartOK = self.dtStart.ParseDateTime(stTryDtStart)
        print "Start time is OK:", dtStartOK
        print "dtStart", self.dtStart
        sFmt = '%Y-%m-%d %H:%M:%S'
#datetime.datetime.fromtimestamp(wx.DateTime.Now().GetTicks()) 
#wx.DateTimeFromTimeT(time.mktime(datetime.datetime.now().timetuple()))
        
        print "self.dtStart.GetTicks()", self.dtStart.GetTicks()
        dtStartPy = datetime.datetime.fromtimestamp(self.dtStart.GetTicks()) 
#        stStandardizedDateTime = self.dtStart.FormatISOCombined()
#        stStandardizedDateTime = datetime.datetime.strptime(self.dtStart, sFmt)
        print "dtStartPy", dtStartPy
        stStandardizedDateTime = dtStartPy.isoformat(' ')
        print "Standardized DateTime", stStandardizedDateTime
        self.tcDTStart.SetValue(stStandardizedDateTime)
        event.Skip()

    def InitPreviewPanel(self, pnl):
        pnl.SetBackgroundColour('#FFFFFF')
        pvSiz = wx.GridBagSizer(0, 0)
        pvSiz.AddGrowableCol(0)
        
        gRow = 0
        pnl.pvLabel = wx.StaticText(pnl, -1, "Red is Masked data")
        pvSiz.Add(pnl.pvLabel, pos=(gRow, 0), span=(1, 1), flag=wx.TOP|wx.LEFT|wx.BOTTOM|wx.EXPAND, border=5)
        
        gRow += 1
        # Add the FloatCanvas canvas
        pnl.NC = NavCanvas.NavCanvas(pnl,
             ProjectionFun = ScaleCanvas,
             Debug = 0,
             BackgroundColor = "WHITE")
        pnl.Canvas = pnl.NC.Canvas # reference the contained FloatCanvas
        # test of drawing one line
#        self.UnBindAllMouseEvents()
#        self.Canvas.InitAll()
#        self.Canvas.Draw()
#        points = [(-100,-100),(100,100), (100,-100), (-100,100)]
#        self.Canvas.AddLine(points, LineWidth = 1, LineColor = 'BLUE')
#        self.Canvas.ZoomToBB() # this makes the drawing about 10% of the whole canvas, but
        # then the "Zoom To Fit" button correctly expands it to the whole space

        pvSiz.Add(pnl.NC, pos=(gRow, 0), span=(1, 1), flag=wx.EXPAND, border=0)
        pvSiz.AddGrowableRow(gRow)
        pnl.SetSizer(pvSiz)
        pnl.SetAutoLayout(1)

#    def refresh_cbxPanelsChoices(self, event):
#        self.cbxGetPanel.Clear()
#        stSQLPanels = 'SELECT ID, CalcName FROM maskingcalc;'
#        scidb.fillComboboxFromSQL(self.cbxGetPanel, stSQLPanels)

#    def onCbxTasks(self, event):
#        print 'self.cbxTasks selected, choice: "', self.cbxTasks.GetValue(), '"'



class maskingFrame(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title)
        self.statusBar = self.CreateStatusBar()
        self.InitUI()
        self.SetSize((750, 600))
#        self.Centre()
        self.Show(True)

    def InitUI(self):
        framePanel = maskingPanel(self, wx.ID_ANY)


def main():
#    app = wx.App(redirect=False)
    app = MyApp(redirect=False)
#    dsFrame = maskingFrame(None, wx.ID_ANY, 'Data Masking')
    app.MainLoop() 

if __name__ == '__main__':
    main()
