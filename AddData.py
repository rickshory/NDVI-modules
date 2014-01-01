import wx, sqlite3
import os, sys
import scidb

class DropTargetForFilesToParse(wx.FileDropTarget):
    def __init__(self, progressArea, msgArea):
        wx.FileDropTarget.__init__(self)
        self.progressArea = progressArea
        self.msgArea = msgArea

    def OnDropFiles(self, x, y, filenames):
        self.progressArea.SetInsertionPointEnd()
        self.progressArea.WriteText("\n%d file(s) dropped at %d,%d:\n" %
                              (len(filenames), x, y))

        for name in filenames:
            self.progressArea.WriteText(name + '\n')
            fileresult = self.parseFileIntoDB(name)
            self.progressArea.SetInsertionPointEnd()
            self.progressArea.WriteText(fileresult + '\n')

    def parseFileIntoDB(self, filename):
        """
        given a string which is the full path to a file
        determines the file structure and parses the
        data into the proper tables

        for initial testing, simply parses any text file into
        the temp DB, the table "Text"
        """
        try:
            file = open(filename, 'r')
            ct = 0
            stSQL = 'INSERT INTO Text(Line) VALUES (?);'
            for line in file:
    #           print line
                items = line.split('\t')
                for item in items:
                    if (ct % 10) == 0: # give some progress diagnostics
                        self.msgArea.ChangeValue("processed " +
                                str(ct) + " items")
#                        wx.Update()
                        wx.Yield()
                    
                    ct += 1
                    try:
                        scidb.curT.execute(stSQL, (item,))
                    except sqlite3.IntegrityError:
                        pass # message is: "column Line is not unique"
                        # catch these and count as duplicate lines ignored
                    except sqlite3.OperationalError:
                        pass # message is: "unrecognized token: "'HOBO..."
                        # deal with these in binary file types
                scidb.tmpConn.commit()
    #           file.close()
            return str(ct) + ' items parsed into database'
        except IOError, error:
            return 'Error opening file\n' + str(error)
        except UnicodeDecodeError, error:
             return 'Cannot open non ascii files\n' + str(error)
        

#

class ParseFiles(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size = (450, 400))
        self.InitUI()
#        self.Centre()
        self.Show(True)

    def InitUI(self):

        framePanel = wx.Panel(self)
        GBSizer = wx.GridBagSizer(5, 5)

        hdr = wx.StaticText(framePanel, label="Drag files below to add their data to the database")
        GBSizer.Add(hdr, pos=(0, 0), span=(1, 2), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)

        btnShowLog = wx.Button(framePanel, label="Show Log", size=(90, 28))
        btnShowLog.Bind(wx.EVT_BUTTON, lambda evt, str=btnShowLog.GetLabel(): self.onClick_BtnShowLog(evt, str))
#        btnShowLog.Bind(wx.EVT_BUTTON, OnBtnShowLogClick)
        GBSizer.Add(btnShowLog, pos=(0, 5), flag=wx.RIGHT|wx.BOTTOM, border=5)

        textProgress = wx.TextCtrl(framePanel, style = wx.TE_MULTILINE)
        GBSizer.Add(textProgress, pos=(1, 0), span=(4, 6),
            flag=wx.EXPAND|wx.TOP|wx.RIGHT|wx.BOTTOM, 
            border=5)

        lblProgTitle = wx.StaticText(framePanel, -1, "Progress:")
        GBSizer.Add(lblProgTitle, pos=(5, 0), span=(1, 1),
            flag=wx.EXPAND|wx.TOP|wx.RIGHT|wx.BOTTOM, 
            border=5)

        textProgMsgs = wx.TextCtrl(framePanel, style = wx.TE_MULTILINE)
        GBSizer.Add(textProgMsgs, pos=(5, 1), span=(1, 5),
            flag=wx.EXPAND|wx.TOP|wx.RIGHT|wx.BOTTOM, 
            border=5)
        
        dt = DropTargetForFilesToParse(textProgress, textProgMsgs)
        textProgress.SetDropTarget(dt)

        txtSelManual = wx.StaticText(framePanel, label="Or select file manually")
        GBSizer.Add(txtSelManual, pos=(6, 0), span=(1, 5),
            flag=wx.ALIGN_RIGHT|wx.TOP|wx.RIGHT|wx.BOTTOM, border=5)

        btnBrowse = wx.Button(framePanel, label="Browse", size=(90, 28))
        btnBrowse.Bind(wx.EVT_BUTTON, lambda evt, str=btnBrowse.GetLabel(): self.onClick_BtnBrowse(evt, str))

        GBSizer.Add(btnBrowse, pos=(6, 5), flag=wx.RIGHT|wx.BOTTOM, border=5)
       
        GBSizer.AddGrowableCol(1)
        GBSizer.AddGrowableRow(2)

        framePanel.SetSizerAndFit(GBSizer)

    def openfile(self, event):
        dlg = wx.FileDialog(self, "Choose a file", os.getcwd(), "", "*.*", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            mypath = os.path.basename(path)
            self.SetStatusText("Not implemented yet")
            #self.SetStatusText("You selected: %s" % mypath)
            dlg.Destroy()
    
    def onButton(self, event, strLabel):
        """"""
        print ' You clicked the button labeled "%s"' % strLabel

    def onClick_BtnShowLog(self, event, strLabel):
        """"""
        print ' You clicked the button labeled "%s"' % strLabel

    def onClick_BtnBrowse(self, event, strLabel):
        """"""
        print ' You clicked the button labeled "%s"' % strLabel


app = wx.App()
ParseFiles(None, -1, 'Add Data to Database')
app.MainLoop()