import wx, sqlite3, datetime, copy, csv
import os, sys, re, cPickle, datetime
import scidb
import wx.lib.scrolledpanel as scrolled, wx.grid
import multiprocessing
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin

try:
    import win32com.client
    hasCom = True
except ImportError:
    hasCom = False

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
        
        self.previewPanel = wx.Panel(hSplit, -1)
        self.previewPanel.SetBackgroundColour('#FFFF00')
        self.pvwLabel = wx.StaticText(self.previewPanel, -1, "previews will be here")

        hSplit.SetMinimumPaneSize(20)
        hSplit.SetSashGravity(0.5)
        hSplit.SplitHorizontally(ndviOptsPanel, self.previewPanel)
        vSiz = wx.BoxSizer(wx.VERTICAL)
        vSiz.Add(hSplit, 1, wx.EXPAND)
        ndviInfoPanel.SetSizer(vSiz)

        vSplit.SetMinimumPaneSize(20)
        vSplit.SetSashGravity(0.5)
        vSplit.SplitVertically(self.ndviSetupPanel, ndviInfoPanel)
        hSiz = wx.BoxSizer(wx.HORIZONTAL)
        hSiz.Add(vSplit, 1, wx.EXPAND)
        self.SetSizer(hSiz)
        print 'dates list size:', self.datesList.GetSize()
        # following doesn't help
        print "dates list width:", self.datesList.GetSize()[0]
        optsSplit.SetSashPosition(position=self.datesList.GetSize()[0]+10, redraw=True)
        return
    

    def InitNDVISetupPanel(self, pnl):
        pnl.SetBackgroundColour(wx.WHITE)
        stpSiz = wx.GridBagSizer(1, 1)
        
        gRow = 0
        stpLabel = wx.StaticText(pnl, -1, 'Set up NDVI calculations here')
        stpSiz.Add(stpLabel, pos=(gRow, 0), span=(1, 3), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)

        gRow += 1
        stpSiz.Add(wx.StaticLine(pnl), pos=(gRow, 0), span=(1, 3), flag=wx.EXPAND)

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

        gRow += 1
        stpSiz.Add(wx.StaticText(self, -1, 'Name'),
                     pos=(gRow, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)              
        self.tcCalcName = wx.TextCtrl(self)
        if self.calcDict['CalcName'] != None:
            self.tcCalcName.SetValue('%s' % self.ColDict['CalcName'])
        stpSiz.Add(self.tcCalcName, pos=(gRow, 1), span=(1, 2), 
            flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)
        gRow += 1
        stpSiz.Add(wx.StaticLine(pnl), pos=(gRow, 0), span=(1, 3), flag=wx.EXPAND)
        gRow += 1


        pnl.SetSizer(stpSiz)
        pnl.SetAutoLayout(1)
        pnl.SetupScrolling()

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

class NDVIFrame(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title)
        self.InitUI()
        self.SetSize((750, 600))
#        self.Centre()
        self.Show(True)

    def InitUI(self):
        framePanel = NDVIPanel(self, wx.ID_ANY)

def main():
    app = wx.App(redirect=False)
    dsFrame = NDVIFrame(None, wx.ID_ANY, 'NDVI calculations')
    app.MainLoop() 

if __name__ == '__main__':
    main()
