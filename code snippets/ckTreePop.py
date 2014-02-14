import wx

class ContextMenu(object):
    def __init__(self):
        super(ContextMenu, self).__init__()
        self._menu = None
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)

    def OnContextMenu(self, event):
        if self._menu is not None:
            self._menu.Destroy()
        self._menu = wx.Menu()
        self.CreateContextMenu(self._menu)
        self.PopupMenu(self._menu)

    def CreateContextMenu(self, menu):
        raise NotImplementedError

class MyList(wx.TreeCtrl, ContextMenu):
    def __init__(self, parent, *args, **kwargs):
        super(MyList, self).__init__(parent, style=wx.TR_DEFAULT_STYLE|wx.TR_HIDE_ROOT)
        ContextMenu.__init__(self)

        self.root = self.AddRoot('')
        self.SetItemHasChildren(self.root, True)

        self.node1 = self.AppendItem(self.root, 'Node 1')
        self.node2 = self.AppendItem(self.root, 'Node 2')
        self.SetItemHasChildren(self.node2, True)
        self.node3 = self.AppendItem(self.node2, 'Node 3')

    def CreateContextMenu(self, menu):
        self._menu.Append(wx.ID_ADD)
        self._menu.Append(wx.ID_DELETE)
        self._menu.Append(wx.ID_EDIT)

class MainFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(MainFrame, self).__init__(*args, **kwargs)

        self.panel = wx.Panel(self)
        self.tree = MyList(self.panel)
        self.text = wx.TextCtrl(self.panel)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.tree, 1, wx.EXPAND)
        sizer.Add(self.text, 2, wx.EXPAND)
        self.panel.SetSizer(sizer)

        self.panel.Fit()
        self.SetInitialSize()

class App(wx.App):
    def __init__(self):
        super(App, self).__init__()
        MainFrame(None, title='Test').Show()

App().MainLoop()