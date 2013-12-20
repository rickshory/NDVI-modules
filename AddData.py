import wx

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
            try:
                file = open(name, 'r')
                text = file.read()
                self.progressArea.WriteText(text)
                file.close()
            except IOError, error:
                self.progressArea.WriteText('Error opening file\n' + str(error) + '\n')
#                dlg = wx.MessageDialog(None, 'Error opening file\n' + str(error))
#                dlg.ShowModal()
            except UnicodeDecodeError, error:
                self.progressArea.WriteText('Cannot open non ascii files\n' + str(error) + '\n')                
#                dlg = wx.MessageDialog(None, 'Cannot open non ascii files\n' + str(error))
#                dlg.ShowModal()

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

        textProgress = wx.TextCtrl(framePanel, style = wx.TE_MULTILINE)
        dt = DropTargetForFilesToParse(textProgress)
        textProgress.SetDropTarget(dt)
        
        GBSizer.Add(textProgress, pos=(1, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM, 
            border=15)
        
        framePanel.SetSizerAndFit(GBSizer)

app = wx.App()
ParseFiles(None, -1, 'Add Data to Database')
app.MainLoop()