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

ID_MASKING_SETUP_PANEL = wx.NewId()
ID_MASKING_PREVIEW_PANEL = wx.NewId()
ID_CHAN_TEXT = wx.NewId()
ID_CHAN_LIST = wx.NewId()
ID_START_TIME = wx.NewId()
ID_END_TIME = wx.NewId()

CkMaskingPreviewEventType = wx.NewEventType()
EVT_CK_MASKING_PREVIEW = wx.PyEventBinder(CkMaskingPreviewEventType, 1)
    
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
        self.Bind(wx.EVT_TEXT, self.OnTextChangeApp)
        self.Bind(EVT_CK_MASKING_PREVIEW, self.CkMaskingPreview)
        return True

    def CkMaskingPreview(self, event):
        event_id = event.GetId()
        ck = event.GetMyCk() # retrieve a parameter
        print "in CkMaskingPreview; event Check:", ck

    def OnTextChangeApp(self, event):
        event_id = event.GetId()

        if event_id == ID_START_TIME:
            print "ID_START_TIME Event reached the App Object"

        if event_id == ID_END_TIME:
            print "ID_END_TIME Event reached the App Object"

        if event_id == ID_CHAN_LIST: # does not hit here
            print "ID_CHAN_LIST Event reached the App Object"
        if event_id == ID_CHAN_TEXT:
            print "ID_CHAN_TEXT Event reached the App Object"

            tpFrame = self.GetTopWindow()
            txChanText = tpFrame.FindWindowById(ID_CHAN_TEXT)
#            print "txChanText", txChanText.GetValue()
            msPnl = tpFrame.FindWindowById(ID_MASKING_SETUP_PANEL)
#            msPnl = txChanText.GetParent() # or this, text and popup are attributes of the same panel

#            pUp = tpFrame.FindWindowById(ID_POPUP_LIST) # this is wrong, gets the list instead of the popup object
            pUp = msPnl.chanPopup # popup is an attibute of the panel, though the panel is not its parent
            ls = pUp.GetControl() # direct handle to the popup's control, which is the list
#            ls = tpFrame.FindWindowById(ID_POPUP_LIST) # or this
            print "Popup list has %i columns" % ls.GetColumnCount()
            # to retrieve the hidden key number stored in the popup list row (e.g. a DB record ID):
            curItem = pUp.curitem
            if curItem == -1:
                keyVal = 0 # something to flag invalid
            else:
                keyVal = ls.GetItemData(curItem)
            print "keyVal", keyVal
# following does not work, selected item in list no longer has focus
#            keyItem = ls.GetItemData(ls.GetFocusedItem())
#            print "keyItem", keyItem

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
        CPevt.SetMyCk(-999)
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
        print 'event reached OnKillFocus'
        print 'in OnKillFocus handler, eventID', event.GetId()
#        self.TryPreview(event.GetId())

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
        
    def TryPreview(self, ctrlID):
        """
        Generic function that sees if there is enough inforation to display
        a preview, and if so does.
        ctrlID is from the textbox that lost focus, or the combobox that was updated,
        to feed into this function; may or may not use.
        """
        print 'in TryPreview function'
        print 'eventID', ctrlID

        print 'self.chanPopup.value', self.chanPopup.value
        print 'self.chanPopup.curitem', self.chanPopup.curitem
        ls = self.chanPopup.GetControl()
        if self.chanPopup.curitem == -1:
            keyItem = None
        else:
            keyItem = ls.GetItemData(self.chanPopup.curitem)
        print "keyItem", keyItem
 #       print 'self.cbxChanID.value', self.cbxChanID.value
 #       print 'self.cbxChanID.curitem', self.cbxChanID.curitem
        print "\nGet the Application Object:"
        app = wx.GetApp()
        print "%s" % repr(app)
        print "\nGet the Frame from the App:"
        frame = app.GetTopWindow()
        print "%s" % repr(frame)
#        print "\nFrame GetChildren:"
#        for child in frame.GetChildren():
#            print "\t%s" % repr(child)
#            for grchild in child.GetChildren():
#                print "\t\t%s" % repr(grchild)
        txbStartTime = frame.FindWindowById(ID_START_TIME)
        print "txbStartTime", txbStartTime.GetValue()
#        txbChanText = frame.FindWindowById(ID_CHAN_TEXT)
#        print "txbChanText", txbChanText.GetValue()
        
    def ScalePreviewCanvas(self, center):
        """
        function that returns a scaling vector to scale y and x relative to each other

        """
        # center gets ignored in this case
        # returns a vector that multiplies X and Y
        return [20,1] # rule of thumb

    def InitPreviewPanel(self, pnl):
        pnl.SetBackgroundColour('#FFFFFF')
        pvSiz = wx.GridBagSizer(0, 0)
        pvSiz.AddGrowableCol(0)
        
        gRow = 0
        self.pvLabel = wx.StaticText(pnl, -1, "Red is Masked data")
        pvSiz.Add(self.pvLabel, pos=(gRow, 0), span=(1, 1), flag=wx.TOP|wx.LEFT|wx.BOTTOM|wx.EXPAND, border=5)
        
        gRow += 1
        # Add the FloatCanvas canvas
        self.NC = NavCanvas.NavCanvas(pnl,
             ProjectionFun = self.ScalePreviewCanvas,
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

#    def refresh_cbxPanelsChoices(self, event):
#        self.cbxGetPanel.Clear()
#        stSQLPanels = 'SELECT ID, CalcName FROM maskingcalc;'
#        scidb.fillComboboxFromSQL(self.cbxGetPanel, stSQLPanels)

#    def onCbxTasks(self, event):
#        print 'self.cbxTasks selected, choice: "', self.cbxTasks.GetValue(), '"'



class maskingFrame(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title)
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
