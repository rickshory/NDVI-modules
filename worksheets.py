import wx, sqlite3, datetime
import os, sys, re, cPickle
import scidb
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin

# ----------------------------------------------------------------------
# customized for drag/drop from list of Stations
# DragStationList
class DragStationList(wx.ListCtrl, ListCtrlAutoWidthMixin):
    def __init__(self, *arg, **kw):
        wx.ListCtrl.__init__(self, *arg, **kw)
        ListCtrlAutoWidthMixin.__init__(self) # rightmost column will fill the rest of the list
        self.Bind(wx.EVT_LIST_BEGIN_DRAG, self._startDrag)


    def _startDrag(self, e):
        """ Put together a data object for drag-and-drop _from_ this list. """
        l = ['Station']
        # mostly need the ItemData, which is the record ID in the Stations table
        idx = self.GetFirstSelected()
        l.append(self.GetItemData(idx))
        # as a convenience, pass the list row text 
        l.append(self.GetItemText(idx))
        # and the ChannelSegment list column to put it in
        l.append(0)

        # Pickle the object
        itemdata = cPickle.dumps(l, 1)
        # create our own data format and use it in a
        # custom data object
        ldata = wx.CustomDataObject("RecIDandTable")
        ldata.SetData(itemdata)
        # Now make a data object for the  item list.
        data = wx.DataObjectComposite()
        data.Add(ldata)

        # Create drop source and begin drag-and-drop.
        dropSource = wx.DropSource(self)
        dropSource.SetData(data)
        res = dropSource.DoDragDrop(flags=wx.Drag_DefaultMove)

        # If move, we could remove the item from this list.
        if res == wx.DragMove:
            pass # disable removing, we only want to assign its info to the other list


# ----------------------------------------------------------------------
# customized for drag/drop from list of Series
# DragSeriesList
class DragSeriesList(wx.ListCtrl, ListCtrlAutoWidthMixin):
    def __init__(self, *arg, **kw):
        wx.ListCtrl.__init__(self, *arg, **kw)
        ListCtrlAutoWidthMixin.__init__(self) # rightmost column will fill the rest of the list
        self.Bind(wx.EVT_LIST_BEGIN_DRAG, self._startDrag)

    def _startDrag(self, e):
        """ Put together a data object for drag-and-drop _from_ this list. """
        l = ['Series']
        # mostly need the ItemData, which is the record ID in the DataSeries table
        idx = self.GetFirstSelected()
        l.append(self.GetItemData(idx))
        # as a convenience, pass the list row text 
        l.append(self.GetItemText(idx))
        # and the ChannelSegment list column to put it in
        l.append(1)

        # Pickle the object
        itemdata = cPickle.dumps(l, 1)
        # create our own data format and use it in a
        # custom data object
        ldata = wx.CustomDataObject("RecIDandTable")
        ldata.SetData(itemdata)
        # Now make a data object for the  item list.
        data = wx.DataObjectComposite()
        data.Add(ldata)

        # Create drop source and begin drag-and-drop.
        dropSource = wx.DropSource(self)
        dropSource.SetData(data)
        res = dropSource.DoDragDrop(flags=wx.Drag_DefaultMove)

        # If move, we could remove the item from this list.
        if res == wx.DragMove:
            pass # disable removing, we only want to assign its info to the other list

# customized for drag/drop from list of ChannelSegments
# drag-TO is implemented, drag-FROM is disabled
# DragChannelSegmentList
class DragChannelSegmentList(wx.ListCtrl, ListCtrlAutoWidthMixin):
    def __init__(self, *arg, **kw):
        wx.ListCtrl.__init__(self, *arg, **kw)
        ListCtrlAutoWidthMixin.__init__(self)
        self.setResizeColumn(3) # Channel column will take up any extra spaces

        dt = ListChannelSegmentDrop(self)
        self.SetDropTarget(dt)

    def _insert(self, x, y, lObj):
        """ Target the drop to given x, y coordinates --- used with drag-and-drop. """

        # Find insertion point.
        index, flags = self.HitTest((x, y))
        print "index from HitTest", index
        print "flag from HitTest", flags

        if index != wx.NOT_FOUND: # clicked on an item
            ChanSegID = self.GetItemData(index)
            stSQL = "UPDATE ChannelSegments SET " + lObj[0] + "ID = ? WHERE ID = ?;"
#            if lObj[0] == 'Station':
#                stSQL = "UPDATE ChannelSegments SET StationID = ? WHERE ID = ?;"
#            if lObj[0] == 'Series':
#                stSQL = "UPDATE ChannelSegments SET SeriesID = ? WHERE ID = ?;"
            scidb.curD.execute(stSQL, (lObj[1], ChanSegID))
            # on the next load, this change will show in the ChannelSegments list
            # but for now just patch in the string
            self.SetStringItem(index, lObj[3], lObj[2])

#   maybe refresh entire list, but following formats are not quite right
#            self.parent.fillChannelSegmentsList()
#            framePanel.fillChannelSegmentsList()


# customized for drop to a list of ChannelSegments
# -----
# ListChannelSegmentDrop

class ListChannelSegmentDrop(wx.PyDropTarget):
    """ Drop target for Channel Segments list.
        Allows dropping Station/Series onto ChannelSegment to assign those handles
    """

    def __init__(self, source):
        """ Arguments:
         - source: source listctrl.
        """
        wx.PyDropTarget.__init__(self)

        self.dv = source

        # specify the type of data we will accept
        self.data = wx.CustomDataObject("RecIDandTable")
        self.SetDataObject(self.data)

    # Called when OnDrop returns True.  We need to get the data and
    # do something with it.
    def OnData(self, x, y, d):
        # copy the data from the drag source to our data object
        if self.GetData():
            # convert it back to a list and give it to the viewer
            ldata = self.data.GetData()
            l = cPickle.loads(ldata)
            self.dv._insert(x, y, l)

        # what is returned signals the source what to do
        # with the original data (move, copy, etc.)  In this
        # case we just return the suggested value given to us.
        return d



class SetupWorksheetsPanel(wx.Panel):
    def __init__(self, parent, id):
        wx.Panel.__init__(self, parent, id)
        self.InitUI()

    def InitUI(self):
        #horizontal mean where the split goes across
        #vertical means the split goes up and down
        hSplit = wx.SplitterWindow(self, -1)
        setupPanel = wx.Panel(hSplit, -1)
#        wx.StaticText(setupPanel, -1, "This will be where you set up the datset columns.")
        vSplit = wx.SplitterWindow(setupPanel, -1)
        treeViewPanel = wx.Panel(vSplit, -1)
        wx.StaticText(treeViewPanel, -1, "This is where you'll see the tree view of datasets")
        detailsPanel = wx.Panel(vSplit, -1)
        wx.StaticText(detailsPanel, -1, "This will have the details")
        vSplit.SplitVertically(treeViewPanel, detailsPanel)
        hSiz = wx.BoxSizer(wx.HORIZONTAL)
        hSiz.Add(vSplit, 1, wx.EXPAND)
        setupPanel.SetSizer(hSiz)
        
        previewPanel = wx.Panel(hSplit, -1)
        wx.StaticText(previewPanel, -1, "This will be where you preview the dataset as a grid.")
        hSplit.SplitHorizontally(setupPanel, previewPanel)

        vSiz = wx.BoxSizer(wx.VERTICAL)
        vSiz.Add(hSplit, 1, wx.EXPAND)
        self.SetSizer(vSiz)


    def fillStationsList(self):
        self.lstStations.DeleteAllItems()
        scidb.curD.execute("SELECT ID, StationName FROM Stations;")
        recs = scidb.curD.fetchall()
        for rec in recs:
            idx = self.lstStations.InsertStringItem(sys.maxint, rec["StationName"])
            self.lstStations.SetItemData(idx, rec["ID"])

    def fillSeriesList(self):
        self.lstSeries.DeleteAllItems()
        scidb.curD.execute("SELECT ID, DataSeriesDescription FROM DataSeries;")
        recs = scidb.curD.fetchall()
        for rec in recs:
            idx = self.lstSeries.InsertStringItem(sys.maxint, rec["DataSeriesDescription"])
            self.lstSeries.SetItemData(idx, rec["ID"])

    def fillChannelSegmentsList(self):
        self.lstChanSegs.DeleteAllItems()
        stSQL = """
        SELECT ChannelSegments.ID,
        COALESCE(Stations.StationName, '(none)') AS Station,
        COALESCE( DataSeries.DataSeriesDescription, '(none)') AS Series,
        DataChannels.Column || ', ' || Loggers.LoggerSerialNumber || ', ' ||
        Sensors.SensorSerialNumber || ', ' || DataTypes.TypeText || ', ' ||
        DataUnits.UnitsText || ', ' || DataChannels.UTC_Offset AS Channel,
        COALESCE(ChannelSegments.SegmentBegin, '(open)') AS Begin,
        COALESCE(ChannelSegments.SegmentEnd, '(open)') AS End
        FROM ((((((ChannelSegments
        LEFT JOIN Stations ON ChannelSegments.StationID = Stations.ID)
        LEFT JOIN DataSeries ON ChannelSegments.SeriesID = DataSeries.ID)
        LEFT JOIN DataChannels ON ChannelSegments.ChannelID = DataChannels.ID)
        LEFT JOIN Loggers ON DataChannels.LoggerID = Loggers.ID)
        LEFT JOIN Sensors ON DataChannels.SensorID = Sensors.ID)
        LEFT JOIN DataTypes ON DataChannels.DataTypeID = DataTypes.ID)
        LEFT JOIN DataUnits ON DataChannels.DataUnitsID = DataUnits.ID;
        """
        scidb.curD.execute(stSQL)
        recs = scidb.curD.fetchall()
        for rec in recs:
            idx = self.lstChanSegs.InsertStringItem(sys.maxint, rec["Station"])
            self.lstChanSegs.SetItemData(idx, rec["ID"])
            self.lstChanSegs.SetStringItem(idx, 1, rec["Series"])
            self.lstChanSegs.SetStringItem(idx, 2, rec["Channel"])
            self.lstChanSegs.SetStringItem(idx, 3, rec["Begin"])
            self.lstChanSegs.SetStringItem(idx, 4, rec["End"])
            
    def onButton(self, event, strLabel):
        """"""
        print ' You clicked the button labeled "%s"' % strLabel

    def onClick_BtnAddStation(self, event, strLabel):
        """
        """
        dlg = wx.TextEntryDialog(None, "Name of Station you are adding to the database:", "New Station", " ")
        answer = dlg.ShowModal()
        if answer == wx.ID_OK:
            stNewStation = dlg.GetValue()
            stNewStation = " ".join(stNewStation.split())
            recID = scidb.assureItemIsInTableField(stNewStation, "Stations", "StationName")
            self.fillStationsList()
        else:
            stNewStation = ''
        dlg.Destroy()
        
    def onClick_BtnAddSeries(self, event, strLabel):
        """
        """
        dlg = wx.TextEntryDialog(None, "Name of Data Series you are adding to the database:", "New Data Series", " ")
        answer = dlg.ShowModal()
        if answer == wx.ID_OK:
            stNewSeries = dlg.GetValue()
            stNewSeries = " ".join(stNewSeries.split())
            recID = scidb.assureItemIsInTableField(stNewSeries, "DataSeries", "DataSeriesDescription")
            self.fillSeriesList()
        else:
            stNewSeries = ''
        dlg.Destroy()

#    def onClick_BtnNotWorkingYet(self, event, strLabel):
#        wx.MessageBox('"Hello" is not implemented yet', 'Info', 
#            wx.OK | wx.ICON_INFORMATION)

class SetupWorksheetsFrame(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title)
        self.InitUI()
        self.SetSize((750, 600))
#        self.Centre()
        self.Show(True)

    def InitUI(self):
        framePanel = SetupWorksheetsPanel(self, wx.ID_ANY)

def main():
    app = wx.App(redirect=False)
    SetupWorksheetsFrame(None, wx.ID_ANY, 'Set Up Worksheets')
    app.MainLoop() 

if __name__ == '__main__':
    main()
