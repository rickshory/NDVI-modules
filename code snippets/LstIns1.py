import wx, sys

class Frame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, size=(270,150))
        self.list = wx.ListCtrl(self, -1, style=wx.LC_REPORT)

        self.list.InsertColumn(0, 'First column', width=100)
        self.list.InsertColumn(1, 'Second column', width=100)
        self.list.InsertColumn(2, 'Index', width = 50)
        self.list.InsertColumn(3, 'supplied val', width = 50)

        index = self.list.InsertStringItem(sys.maxint, "alpha 1")
        self.list.SetStringItem(index, 1, "alpha 2")
        self.list.SetStringItem(index, 2, str(index))
        self.list.SetStringItem(index, 3, str(sys.maxint))

        index = self.list.InsertStringItem(4, "beta 1")
        self.list.SetStringItem(index, 1, "beta 2")
        self.list.SetStringItem(index, 2, str(index))
        self.list.SetStringItem(index, 3, str(4))

        index = self.list.InsertStringItem(1, "gamma 1")
        self.list.SetStringItem(index, 1, "gamma 2")
        self.list.SetStringItem(index, 2, str(index))
        self.list.SetStringItem(index, 3, str(1))

        self.Show()

app = wx.App(False)
Frame()
app.MainLoop()