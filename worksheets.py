import wx, sqlite3, datetime
import os, sys, re, cPickle
import scidb

class SetupWorksheetsPanel(wx.Panel):
    def __init__(self, parent, id):
        wx.Panel.__init__(self, parent, id)
        self.InitUI()

    def InitUI(self):
        #horizontal split mean where the split goes across
        #vertical split means the split goes up and down
        hSplit = wx.SplitterWindow(self, -1)
        setupPanel = wx.Panel(hSplit, -1)
#        wx.StaticText(setupPanel, -1, "This will be where you set up the datset columns.")
        vSplit = wx.SplitterWindow(setupPanel, -1)
        treeViewPanel = wx.Panel(vSplit, -1)

        # a combobox for tasks for the tree items
        self.tTaskList = ['Add', 'Delete']
#        self.lblTaskList = wx.StaticText(self, label="Task")
        self.trTaskCbx = wx.ComboBox(self, size=(95, -1), choices=self.tTaskList, style=wx.CB_DROPDOWN)
#         self.Bind(wx.EVT_COMBOBOX, self.EvtComboBox, self.trTaskCbx)
#         self.Bind(wx.EVT_TEXT, self.EvtText,self.trTaskCbx)
#        wx.StaticText(treeViewPanel, -1, "This is where you'll see the tree view of datasets")
        self.dsTree = wx.TreeCtrl(treeViewPanel, 1, wx.DefaultPosition, (-1,-1), wx.TR_HAS_BUTTONS|wx.TR_LINES_AT_ROOT)
        dsRoot = self.dsTree.AddRoot('DataSets')
        self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)


        trPnlSiz = wx.BoxSizer(wx.VERTICAL)
#        trPnlSiz.Add(self.lblTaskList)
#        trPnlSiz.Add(self.trTaskCbx)
        trPnlSiz.Add(self.dsTree, 1, wx.EXPAND)
        treeViewPanel.SetSizer(trPnlSiz)

        detailsPanel = wx.Panel(vSplit, -1)
        wx.StaticText(detailsPanel, -1, "This will have the details")
        vSplit.SplitVertically(treeViewPanel, detailsPanel)
        hSiz = wx.BoxSizer(wx.HORIZONTAL)
        hSiz.Add(vSplit, 1, wx.EXPAND)
        setupPanel.SetSizer(hSiz)
        
        previewPanel = wx.Panel(hSplit, -1)
        wx.StaticText(previewPanel, -1, "This will be where you preview the dataset as a grid.")
        hSplit.SplitHorizontally(setupPanel, previewPanel)

        vSiz = wx.BoxSizer(wx.VERTICAL)
        vSiz.Add(hSplit, 1, wx.EXPAND)
        self.SetSizer(vSiz)

    def OnRightUp(self, event):
        index, flags = self.HitTest((x, y))
        print "index from HitTest", index
        print "flag from HitTest", flags
            
    def onButton(self, event, strLabel):
        """"""
        print ' You clicked the button labeled "%s"' % strLabel


#    def onClick_BtnNotWorkingYet(self, event, strLabel):
#        wx.MessageBox('"Hello" is not implemented yet', 'Info', 
#            wx.OK | wx.ICON_INFORMATION)

class SetupWorksheetsFrame(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title)
        self.InitUI()
        self.SetSize((750, 600))
#        self.Centre()
        self.Show(True)

    def InitUI(self):
        framePanel = SetupWorksheetsPanel(self, wx.ID_ANY)

def main():
    app = wx.App(redirect=False)
    SetupWorksheetsFrame(None, wx.ID_ANY, 'Set Up Worksheets')
    app.MainLoop() 

if __name__ == '__main__':
    main()
