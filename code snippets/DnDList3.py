import wx

# dragliststriped.py

class DragListStriped(wx.ListCtrl):
    def __init__(self, *arg, **kw):
        wx.ListCtrl.__init__(self, *arg, **kw)

        self.Bind(wx.EVT_LIST_BEGIN_DRAG, self._onDrag)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self._onSelect)
        self.Bind(wx.EVT_LEFT_UP,self._onMouseUp)
        self.Bind(wx.EVT_LEFT_DOWN, self._onMouseDown)
        self.Bind(wx.EVT_LEAVE_WINDOW, self._onLeaveWindow)
        self.Bind(wx.EVT_ENTER_WINDOW, self._onEnterWindow)
        self.Bind(wx.EVT_LIST_INSERT_ITEM, self._onInsert)
        self.Bind(wx.EVT_LIST_DELETE_ITEM, self._onDelete)

        #---------------
        # Variables
        #---------------
        self.IsInControl=True
        self.startIndex=-1
        self.dropIndex=-1
        self.IsDrag=False
        self.dragIndex=-1

    def _onLeaveWindow(self, event):
        self.IsInControl=False
        self.IsDrag=False
        event.Skip()

    def _onEnterWindow(self, event):
        self.IsInControl=True
        event.Skip()

    def _onDrag(self, event):
        self.IsDrag=True
        self.dragIndex=event.m_itemIndex
        event.Skip()
        pass

    def _onSelect(self, event):
        self.startIndex=event.m_itemIndex
        event.Skip()

    def _onMouseUp(self, event):
        # Purpose: to generate a dropIndex.
        # Process: check self.IsInControl, check self.IsDrag, HitTest, compare HitTest value
        # The mouse can end up in 5 different places:
        # Outside the Control
        # On itself
        # Above its starting point and on another item
        # Below its starting point and on another item
        # Below its starting point and not on another item

        if self.IsInControl==False:       #1. Outside the control : Do Nothing
            self.IsDrag=False
        else:                                   # In control but not a drag event : Do Nothing
            if self.IsDrag==False:
                pass
            else:                               # In control and is a drag event : Determine Location
                self.hitIndex=self.HitTest(event.GetPosition())
                self.dropIndex=self.hitIndex[0]
                # -- Drop index indicates where the drop location is; what index number
                #---------
                # Determine dropIndex and its validity
                #--------
                if self.dropIndex==self.startIndex or self.dropIndex==-1:    #2. On itself or below control : Do Nothing
                    pass
                else:
                    #----------
                    # Now that dropIndex has been established do 3 things
                    # 1. gather item data
                    # 2. delete item in list
                    # 3. insert item & it's data into the list at the new index
                    #----------
                    dropList=[]         # Drop List is the list of field values from the list control
                    thisItem=self.GetItem(self.startIndex)
                    for x in range(self.GetColumnCount()):
                        dropList.append(self.GetItem(self.startIndex,x).GetText())
                    thisItem.SetId(self.dropIndex)
                    self.DeleteItem(self.startIndex)
                    self.InsertItem(thisItem)
                    for x in range(self.GetColumnCount()):
                        self.SetStringItem(self.dropIndex,x,dropList[x])
            #------------
            # I don't know exactly why, but the mouse event MUST
            # call the stripe procedure if the control is to be successfully
            # striped. Every time it was only in the _onInsert, it failed on
            # dragging index 3 to the index 1 spot.
            #-------------
            # Furthermore, in the load button on the wxFrame that this lives in,
            # I had to call the _onStripe directly because it would occasionally fail
            # to stripe without it. You'll notice that this is present in the example stub.
            # Someone with more knowledge than I probably knows why...and how to fix it properly.
            #-------------
        self._onStripe()
        self.IsDrag=False
        event.Skip()

    def _onMouseDown(self, event):
        self.IsInControl=True
        event.Skip()

    def _onInsert(self, event):
        # Sequencing on a drop event is:
        # wx.EVT_LIST_ITEM_SELECTED
        # wx.EVT_LIST_BEGIN_DRAG
        # wx.EVT_LEFT_UP
        # wx.EVT_LIST_ITEM_SELECTED (at the new index)
        # wx.EVT_LIST_INSERT_ITEM
        #--------------------------------
        # this call to onStripe catches any addition to the list; drag or not
        self._onStripe()
        self.dragIndex=-1
        event.Skip()

    def _onDelete(self, event):
        self._onStripe()
        event.Skip()

    def _onStripe(self):
        if self.GetItemCount()>0:
            for x in range(self.GetItemCount()):
                if x % 2==0:
                    self.SetItemBackgroundColour(x,wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DLIGHT))
                else:
                    self.SetItemBackgroundColour(x,wx.WHITE)

if __name__ == "__main__":
    firstNameList = ["Ben", "Bruce", "Clark", "Dick"]
    lastNameList =  ["Grimm","Wayne", "Kent", "Grayson"]
    superNameList = ["The Thing", "Batman", "Superman", "Robin"]

    class ThisApp(wx.App):
        def OnInit(self):
            self.myFrame = wx.Frame(None, title='Drag List Striped Example')
            self.myFrame.Show(True)
            self.SetTopWindow(self.myFrame)
            return True

    myApp = ThisApp(redirect=False)
    dls = DragListStriped(myApp.myFrame, style=wx.LC_REPORT|wx.LC_SINGLE_SEL)
    dls.InsertColumn(0, "First Name")
    dls.InsertColumn(1, "Last Name")
    dls.InsertColumn(2, "Superhero Name")
    sizer = wx.BoxSizer()
    myApp.myFrame.SetSizer(sizer)
    sizer.Add(dls, proportion=1, flag=wx.EXPAND)

    for index in range(len(firstNameList)):
        dls.InsertStringItem(index, firstNameList[index])
        dls.SetStringItem(index, 1, lastNameList[index])
        dls.SetStringItem(index, 2, superNameList[index])
    myApp.myFrame.Layout()
    dls._onStripe()
    myApp.MainLoop()