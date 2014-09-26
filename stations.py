import wx, sqlite3, datetime
import os, sys, re, cPickle
import scidb
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin
import wx.lib.scrolledpanel as scrolled, wx.grid

ID_NEW_STATION_BTN = wx.NewId()
ID_EDIT_STATION_BTN = wx.NewId()

class Dialog_StationDetails(wx.Dialog):
    def __init__(self, parent, id, title = "Add or Edit Station Details", actionCode = ['New', 0]):
        wx.Dialog.__init__(self, parent, id)
        self.InitUI(actionCode)
        self.SetSize((350, 300))
        self.SetTitle("Add or Edit Station Details") # overrides title passed above

    def InitUI(self, actionCode):
#        pnl = InfoPanel_StationDetails(self, wx.ID_ANY)
        self.pnl = InfoPanel_StationDetails(self, actionCode)
   
    def OnClose(self, event):
        self.Destroy()

class InfoPanel_StationDetails(scrolled.ScrolledPanel):
    def __init__(self, parent, actionCode):
        scrolled.ScrolledPanel.__init__(self, parent, -1)
#    def __init__(self, parent, id):
#        wx.Panel.__init__(self, parent, id)
        self.InitUI(actionCode)
        
    def InitUI(self, actionCode):
        
        print "Initializing StationDetails frame"
        if actionCode[0] == 'New': # create a new Station record
            self.StDict = scidb.dictFromTableDefaults('Stations')
            print 'new default self.StDict:', self.StDict
            self.stStaLabel = 'Name of Station you are adding to the database'
        else: # editing an existing record
            self.StDict = scidb.dictFromTableID('Stations', actionCode[1])
            print 'self.StDict loaded from table:', self.StDict
            self.stStaLabel = 'Station'

        print "Initializing Panel_StationDetails ->>>>"

        print "actionCode:", actionCode
        self.LayoutPanel()
        self.FillPanelFromDict()
        

    def LayoutPanel(self):
        self.SetBackgroundColour(wx.WHITE) # this overrides color of enclosing panel
        shPnlSiz = wx.GridBagSizer(1, 1)

        gRow = 0
        shPnlSiz.Add(wx.StaticText(self, -1, self.stStaLabel),
            pos=(gRow, 0), span=(1, 3), flag=wx.ALIGN_LEFT|wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
 
#        gRow += 1
#        shPnlSiz.Add(wx.StaticLine(self), pos=(gRow, 0), span=(1, 3), flag=wx.EXPAND)
        
        gRow += 1
        self.tcStationName = wx.TextCtrl(self)
        shPnlSiz.Add(self.tcStationName, pos=(gRow, 0), span=(1, 3), 
            flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)

        gRow += 1
        shPnlSiz.Add(wx.StaticText(self, -1, 'Processing requires longitude to calculate'),
            pos=(gRow, 0), span=(1, 3), flag=wx.LEFT|wx.TOP, border=5)
        gRow += 1
        shPnlSiz.Add(wx.StaticText(self, -1, 'solar time (latitude is unused). Choose Site'),
            pos=(gRow, 0), span=(1, 3), flag=wx.LEFT, border=5)
        gRow += 1
        shPnlSiz.Add(wx.StaticText(self, -1, 'or enter number(s) for each station.'),
            pos=(gRow, 0), span=(1, 3), flag=wx.LEFT|wx.BOTTOM, border=5)

        gRow += 1
        shPnlSiz.Add(wx.StaticText(self, -1, 'Site'),
            pos=(gRow, 0), span=(1, 1), flag=wx.ALIGN_RIGHT|wx.LEFT|wx.BOTTOM, border=5)
        self.cbxFldSites = wx.ComboBox(self, -1, style=wx.CB_READONLY)
        stSQLFieldSites = 'SELECT ID, SiteName FROM FieldSites'
        scidb.fillComboboxFromSQL(self.cbxFldSites, stSQLFieldSites)
        shPnlSiz.Add(self.cbxFldSites, pos=(gRow, 1), span=(1, 1), 
            flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)

        btnAddSite = wx.Button(self, label="New", size=(32, 20))
        btnAddSite.Bind(wx.EVT_BUTTON, lambda evt, str=btnAddSite.GetLabel(): self.onClick_BtnAddSite(evt, str))
        shPnlSiz.Add(btnAddSite, pos=(gRow, 2), flag=wx.ALIGN_LEFT|wx.LEFT, border=5)

        gRow += 1
        shPnlSiz.Add(wx.StaticText(self, -1, 'You only need to enter Station latitude and longitude if'),
            pos=(gRow, 0), span=(1, 3), flag=wx.LEFT|wx.TOP, border=5)
        gRow += 1
        shPnlSiz.Add(wx.StaticText(self, -1, 'you want to override the Site latitude and longitude.'),
            pos=(gRow, 0), span=(1, 3), flag=wx.LEFT|wx.BOTTOM, border=5)

        gRow += 1
        shPnlSiz.Add(wx.StaticText(self, -1, 'Latitude'),
            pos=(gRow, 0), span=(1, 1), flag=wx.ALIGN_RIGHT|wx.LEFT|wx.BOTTOM, border=5)
        self.tcLat = wx.TextCtrl(self)
        shPnlSiz.Add(self.tcLat, pos=(gRow, 1), span=(1, 2), 
            flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)

        gRow += 1
        shPnlSiz.Add(wx.StaticText(self, -1, 'Longitude'),
            pos=(gRow, 0), span=(1, 1), flag=wx.ALIGN_RIGHT|wx.LEFT|wx.BOTTOM, border=5)
        self.tcLon = wx.TextCtrl(self)
        shPnlSiz.Add(self.tcLon, pos=(gRow, 1), span=(1, 2), 
            flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)

        gRow += 1
        self.btnSave = wx.Button(self, label="Save", size=(90, 28))
        self.btnSave.Bind(wx.EVT_BUTTON, lambda evt: self.onClick_BtnSave(evt))
        shPnlSiz.Add(self.btnSave, pos=(gRow, 0), flag=wx.LEFT|wx.BOTTOM, border=5)
        self.btnCancel = wx.Button(self, label="Cancel", size=(90, 28))
        self.btnCancel.Bind(wx.EVT_BUTTON, lambda evt: self.onClick_BtnCancel(evt))
        shPnlSiz.Add(self.btnCancel, pos=(gRow, 1), flag=wx.LEFT|wx.BOTTOM, border=5)

        self.SetSizer(shPnlSiz)
        self.SetAutoLayout(1)
        self.SetupScrolling()

    def FillPanelFromDict(self):
        if self.StDict['StationName'] != None:
            self.tcStationName.SetValue(self.StDict['StationName'])
        scidb.setComboboxToClientData(self.cbxFldSites, self.StDict['SiteID'])
        if self.StDict['LatitudeDecDegrees'] != None:
            self.tcLat.SetValue('%.6f' % self.StDict['LatitudeDecDegrees'])
        if self.StDict['LongitudeDecDegrees'] != None:
            self.tcLon.SetValue('%.6f' % self.StDict['LongitudeDecDegrees'])

    def FillDictFromPanel(self):
        # clean up whitespace; remove leading/trailing & multiples
        self.StDict['StationName'] = " ".join(self.tcStationName.GetValue().split())
        self.StDict['SiteID'] = scidb.getComboboxIndex(self.cbxFldSites)
        try:
            self.StDict['LatitudeDecDegrees'] = float(self.tcLat.GetValue())
        except:
            self.StDict['LatitudeDecDegrees'] = None
        try:
            self.StDict['LongitudeDecDegrees'] = float(self.tcLon.GetValue())
        except:
            self.StDict['LongitudeDecDegrees'] = None

    def onClick_BtnAddSite(self, event, str):
        wx.MessageBox('"Add Site" button clicked', 'Verify',
            wx.OK | wx.ICON_INFORMATION)


    def onClick_BtnSave(self, event):
        """
        If actionCode[0] = 'New', the StationDetails is being created.
        Attempt to create a new record and make the new record ID available.
        If actionCode[0] = 'Edit', attempt to save any changes to the existing DB record
        """
        self.FillDictFromPanel() # get all values before testing
        # verify
        stStationName = self.StDict['StationName']
        print "stStationName:", stStationName
        if stStationName == '':
            wx.MessageBox('Need Station Name', 'Missing',
                wx.OK | wx.ICON_INFORMATION)
            self.tcStationName.SetValue(stStationName)
            self.tcStationName.SetFocus()
            self.Scroll(0, 0) # the required controls are all at the top
            return
    
        maxLen = scidb.lenOfVarcharTableField('Stations', 'StationName')
        if maxLen < 1:
            wx.MessageBox('Error %d getting [Stations].[StationName] field length.' % maxLen, 'Error',
                wx.OK | wx.ICON_INFORMATION)
            return
        if len(stStationName) > maxLen:
            wx.MessageBox('Max length for Station Name is %d characters.\n\nIf trimmed version is acceptable, retry.' % maxLen, 'Invalid',
                wx.OK | wx.ICON_INFORMATION)
            self.tcStationName.SetValue(stStationName[:(maxLen)])
            self.tcStationName.SetFocus()
            self.Scroll(0, 0) # the required controls are all at the top
            return    
        recID = scidb.dictIntoTable_InsertOrReplace('Stations', self.StDict)
        parObject = self.GetParent()
        if parObject.GetClassName() == "wxDialog":
            parObject.EndModal(0)

    def onClick_BtnCancel(self, event):
        """
        This frame is shown in a Dialog, which is its parent object.
        """
        parObject = self.GetParent()
        if parObject.GetClassName() == "wxDialog":
            parObject.EndModal(0)

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



class SetupStationsPanel(wx.Panel):
    def __init__(self, parent, id):
        wx.Panel.__init__(self, parent, id)
        self.InitUI()

    def InitUI(self):
        
        # improve this layout using wx.SplitterWindow instead

        sizerWholeFrame = wx.GridBagSizer(5, 5)

        hdr = wx.StaticText(self, label="Drag Stations and Series to assign them to Channel Segments")
        sizerWholeFrame.Add(hdr, pos=(0, 0), span=(1, 2), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)

        hLine = wx.StaticLine(self)
        sizerWholeFrame.Add(hLine, pos=(1, 0), span=(1, 3), 
            flag=wx.EXPAND|wx.BOTTOM, border=1)

        sizerSta = wx.GridBagSizer(1, 1)

        hdrStation = wx.StaticText(self, label="Stations:")
        sizerSta.Add(hdrStation, pos=(0, 0), span=(1, 1),
                     flag=wx.ALIGN_LEFT|wx.TOP|wx.LEFT, border=1)
        
        btnAddStation = wx.Button(self, label="New", size=(32, 20))
        btnAddStation.Bind(wx.EVT_BUTTON, lambda evt, str=btnAddStation.GetLabel(): self.onClick_BtnWorkOnStation(evt, str))
        sizerSta.Add(btnAddStation, pos=(0, 1), flag=wx.ALIGN_LEFT|wx.LEFT, border=10)
        
        self.lstStations = DragStationList(self, style=wx.LC_REPORT|wx.LC_NO_HEADER|wx.LC_SINGLE_SEL)
        self.lstStations.InsertColumn(0, "Station")
        self.fillStationsList()
        
        sizerSta.Add(self.lstStations, pos=(1, 0), span=(2, 2), flag=wx.EXPAND)
        sizerSta.AddGrowableRow(1)
        sizerSta.AddGrowableCol(1)

        sizerWholeFrame.Add(sizerSta, pos=(2, 0), span=(1, 1), 
            flag=wx.EXPAND)

        sizerSer = wx.GridBagSizer(1, 1)

        hdrSeries = wx.StaticText(self, label="Series:")
        sizerSer.Add(hdrSeries, pos=(0, 0), span=(1, 1),
                     flag=wx.ALIGN_LEFT|wx.TOP|wx.LEFT, border=1)
        
        btnAddSeries = wx.Button(self, label="New", size=(32, 20))
        btnAddSeries.Bind(wx.EVT_BUTTON, lambda evt, str=btnAddSeries.GetLabel(): self.onClick_BtnAddSeries(evt, str))
        sizerSer.Add(btnAddSeries, pos=(0, 1), flag=wx.ALIGN_LEFT|wx.LEFT, border=10)
        
        self.lstSeries = DragSeriesList(self, style=wx.LC_REPORT|wx.LC_NO_HEADER|wx.LC_SINGLE_SEL)
        self.lstSeries.InsertColumn(0, "Series")
        self.fillSeriesList()

        sizerSer.Add(self.lstSeries, pos=(1, 0), span=(2, 2), flag=wx.EXPAND)
        sizerSer.AddGrowableRow(1)
        sizerSer.AddGrowableCol(1)

        sizerWholeFrame.Add(sizerSer, pos=(2, 1), span=(1, 1), 
            flag=wx.EXPAND)

        sizerChanSegs = wx.GridBagSizer(1, 1)

        hdrChanSegs = wx.StaticText(self, label="Channel Segments:")
        sizerChanSegs.Add(hdrChanSegs, pos=(0, 0), span=(1, 1), flag=wx.ALIGN_LEFT|wx.TOP, border=5)

        self.lstChanSegs = DragChannelSegmentList(self, style=wx.LC_REPORT|wx.LC_VRULES|wx.LC_SINGLE_SEL)
        self.lstChanSegs.InsertColumn(0, "Station")
        self.lstChanSegs.InsertColumn(1, "Series")
        self.lstChanSegs.InsertColumn(2, "Channel Segment (Col, Logger, Sensor, Type, Units, HrOffset)")
        self.lstChanSegs.InsertColumn(3, "Start")
        self.lstChanSegs.InsertColumn(4, "End")

        self.fillChannelSegmentsList()

        sizerChanSegs.Add(self.lstChanSegs, pos=(1, 0), span=(1, 2), flag=wx.EXPAND)
        sizerChanSegs.AddGrowableRow(1)
        sizerChanSegs.AddGrowableCol(1)

        sizerWholeFrame.Add(sizerChanSegs, pos=(3, 0), span=(1, 3), 
            flag=wx.EXPAND)
       
        sizerWholeFrame.AddGrowableCol(0)
        sizerWholeFrame.AddGrowableCol(1)
        sizerWholeFrame.AddGrowableRow(3)

        self.SetSizerAndFit(sizerWholeFrame)

    def fillStationsList(self):
        scidb.fillListctrlFromSQL(self.lstStations, "SELECT ID, StationName FROM Stations;")

    def fillSeriesList(self):
        scidb.fillListctrlFromSQL(self.lstSeries, "SELECT ID, DataSeriesDescription FROM DataSeries;")

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

    def onClick_BtnWorkOnStation(self, event, strLabel):
        """
        """
        print "in onClick_BtnWorkOnStation"
        if strLabel == "New":
            dia = Dialog_StationDetails(self, wx.ID_ANY, actionCode = ['New', 0])
        elif strLabel == "Edit":
            recNum = self.lstStations.GetItemData(self.lstStations.GetFocusedItem())
            if recNum == None:
                wx.MessageBox('Select a Station to edit', 'No Selection',
                    wx.OK | wx.ICON_INFORMATION)
                return
            dia = Dialog_StationDetails(self, wx.ID_ANY, actionCode = ['Edit', recNum])
        else:
            return
        # the dialog contains an 'InfoPanel_StationDetails' named 'pnl'
        result = dia.ShowModal()
        # dialog is exited using EndModal, and comes back here
        print "Modal dialog result:", result
        # test of pulling things out of the modal dialog
        self.stationName = dia.pnl.tcStationName.GetValue()
        print "Name of new station, from the Modal:", self.stationName
        dia.Destroy()
        self.fillStationsList()
        
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

class SetupStationsFrame(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title)
        self.InitUI()
        self.SetSize((750, 600))
#        self.Centre()
        self.Show(True)

    def InitUI(self):
        framePanel = SetupStationsPanel(self, wx.ID_ANY)

def main():
    app = wx.App(redirect=False)
    SetupStationsFrame(None, wx.ID_ANY, 'Assign Stations and Series')
    app.MainLoop() 

if __name__ == '__main__':
    main()
