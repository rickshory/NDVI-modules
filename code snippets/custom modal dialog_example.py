
import wx

class MyDialog(wx.Dialog):
    def __init__(self, parent, id, title):
        wx.Dialog.__init__(self, parent, id, title)
        self.InitUI()
        self.SetSize((250, 200))
        self.SetTitle("Changed Title") # overrides title passed above

    def InitUI(self):
        pnl = wx.Panel(self)
        GBSizer = wx.GridBagSizer(2, 2)
        hdr = wx.StaticText(pnl, label="Header")
        GBSizer.Add(hdr, pos=(0, 0), span=(1, 1), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        btnHey = wx.Button(pnl, label="Hey", size=(90, 28))
        btnHey.Bind(wx.EVT_BUTTON, lambda evt, str=btnHey.GetLabel(): self.onClick_BtnHey(evt, str))
        GBSizer.Add(btnHey, pos=(1, 1), flag=wx.RIGHT|wx.BOTTOM, border=5)
        pnl.SetSizerAndFit(GBSizer)
        

    def OnClose(self, event):
        self.Destroy()
        
    def onClick_BtnHey(self, event, strLabel):
        """"""
        wx.MessageBox('Yes, this button works from a modal frame', 'Info', 
            wx.OK | wx.ICON_INFORMATION)
        
class OuterAppFrame(wx.Frame):
    
    def __init__(self, *args, **kw):
        super(OuterAppFrame, self).__init__(*args, **kw) 
        self.InitUI()
        
    def InitUI(self):    
    
        panel = wx.Panel(self, wx.ID_ANY)
        wx.Button(panel, 1, 'Show Custom Dialog', (100,100))
        self.Bind (wx.EVT_BUTTON, self.OnShowCustomDialog, id=1)

        self.SetSize((300, 200))
        self.SetTitle('Outer App Framework')
        self.Centre()
        self.Show(True)

    def OnShowCustomDialog(self, event):
        dia = MyDialog(self, wx.ID_ANY, 'Pop-up Module')
        dia.ShowModal()
        dia.Destroy()

def main():
    
    ex = wx.App(redirect = 0) #stdio will stay at the console
    OuterAppFrame(None)
    ex.MainLoop()    


if __name__ == '__main__':
    main()
