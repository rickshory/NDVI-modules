import wx, sqlite3, datetime
import os, sys, re, cPickle
import scidb

menu_titles = [ "Open",
                "Properties",
                "Rename",
                "Delete" ]

menu_title_by_id = {}
#for title in menu_titles:
for id in range(len(menu_titles)):
    menu_title_by_id[ id + 101 ] = menu_titles[id]

class dTreeCtrl(wx.TreeCtrl): 
    def __init__(self, *args, **kargs): 
        wx.TreeCtrl.__init__(self, *args, **kargs) 
        self.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouseEvent) 
    
    def OnMouseEvent(self, event): 
        if event.LeftDown() and not self.HasFlag(wx.TR_MULTIPLE): 
            ht_item, ht_flags = self.HitTest(event.GetPosition())
            print "LeftDown HitTest Item:", ht_item, "Flags:", ht_flags
            if (ht_flags & wx.TREE_HITTEST_ONITEM) != 0: 
                self.SetFocus() 
                self.SelectItem(ht_item) 
            else: 
                event.Skip() 
        elif event.LeftUp(): 
            ht_item, ht_flags = self.HitTest(event.GetPosition())
            print "LeftUp HitTest Item:", ht_item, "Flags:", ht_flags
            if (ht_flags & wx.TREE_HITTEST_ONITEM) != 0: 
                print "OnMouseEvent -> LeftUp"
#                ItemData = ht_item.GetItemData()
                print "Dir ht_item:", dir(ht_item)
                print "ht_item.m_pItem:", ht_item.m_pItem
        else: 
            event.Skip() 

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

#        # a combobox for tasks for the tree items
#        self.tTaskList = ['Add', 'Delete']
#        self.lblTaskList = wx.StaticText(self, label="Task")
#        self.trTaskCbx = wx.ComboBox(self, size=(95, -1), choices=self.tTaskList, style=wx.CB_DROPDOWN)
#         self.Bind(wx.EVT_COMBOBOX, self.EvtComboBox, self.trTaskCbx)
#         self.Bind(wx.EVT_TEXT, self.EvtText,self.trTaskCbx)
#        wx.StaticText(treeViewPanel, -1, "This is where you'll see the tree view of datasets")
        self.dsTree = wx.TreeCtrl(treeViewPanel, 1, wx.DefaultPosition, (-1,-1), wx.TR_HAS_BUTTONS|wx.TR_LINES_AT_ROOT)
#        self.dsTree = dTreeCtrl(treeViewPanel, 1, wx.DefaultPosition, (-1,-1), wx.TR_HAS_BUTTONS|wx.TR_LINES_AT_ROOT)
        dsRoot = self.dsTree.AddRoot('DataSets')
        ### 1. Register source's EVT_s to invoke launcher. ###
#        wx.EVT_TREE_ITEM_ACTIVATED(self.dsTree, -1, self.dsTreeLeftClick)
        wx.EVT_TREE_ITEM_RIGHT_CLICK(self.dsTree, -1, self.dsTreeRightClick)
        self.dsTree.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged, id=1)
        self.tree_item_clicked = None

        trPnlSiz = wx.BoxSizer(wx.VERTICAL)
#        trPnlSiz.Add(self.lblTaskList)
#        trPnlSiz.Add(self.trTaskCbx)
        trPnlSiz.Add(self.dsTree, 1, wx.EXPAND)
        treeViewPanel.SetSizer(trPnlSiz)

        detailsPanel = wx.Panel(vSplit, -1)
        self.detailsLabel = wx.StaticText(detailsPanel, -1, "This will have the details")
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

    def OnSelChanged(self, event):
        print "OnSelChanged"
        item = event.GetItem()
        self.detailsLabel.SetLabel(self.dsTree.GetItemText(item))


    def dsTreeLeftClick(self, event):
        print "Item left clicked"
        item = event.GetItem()
        self.detailsLabel.SetLabel(self.dsTree.GetItemText(item))


    def dsTreeRightClick(self, event):
        self.tree_item_clicked = right_click_context = event.GetItem()
#        print "Item:", self.tree_item_clicked
#        print "Dir:", dir(self.tree_item_clicked)
#        print "Dir dict:", dir(self.tree_item_clicked.__dict__)
#        label = event.GetLabel()
#        print "Label:", label
        keycode = event.GetKeyCode()
        print "KeyCode:", keycode
        point =  event.GetPoint()
        print "Point:", point
        menu = wx.Menu()
        for (id,title) in menu_title_by_id.items():
        
#        for title in menu_titles:
#        for id in range(len(menu_titles)):
            
            ### 3. Launcher packs menu with Append. ###
#            id = wx.NewID()
            print id, title
            menu.Append( id, title )
            ### 4. Launcher registers menu handlers with EVT_MENU, on the menu. ###
            wx.EVT_MENU( menu, id, self.MenuSelectionCb )

        ### 5. Launcher displays menu with call to PopupMenu, invoked on the source component, passing event's GetPoint. ###
        self.PopupMenu( menu, event.GetPoint() )
        menu.Destroy() # destroy to avoid mem leak

    def MenuSelectionCb( self, event ):
        # do something
        operation = menu_title_by_id[ event.GetId() ]
        print "operation:", operation
#        target = self.tree_item_clicked
        target = self.dsTree.GetItemText(self.tree_item_clicked)
        print "target:", target
        print 'Perform "%(operation)s" on "%(target)s."' % vars()
        
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
