import wx
import ck_extern_pnl

class MyDialog(wx.Dialog):
    def __init__(self, parent, id, title):
        wx.Dialog.__init__(self, parent, id, title)
        self.InitUI()
        self.SetSize((250, 200))
        self.SetTitle("Changed Title") # overrides title passed above

    def InitUI(self):
        pnl = ck_extern_pnl.ExternalPanel(self, wx.ID_ANY)
   
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
