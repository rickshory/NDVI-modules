import wx

class ExternalPanel(wx.Panel):
    def __init__(self, parent, id):
        wx.Panel.__init__(self, parent, id)
        self.InitUI()

    def InitUI(self):
        GBSizer = wx.GridBagSizer(2, 2)
        hdr = wx.StaticText(self, label="Header")
        GBSizer.Add(hdr, pos=(0, 0), span=(1, 1), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        btnHey = wx.Button(self, label="Hey", size=(90, 28))
        btnHey.Bind(wx.EVT_BUTTON, lambda evt, str=btnHey.GetLabel(): self.onClick_BtnHey(evt, str))
        GBSizer.Add(btnHey, pos=(1, 1), flag=wx.RIGHT|wx.BOTTOM, border=5)
        self.SetSizerAndFit(GBSizer)
        
    def OnClose(self, event):
        self.Destroy()
        
    def onClick_BtnHey(self, event, strLabel):
        """"""
        wx.MessageBox('Yes, this button works from the modal frame with panel externally loaded', 'Info', 
            wx.OK | wx.ICON_INFORMATION)
