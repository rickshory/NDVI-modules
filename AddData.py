import wx
import scidb

class DropTargetForFilesToParse(wx.FileDropTarget):
    def __init__(self, progressArea):
        wx.FileDropTarget.__init__(self)
        self.progressArea = progressArea

    def OnDropFiles(self, x, y, filenames):
        self.progressArea.SetInsertionPointEnd()
        self.progressArea.WriteText("\n%d file(s) dropped at %d,%d:\n" %
                              (len(filenames), x, y))

        for name in filenames:
            self.progressArea.WriteText(name + '\n')
            fileresult = scidb.parseFileIntoDB(name)
            self.progressArea.WriteText(fileresult + '\n')

class ParseFiles(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size = (450, 400))
        self.InitUI()
#        self.Centre()
        self.Show(True)

    def InitUI(self):

        framePanel = wx.Panel(self)
        GBSizer = wx.GridBagSizer(5, 5)

        hdr = wx.StaticText(framePanel, label="Drag files below to add their data to the database")
        GBSizer.Add(hdr, pos=(0, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)

        btnShowLog = wx.Button(framePanel, label="Show Log", size=(90, 28))
        GBSizer.Add(btnShowLog, pos=(0, 5), flag=wx.RIGHT|wx.BOTTOM, border=5)

        textProgress = wx.TextCtrl(framePanel, style = wx.TE_MULTILINE)
        dt = DropTargetForFilesToParse(textProgress)
        textProgress.SetDropTarget(dt)
        GBSizer.Add(textProgress, pos=(1, 0), span=(4, 6),
            flag=wx.EXPAND|wx.TOP|wx.RIGHT|wx.BOTTOM, 
            border=5)

        txtSelManual = wx.StaticText(framePanel, label="Or select file manually")
        GBSizer.Add(txtSelManual, pos=(5, 0), span=(1, 5),
            flag=wx.ALIGN_RIGHT|wx.TOP|wx.RIGHT|wx.BOTTOM, border=5)

        btnBrowse = wx.Button(framePanel, label="Browse", size=(90, 28))
        GBSizer.Add(btnBrowse, pos=(5, 5), flag=wx.RIGHT|wx.BOTTOM, border=5)
       
        GBSizer.AddGrowableCol(1)
        GBSizer.AddGrowableRow(2)

        framePanel.SetSizerAndFit(GBSizer)

app = wx.App()
ParseFiles(None, -1, 'Add Data to Database')
app.MainLoop()