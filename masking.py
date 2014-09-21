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

ID_CBX_SEL_STATION= wx.NewId()
ID_CBX_SEL_LOGGER= wx.NewId()
ID_MASKING_SETUP_PANEL = wx.NewId()
ID_MASKING_PREVIEW_PANEL = wx.NewId()
ID_CHAN_TEXT = wx.NewId()
ID_CHAN_LIST = wx.NewId()
ID_START_TIME = wx.NewId()
ID_END_TIME = wx.NewId()
ID_APPLY_BTN = wx.NewId()
ID_RB_MASK = wx.NewId()
ID_RB_UNMASK = wx.NewId()
ID_ST_DAY_DN_BTN = wx.NewId()
ID_ST_HOUR_DN_BTN = wx.NewId()
ID_ST_HOUR_UP_BTN = wx.NewId()
ID_ST_DAY_UP_BTN = wx.NewId()
ID_EN_DAY_DN_BTN = wx.NewId()
ID_EN_HOUR_DN_BTN = wx.NewId()
ID_EN_HOUR_UP_BTN = wx.NewId()
ID_EN_DAY_UP_BTN = wx.NewId()

ID_Starts = [ID_ST_DAY_DN_BTN, ID_ST_HOUR_DN_BTN, ID_ST_HOUR_UP_BTN, ID_ST_DAY_UP_BTN]
ID_Ends = [ID_EN_DAY_DN_BTN, ID_EN_HOUR_DN_BTN, ID_EN_HOUR_UP_BTN, ID_EN_DAY_UP_BTN]
ID_TimeAdjusts = ID_Starts + ID_Ends

CkMaskingPreviewEventType = wx.NewEventType()
EVT_CK_MASKING_PREVIEW = wx.PyEventBinder(CkMaskingPreviewEventType, 1)

sFmt = '%Y-%m-%d %H:%M:%S'

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
        tpFrame = self.GetTopWindow()
        pvPnl = tpFrame.FindWindowById(ID_MASKING_PREVIEW_PANEL)
        self.pvCanvas = pvPnl.Canvas
        self.Bind(EVT_CK_MASKING_PREVIEW, self.CkMaskingPreview)
        self.Bind(wx.EVT_BUTTON, self.OnButton)
        self.statBar = self.dsFrame.statusBar
        self.statBar.SetStatusText('Select Data Channel, and Start and End timestamps')
        return True

    def OnButton(self, event):
        event_id = event.GetId()
        if event_id == ID_APPLY_BTN: #
            print "ID_APPLY_BTN Event reached OnButton at App level"
            self.SvcApplyMaskButton()
        if event_id in ID_TimeAdjusts:
            self.AdjustTimeRange(event_id)

    def AdjustTimeRange(self, event_id):
        if not self.PreviewControlsValid():
            return
        if event_id in ID_Starts:
            if event_id == ID_ST_DAY_DN_BTN:
                self.statBar.SetStatusText('Start time down by one day')
                self.dStart = self.dStart - datetime.timedelta(days=1)

            if event_id == ID_ST_HOUR_DN_BTN:
                self.statBar.SetStatusText('Start time down by one hour')
                self.dStart = self.dStart - datetime.timedelta(hours=1)

            if event_id == ID_ST_HOUR_UP_BTN:
                self.statBar.SetStatusText('Start time up by one hour')
                self.dStart = self.dStart + datetime.timedelta(hours=1)

            if event_id == ID_ST_DAY_UP_BTN:
                self.statBar.SetStatusText('Start time up by one day')
                self.dStart = self.dStart + datetime.timedelta(days=1)

            self.stUseStart = self.dStart.strftime(sFmt)
            tpFrame = self.GetTopWindow()
            txStartTime = tpFrame.FindWindowById(ID_START_TIME)
            txStartTime.SetValue(self.stUseStart)

        if event_id in ID_Ends:
            if event_id == ID_EN_DAY_DN_BTN:
                self.statBar.SetStatusText('End time down by one day')
                self.dEnd = self.dEnd - datetime.timedelta(days=1)

            if event_id == ID_EN_HOUR_DN_BTN:
                self.statBar.SetStatusText('End time down by one hour')
                self.dEnd = self.dEnd - datetime.timedelta(hours=1)

            if event_id == ID_EN_HOUR_UP_BTN:
                self.statBar.SetStatusText('End time up by one hour')
                self.dEnd = self.dEnd + datetime.timedelta(hours=1)

            if event_id == ID_EN_DAY_UP_BTN:
                self.statBar.SetStatusText('End time up by one day')
                self.dEnd = self.dEnd + datetime.timedelta(days=1)

            self.stUseEnd = self.dEnd.strftime(sFmt)
            tpFrame = self.GetTopWindow()
            txEndTime = tpFrame.FindWindowById(ID_END_TIME)
            txEndTime.SetValue(self.stUseEnd)

        self.PreviewControlsValid() # re-fetch parameters
        self.ShowMaskingPreview()

    def SvcApplyMaskButton(self):
        if not self.PreviewControlsValid():
            return
        tpFrame = self.GetTopWindow()
        radioButtonMask = tpFrame.FindWindowById(ID_RB_MASK)
        if radioButtonMask.GetValue():
            iSense = 0
        else:
            iSense = 1

        stSQLMask = """UPDATE Data SET Use = {iS}
        WHERE Data.ChannelID = {iCh}
        AND Data.UTTimestamp >= '{sDs}'
        AND Data.UTTimestamp <= '{sDe}'
        """.format(iS=iSense, iCh=self.ChanID, sDs=self.stUseStart, sDe=self.stUseEnd)

        scidb.curD.execute(stSQLMask)
        self.statBar.SetStatusText('Showing mask results')
        self.ShowMaskingPreview()

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

        if event_id == ID_APPLY_BTN: # does not hit here
            print "ID_APPLY_BTN Event reached CkMaskingPreview at App level"
        
        if self.PreviewControlsValid():
            self.dsFrame.statusBar.SetStatusText('Creating preview for ' + self.stItem)
            self.ShowMaskingPreview()

    def PreviewControlsValid(self):
        """
         This function tests whether the variables needed for a preview are valid
        These are ChannelID, and Start and End times
        If they all are, returns True, otherwise False
        Any error messages appear in the statusbar
        If all are valid, these class variables are set:
        - ChanID, stUseStart, and stUseEnd
        - scaleY, the scaling factor for Y data
        - stItem, the verbose information about the channel
        - fDataMin
        - fDataMax
        - totSecs
        """
        tpFrame = self.GetTopWindow()
        # get ChannelID, if selected
        txChanText = tpFrame.FindWindowById(ID_CHAN_TEXT)
        msPnl = tpFrame.FindWindowById(ID_MASKING_SETUP_PANEL)
        pUp = msPnl.chanPopup # popup is an attibute of the panel, though the panel is not its parent
        ls = pUp.GetControl() # direct handle to the popup's control, which is the listCtrl
        # to retrieve the hidden key number stored in the popup list row (e.g. a DB record ID):
        curItem = pUp.curitem
        if curItem == -1:
            self.ChanID = 0 # something to flag invalid
            self.dsFrame.statusBar.SetStatusText('Select a Data Channel for a masking preview')
            self.stItem = ''
            return False
        else:
            self.ChanID = ls.GetItemData(curItem)
            self.dsFrame.statusBar.SetStatusText('Data Channel ' + str(self.ChanID) + ' selected')
            # the selection may happen without filling the textbox; explicitly fill textbox
            self.stItem = ls.GetItemText(curItem)
            txChanText.SetValue(self.stItem)
#            print "Current list item", ls.GetItemText(curItem)

        # validate timestamps
        txStartTime = tpFrame.FindWindowById(ID_START_TIME)
        stDTStart = txStartTime.GetValue()
        if stDTStart.strip() == '': # empty timestamp is valid, meaning first in channel
            # get the earliest timestamp for this channel
            stSQLmin = """SELECT MIN(UTTimestamp) AS DataFirst FROM Data 
                WHERE Data.ChannelID = {iCh};
                """.format(iCh=self.ChanID)
            self.stUseStart = scidb.curD.execute(stSQLmin).fetchone()['DataFirst']
            txStartTime.SetValue(self.stUseStart)
            stMsg = 'Season-long previews may take several seconds to display.'
            dlg = wx.MessageDialog(msPnl, stMsg, 'Note', wx.OK)
            result = dlg.ShowModal()
            dlg.Destroy()
        else: # test the control for valid date/time
            dtStart = wx.DateTime() # Uninitialized datetime
            StartTimeValid = dtStart.ParseDateTime(stDTStart)
#            print "StartTimeValid", StartTimeValid
            if StartTimeValid == -1:
                self.dsFrame.statusBar.SetStatusText('Start time is not valid')
                self.stUseStart = ''
                return False
            else:
                # remember the timestamp and write it back to the control in standard format
                self.stUseStart = dtStart.Format(sFmt)
                txStartTime.SetValue(self.stUseStart)

        txEndTime = tpFrame.FindWindowById(ID_END_TIME)
        stDTEnd = txEndTime.GetValue()
        if stDTEnd.strip() == '': # empty timestamp is valid, meaning last in channel
            # get the latest timestamp for this channel
            stSQLmax = """SELECT MAX(UTTimestamp) AS DataLast FROM Data 
                WHERE Data.ChannelID = {iCh};
                """.format(iCh=self.ChanID)
            self.stUseEnd = scidb.curD.execute(stSQLmax).fetchone()['DataLast']
            txEndTime.SetValue(self.stUseEnd)
            stMsg = 'Season-long previews may take several seconds to display.'
            dlg = wx.MessageDialog(msPnl, stMsg, 'Note', wx.OK)
            result = dlg.ShowModal()
            dlg.Destroy()
        else: # test the control for valid date/time
            dtEnd = wx.DateTime() # Uninitialized datetime
            EndTimeValid = dtEnd.ParseDateTime(stDTEnd)
            if EndTimeValid == -1:
                self.dsFrame.statusBar.SetStatusText('End time is not valid')
                self.stUseEnd = ''
                return False
            else:
                # remember the timestamp and write it back to the control in standard format
                self.stUseEnd = dtEnd.Format(sFmt)
                txEndTime.SetValue(self.stUseEnd)

        self.dsFrame.statusBar.SetStatusText('Getting data range for ' + self.stItem)
        stSQLMinMax = """SELECT MIN(CAST(Data.Value AS FLOAT)) AS MinData,
            MAX(CAST(Data.Value AS FLOAT)) AS MaxData
            FROM Data
            WHERE Data.ChannelID = {iCh}
            AND Data.UTTimestamp >= '{sDs}'
            AND Data.UTTimestamp <= '{sDe}';
            """.format(iCh=self.ChanID, sDs=self.stUseStart, sDe=self.stUseEnd)
        MnMxRec = scidb.curD.execute(stSQLMinMax).fetchone()
        self.fDataMin = MnMxRec['MinData']
        self.fDataMax = MnMxRec['MaxData']
        print "Min", self.fDataMin, "Max", self.fDataMax
        self.dStart = datetime.datetime.strptime(self.stUseStart, sFmt)
        self.dEnd = datetime.datetime.strptime(self.stUseEnd, sFmt)
        self.totSecs = (self.dEnd - self.dStart).total_seconds()
        print 'totSecs', self.totSecs
        if self.fDataMax == self.fDataMin:
            self.scaleY = 0
        else:
            self.scaleY = (self.totSecs * 0.618) / (self.fDataMax - self.fDataMin)
        return True
        
    def ShowMaskingPreview(self):
        """
        Shows the points (red=masked, blue=unmasked) for the channel for the time frame
        selected. Requires that self.ChanID, self.stUseStart, self.stUseEnd, and self.scaleY
        be validated before entering this function. Also, should have previously assigned
        self.statBar = self.dsFrame.statusBar
        self.pvCanvas = pvPnl.Canvas
        """
        secsExtra = 0.9 * self.totSecs
        stSQLUsed = """SELECT strftime('%s', Data.UTTimestamp) - strftime('%s', '{sDs}') AS Secs,
            Data.Value * {fSy} AS Val
            FROM Data
            WHERE Data.ChannelID = {iCh} 
            AND Data.UTTimestamp >= DATETIME('{sDs}', '-{iSe} seconds')
            AND Data.UTTimestamp <= DATETIME('{sDe}', '+{iSe} seconds')
            AND Data.Use = 1
            ORDER BY Secs;
            """.format(iCh=self.ChanID, sDs=self.stUseStart, sDe=self.stUseEnd, fSy=self.scaleY, iSe=secsExtra)
        ptRecs = scidb.curD.execute(stSQLUsed).fetchall()
        ptsUsed = []
        for ptRec in ptRecs:
#                print ptRec['Secs'], ptRec['Value']
            ptsUsed.append((ptRec['Secs'], ptRec['Val']))
        iLU = len(ptsUsed)
        stSQLMasked = """SELECT strftime('%s', Data.UTTimestamp) - strftime('%s', '{sDs}') AS Secs,
            Data.Value * {fSy} AS Val
            FROM Data
            WHERE Data.ChannelID = {iCh} 
            AND Data.UTTimestamp >= DATETIME('{sDs}', '-{iSe} seconds')
            AND Data.UTTimestamp <= DATETIME('{sDe}', '+{iSe} seconds')
            AND Data.Use = 0
            ORDER BY Secs;
            """.format(iCh=self.ChanID, sDs=self.stUseStart, sDe=self.stUseEnd, fSy=self.scaleY, iSe=secsExtra)
        ptRecs = scidb.curD.execute(stSQLMasked).fetchall()
        ptsMasked = []
        for ptRec in ptRecs:
#                print ptRec['Secs'], ptRec['Value']
            ptsMasked.append((ptRec['Secs'], ptRec['Val']))
        iLM = len(ptsMasked)
        print "Points used:", len(ptsUsed)
        print "Points masked:", len(ptsMasked)
        if iLU + iLM == 0:
            self.statBar.SetStatusText('no data for this time range')

#        self.UnBindAllMouseEvents()
# self.pvCanvas
        self.pvCanvas.InitAll()
        self.pvCanvas.Draw()
        if iLU + iLM == 0:
            stNoData = "No data for this time range"
            pt = (0,0)
            self.pvCanvas.AddScaledText(stNoData, pt, Size = 10, Color = 'BLACK', Position = "cc")
        else: # show the preview
            # draw the bounding box
            yExtra = 0.1 * (self.fDataMax - self.fDataMin) * self.scaleY
            xy = (-0.5, (self.fDataMin * self.scaleY) - yExtra)
            wh = (self.totSecs + 2.5, ((self.fDataMax - self.fDataMin) * self.scaleY) + (2 * yExtra))
#            self.pvCanvas.AddRectangle(xy, wh, LineWidth = 1, LineColor = 'GREEN', FillColor = None, FillStyle = 'Transparent')
            # draw bounding brackets
            bracketPtLen = 0.2 * self.totSecs
            yBase = (self.fDataMin * self.scaleY) - yExtra
            yHt = ((self.fDataMax - self.fDataMin) * self.scaleY) + (2 * yExtra)
            ptsLBracket = []
            ptsLBracket.append((bracketPtLen - 0.5, yBase + yHt))
            ptsLBracket.append((-0.5, yBase + yHt))
            ptsLBracket.append((-0.5, yBase))
            ptsLBracket.append((bracketPtLen - 0.5, yBase))
            self.pvCanvas.AddLine(ptsLBracket, LineWidth = 1, LineColor = 'BLACK')

            ptsRBracket = []
            ptsRBracket.append((self.totSecs + 0.5 - bracketPtLen, yBase + yHt))
            ptsRBracket.append((self.totSecs + 0.5, yBase + yHt))
            ptsRBracket.append((self.totSecs + 0.5, yBase))
            ptsRBracket.append((self.totSecs + 0.5 - bracketPtLen, yBase))
            self.pvCanvas.AddLine(ptsRBracket, LineWidth = 1, LineColor = 'BLACK')


            # display the points
            if iLU > 0:
                self.pvCanvas.AddPointSet(ptsUsed, Color = 'BLUE', Diameter = 1)
            if iLM > 0:
                self.pvCanvas.AddPointSet(ptsMasked, Color = 'RED', Diameter = 1)
        self.pvCanvas.ZoomToBB() # fit the whole space
        

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
    # Default returns False.
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
        self.cbxStationID = wx.ComboBox(pnl, ID_CBX_SEL_STATION, style=wx.CB_READONLY)
        scidb.fillComboboxFromSQL(self.cbxStationID, stSQLStations)
        stpSiz.Add(self.cbxStationID, pos=(gRow, 2), span=(1, 3), flag=wx.LEFT, border=5)

        gRow += 1
        stpSiz.Add(wx.StaticText(pnl, -1, 'Narrow Channel choices to Logger:'),
                     pos=(gRow, 0), span=(1, 2), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)

        stSQLLoggers = 'SELECT ID, LoggerSerialNumber FROM Loggers;'
        pnl.cbxLoggerID = wx.ComboBox(pnl, ID_CBX_SEL_LOGGER, style=wx.CB_READONLY)
        scidb.fillComboboxFromSQL(pnl.cbxLoggerID, stSQLLoggers)
        stpSiz.Add(pnl.cbxLoggerID, pos=(gRow, 2), span=(1, 3), flag=wx.LEFT, border=5)

        self.Bind(wx.EVT_COMBOBOX, self.OnSelect)

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
        stpSiz.Add(wx.StaticText(pnl, -1, 'Time interval to view, in Universal Time'),
                     pos=(gRow, 1), span=(1, 5), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)

        gRow += 1
        stpSiz.Add(wx.StaticText(pnl, -1, 'Start'),
                     pos=(gRow, 0), span=(1, 1), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.tcDTStart = wx.TextCtrl(pnl, ID_START_TIME, style=wx.TE_PROCESS_ENTER)
        self.tcDTStart.Bind(wx.EVT_TEXT_ENTER, self.OnEnterKey)
        self.tcDTStart.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)
        stpSiz.Add(self.tcDTStart, pos=(gRow, 1), span=(1, 3), 
            flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)
#        self.tcDTStart.SetValue('2010-06-13 5pm') # for testing
        self.tcDTStart.SetValue('timestamp, or blank for first in Channel')

        # add StartTime adjustment buttons
        sbHorizSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.StartDayDnButton = wx.Button(pnl, ID_ST_DAY_DN_BTN, '<Da', style=wx.BU_EXACTFIT)
        self.Bind(wx.EVT_BUTTON,  self.OnTimeAdjustButton, id=ID_ST_DAY_DN_BTN)
        sbHorizSizer.Add(self.StartDayDnButton)

        self.StartHourDnButton = wx.Button(pnl, ID_ST_HOUR_DN_BTN, '<Hr', style=wx.BU_EXACTFIT)
        self.Bind(wx.EVT_BUTTON,  self.OnTimeAdjustButton, id=ID_ST_HOUR_DN_BTN)
        sbHorizSizer.Add(self.StartHourDnButton)

        self.StartHourUpButton = wx.Button(pnl, ID_ST_HOUR_UP_BTN, 'Hr>', style=wx.BU_EXACTFIT)
        self.Bind(wx.EVT_BUTTON,  self.OnTimeAdjustButton, id=ID_ST_HOUR_UP_BTN)
        sbHorizSizer.Add(self.StartHourUpButton)

        self.StartDayUpButton = wx.Button(pnl, ID_ST_DAY_UP_BTN, 'Da>', style=wx.BU_EXACTFIT)
        self.Bind(wx.EVT_BUTTON,  self.OnTimeAdjustButton, id=ID_ST_DAY_UP_BTN)
        sbHorizSizer.Add(self.StartDayUpButton)

        stpSiz.Add(sbHorizSizer, pos=(gRow, 4), span=(1, 1))

        gRow += 1
        stpSiz.Add(wx.StaticText(pnl, -1, 'End'),
                     pos=(gRow, 0), span=(1, 1), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.tcDTEnd = wx.TextCtrl(pnl, ID_END_TIME, style=wx.TE_PROCESS_ENTER)
        self.tcDTEnd.Bind(wx.EVT_TEXT_ENTER, self.OnEnterKey)
        self.tcDTEnd.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)
        stpSiz.Add(self.tcDTEnd, pos=(gRow, 1), span=(1, 3), 
            flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)
        
#        self.tcDTEnd.SetValue('2010-06-14 5pm') # for testing
        self.tcDTEnd.SetValue('timestamp, or blank for last in Channel')

        # add EndTime adjustment buttons
        ebHorizSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.EndDayDnButton = wx.Button(pnl, ID_EN_DAY_DN_BTN, '<Da', style=wx.BU_EXACTFIT)
        self.Bind(wx.EVT_BUTTON,  self.OnTimeAdjustButton, id=ID_EN_DAY_DN_BTN)
        ebHorizSizer.Add(self.EndDayDnButton)

        self.EndHourDnButton = wx.Button(pnl, ID_EN_HOUR_DN_BTN, '<Hr', style=wx.BU_EXACTFIT)
        self.Bind(wx.EVT_BUTTON,  self.OnTimeAdjustButton, id=ID_EN_HOUR_DN_BTN)
        ebHorizSizer.Add(self.EndHourDnButton)

        self.EndHourUpButton = wx.Button(pnl, ID_EN_HOUR_UP_BTN, 'Hr>', style=wx.BU_EXACTFIT)
        self.Bind(wx.EVT_BUTTON,  self.OnTimeAdjustButton, id=ID_EN_HOUR_UP_BTN)
        ebHorizSizer.Add(self.EndHourUpButton)

        self.EndDayUpButton = wx.Button(pnl, ID_EN_DAY_UP_BTN, 'Da>', style=wx.BU_EXACTFIT)
        self.Bind(wx.EVT_BUTTON,  self.OnTimeAdjustButton, id=ID_EN_DAY_UP_BTN)
        ebHorizSizer.Add(self.EndDayUpButton)

        stpSiz.Add(ebHorizSizer, pos=(gRow, 4), span=(1, 1))
        
        gRow += 1
        stpSiz.Add(wx.StaticLine(pnl), pos=(gRow, 0), span=(1, iLinespan), flag=wx.EXPAND)

        gRow += 1
        mrbVertSizer = wx.BoxSizer(wx.VERTICAL)
        
        self.rbMask = wx.RadioButton(pnl, ID_RB_MASK, label='Mask', style=wx.RB_GROUP)
        mrbVertSizer.Add(self.rbMask, proportion=0, flag=wx.ALIGN_LEFT|wx.LEFT)
        self.rbMask.Bind(wx.EVT_RADIOBUTTON, self.giveRBInfo)

        self.rbUnmask = wx.RadioButton(pnl, ID_RB_UNMASK, label='Unmask')
        mrbVertSizer.Add(self.rbUnmask, proportion=0, flag=wx.ALIGN_LEFT|wx.LEFT)
        self.rbUnmask.Bind(wx.EVT_RADIOBUTTON, self.giveRBInfo)

        iRBLeftBorderWd = 30
        stpSiz.Add(mrbVertSizer, pos=(gRow, 0), span=(1, 2), 
            flag=wx.ALIGN_LEFT|wx.LEFT, border=iRBLeftBorderWd)

        self.applyButton = wx.Button(pnl, ID_APPLY_BTN, 'Apply')
        self.Bind(wx.EVT_BUTTON,  self.OnApplyBtn, id=ID_APPLY_BTN)
        stpSiz.Add(self.applyButton, pos=(gRow, 3), span=(1, 1), 
            flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)

        self.giveRBInfo(-1) # have to explictly call this 1st time; -1 is dummy value for event

        pnl.SetSizer(stpSiz)
        pnl.SetAutoLayout(1)
        pnl.SetupScrolling()

    def OnSelect(self, event):
        item = event.GetSelection()
        event_id = event.GetId()
        if event_id == ID_CBX_SEL_STATION:
            keyItem = self.cbxStationID.GetClientData(item)
            print 'Station cbx, item ', item, 'key', keyItem
        if event_id == ID_CBX_SEL_LOGGER:
            print 'Logger cbx, item ', item


    def OnTimeAdjustButton(self, event):
        event.Skip()
        
    def OnKillFocus(self, event):
        # send an event on to the general Check Masking Preview function
        CPevt = CkMaskingPreviewEvent(CkMaskingPreviewEventType, -1)
        CPevt.SetMyCk(['TimeStamp', 'OnKillFocus', event.GetId()])
        self.GetEventHandler().ProcessEvent(CPevt)

    def OnEnterKey(self, event):
        print 'event reached OnEnterKey'
        print 'in OnEnterKey handler, eventID', event.GetId()

    def OnApplyBtn(self, event):
        print 'event reached button class of Apply button'
        event.Skip()

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
             ProjectionFun = None,
             Debug = 0,
             BackgroundColor = "WHITE")
        pnl.Canvas = pnl.NC.Canvas # reference the contained FloatCanvas

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

    def giveRBInfo(self, event):
        """
        Give the user some information about this option
        """
        stMsg = ''
        if self.rbMask.GetValue():
            stMsg = ' Data will be masked.'
        if self.rbUnmask.GetValue():
            stMsg = ' Data will be unmasked.'
        # maybe implement message in status bar
        print stMsg
#        self.tcOutputOptInfo.SetValue(stMsg)
        return

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
