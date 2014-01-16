import wx
import add_data

class AddDataDialog(wx.Dialog):
    def __init__(self, parent, id, title):
        wx.Dialog.__init__(self, parent, id, title)
        self.InitUI()
        self.SetSize((450, 400))
#        self.SetTitle("Add Data to Database") # overrides title passed above

    def InitUI(self):
        pnl = add_data.ParseFilesPanel(self, wx.ID_ANY)
   
    def OnClose(self, event):
        self.Destroy()
        
        
class OuterAppFrame(wx.Frame):
    
    def __init__(self, *args, **kw):
        super(OuterAppFrame, self).__init__(*args, **kw) 
        self.InitUI()
        
    def InitUI(self):    
    
        panel = wx.Panel(self, wx.ID_ANY)
        wx.Button(panel, 1, 'Add Data to Database', (100,100))
        self.Bind (wx.EVT_BUTTON, self.OnShowAddDataDialog, id=1)

        self.SetSize((300, 200))
        self.SetTitle('Outer App Framework')
        self.Centre()
        self.Show(True)

    def OnShowAddDataDialog(self, event):
        dia = AddDataDialog(self, wx.ID_ANY, 'Add Data to Database')
        dia.ShowModal()
        dia.Destroy()

def main():
    
    ex = wx.App(redirect = 0) #stdio will stay at the console
    OuterAppFrame(None)
    ex.MainLoop()    


if __name__ == '__main__':
    main()
