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

        self.textProgress = wx.TextCtrl(self, -1, style = wx.TE_MULTILINE)
        dt = DropTargetForFilesToParse(self.textProgress)
        self.textProgress.SetDropTarget(dt)
#        self.Centre()
        self.Show(True)


app = wx.App()
ParseFiles(None, -1, 'AddData.py')
app.MainLoop()