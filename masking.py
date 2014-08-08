import wx, sqlite3, datetime, copy, csv
import os, sys, re, cPickle, datetime
import scidb
import wx.lib.scrolledpanel as scrolled, wx.grid
import multiprocessing
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin
from wx.lib.wordwrap import wordwrap
import wx.combo

try:
    from floatcanvas import NavCanvas, FloatCanvas, Resources
except ImportError: # if it's not there locally, try the wxPython lib.
    from wx.lib.floatcanvas import NavCanvas, FloatCanvas, Resources
import wx.lib.colourdb

"""
A simple test case for wx.ComboCtrl using a wx.ListCtrl for the popup
"""

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
#        wx.ComboPopup.__init__(self)
#        self.lc = None

    def AddItem(self, txt):
        self.lc.InsertItem(self.lc.GetItemCount(), txt)

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
        self.lc = wx.ListCtrl(parent, -1, style=wx.LC_LIST | wx.LC_SINGLE_SEL | wx.SIMPLE_BORDER)

        self.lc.InsertColumn(0, 'State')
        self.lc.InsertColumn(1, 'Capital')
        self.lc.SetColumnWidth(0, 140)
        self.lc.SetColumnWidth(1, 153)

        num_items = self.lc.GetItemCount()
        self.lc.InsertStringItem(num_items, 'Alabama')
        self.lc.SetStringItem(num_items, 1, 'Montgomery')
        self.lc.InsertStringItem(num_items, 'New York')
        self.lc.SetStringItem(num_items, 1, 'Albany')
        self.lc.InsertStringItem(num_items, 'Nebraska')
        self.lc.SetStringItem(num_items, 1, 'Lincoln')

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
        minWidth = self.lc.GetColumnWidth(0) + self.lc.GetColumnWidth(1)
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
        self.maskingSetupPanel = scrolled.ScrolledPanel(hSplit, -1)
        self.InitMaskingSetupPanel(self.maskingSetupPanel)        
#        self.maskingSetupLabel = wx.StaticText(self.maskingSetupPanel, -1, "Set up Masking here")

        self.maskingPreviewPanel = wx.Panel(hSplit, -1)
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
        self.cbxStationID = wx.ComboBox(pnl, -1, style=wx.CB_READONLY)
        scidb.fillComboboxFromSQL(self.cbxStationID, stSQLStations)
        stpSiz.Add(self.cbxStationID, pos=(gRow, 2), span=(1, 3), flag=wx.LEFT, border=5)

        gRow += 1
        stpSiz.Add(wx.StaticText(pnl, -1, 'Narrow Channel choices to Logger:'),
                     pos=(gRow, 0), span=(1, 2), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)

        stSQLLoggers = 'SELECT ID, LoggerSerialNumber FROM Loggers;'
        self.cbxLoggerID = wx.ComboBox(pnl, -1, style=wx.CB_READONLY)
        scidb.fillComboboxFromSQL(self.cbxLoggerID, stSQLLoggers)
        stpSiz.Add(self.cbxLoggerID, pos=(gRow, 2), span=(1, 3), flag=wx.LEFT, border=5)

    
        gRow += 1
        stpSiz.Add(wx.StaticText(pnl, -1, 'Data Channel:'),
                     pos=(gRow, 0), span=(1, 2), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        
        stSQLChan = "SELECT DataChannels.ID, " \
            "( DataChannels.Column || ',' ||  Loggers.LoggerSerialNumber || ',' ||  " \
            "Sensors.SensorSerialNumber || ',' ||  DataTypes.TypeText || ',' ||  " \
            "DataUnits.UnitsText || ',' ||  DataChannels.UTC_Offset) AS Unq, " \
            "DataSeries.DataSeriesDescription, ChannelSegments.SegmentBegin " \
            "FROM (((((DataChannels LEFT JOIN Loggers ON DataChannels.LoggerID = Loggers.ID) " \
            "LEFT JOIN Sensors ON DataChannels.SensorID = Sensors.ID) " \
            "LEFT JOIN DataTypes ON DataChannels.DataTypeID = DataTypes.ID) " \
            "LEFT JOIN DataUnits ON DataChannels.DataUnitsID = DataUnits.ID) " \
            "LEFT JOIN ChannelSegments ON DataChannels.ID = ChannelSegments.ChannelID) " \
            "LEFT JOIN DataSeries ON ChannelSegments.SeriesID = DataSeries.ID;"
        self.cbxChanID = wx.ComboBox(pnl, -1, style=wx.CB_READONLY)
        scidb.fillComboboxFromSQL(self.cbxChanID, stSQLChan)
        stpSiz.Add(self.cbxChanID, pos=(gRow, 2), span=(1, 3), flag=wx.LEFT, border=5)
        stSQLSeries = 'SELECT ID, DataSeriesDescription FROM DataSeries;'

        gRow += 1
        stpSiz.Add(wx.StaticLine(pnl), pos=(gRow, 0), span=(1, iLinespan), flag=wx.EXPAND)

        gRow += 1
        # test creating a comboCtrl
        self.comboCtrl = wx.combo.ComboCtrl(pnl, wx.ID_ANY, "")
#        self.popupCtrl = wx.combo.ListViewComboPopup()
        self.popupCtrl = ListCtrlComboPopup()

        # It is important to call SetPopupControl() as soon as possible
        self.comboCtrl.SetPopupControl(self.popupCtrl)

        # Populate using wx.ListView methods
#        i=self.popupCtrl.GetItemCount() # dummy variable, will change with each InsertStringItem
#        self.popupCtrl.InsertStringItem(i, "First Item")
#        self.popupCtrl.InsertItem(self.popupCtrl.GetItemCount(), "First Item")
#        self.popupCtrl.InsertItem(self.popupCtrl.GetItemCount(), "Second Item")
#        self.popupCtrl.InsertItem(self.popupCtrl.GetItemCount(), "Third Item")

        stpSiz.Add(self.comboCtrl, pos=(gRow, 2), span=(1, 5), flag=wx.LEFT, border=5)

        gRow += 1
        stpSiz.Add(wx.StaticLine(pnl), pos=(gRow, 0), span=(1, iLinespan), flag=wx.EXPAND)

        gRow += 1
        stpSiz.Add(wx.StaticLine(pnl), pos=(gRow, 0), span=(1, iLinespan), flag=wx.EXPAND)

        gRow += 1
        stpSiz.Add(wx.StaticLine(pnl), pos=(gRow, 0), span=(1, iLinespan), flag=wx.EXPAND)

        gRow += 1
        stpSiz.Add(wx.StaticLine(pnl), pos=(gRow, 0), span=(1, iLinespan), flag=wx.EXPAND)

        pnl.SetSizer(stpSiz)
        pnl.SetAutoLayout(1)
        pnl.SetupScrolling()



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

    def refresh_cbxPanelsChoices(self, event):
        self.cbxGetPanel.Clear()
        stSQLPanels = 'SELECT ID, CalcName FROM maskingcalc;'
        scidb.fillComboboxFromSQL(self.cbxGetPanel, stSQLPanels)

    def onCbxTasks(self, event):
        print 'self.cbxTasks selected, choice: "', self.cbxTasks.GetValue(), '"'



class maskingFrame(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title)
        self.InitUI()
        self.SetSize((750, 600))
#        self.Centre()
        self.Show(True)

    def InitUI(self):
        framePanel = maskingPanel(self, wx.ID_ANY)


            
    def OnMessage(self, on, msg):
        if not on:
            msg = ""
        self.SetStatusText(msg)


def main():
    app = wx.App(redirect=False)
    dsFrame = maskingFrame(None, wx.ID_ANY, 'Data Masking')
    app.MainLoop() 

if __name__ == '__main__':
    main()
