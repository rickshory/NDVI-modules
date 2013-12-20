import wx

class DropTargetForFilesToParse(wx.FileDropTarget):
    def __init__(self, window):
        wx.FileDropTarget.__init__(self)
        self.window = window

    def OnDropFiles(self, x, y, filenames):
        self.window.SetInsertionPointEnd()
        self.window.WriteText("\n%d file(s) dropped at %d,%d:\n" %
                              (len(filenames), x, y))

        for name in filenames:
            self.window.WriteText(name + '\n')
            try:
                file = open(name, 'r')
                text = file.read()
                self.window.WriteText(text)
                file.close()
            except IOError, error:
                dlg = wx.MessageDialog(None, 'Error opening file\n' + str(error))
                dlg.ShowModal()
            except UnicodeDecodeError, error:
                dlg = wx.MessageDialog(None, 'Cannot open non ascii files\n' + str(error))
                dlg.ShowModal()

class DropFile(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size = (450, 400))

        self.textProgress = wx.TextCtrl(self, -1, style = wx.TE_MULTILINE)
        dt = DropTargetForFilesToParse(self.textProgress)
        self.textProgress.SetDropTarget(dt)
#        self.Centre()
        self.Show(True)


app = wx.App()
DropFile(None, -1, 'AddData.py')
app.MainLoop()