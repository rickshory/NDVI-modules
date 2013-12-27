import wx, sqlite3
import scidb

class DropTargetForFilesToParse(wx.FileDropTarget):
    def __init__(self, progressArea):
        wx.FileDropTarget.__init__(self)
        self.progressArea = progressArea

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
        existingText = self.progressArea.GetValue() #remember contents
        try:
            file = open(filename, 'r')
            ct = 0
            stSQL = 'INSERT INTO Text(Line) VALUES (?);'
            for line in file:
    #           print line
                items = line.split('\t')
                for item in items:
                    if (ct % 10) == 0: # give some progress diagnostics
                        self.progressArea.ChangeValue(existingText)
                        self.progressArea.SetInsertionPointEnd()
                        self.progressArea.WriteText('\n' + "processed " +
                                str(ct) + " items" + '\n')
                    
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
        # put the progress box back the way it was
            self.progressArea.ChangeValue(existingText)    
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
        GBSizer.Add(hdr, pos=(0, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)

        btnShowLog = wx.Button(framePanel, label="Show Log", size=(90, 28))
        GBSizer.Add(btnShowLog, pos=(0, 5), flag=wx.RIGHT|wx.BOTTOM, border=5)

        textProgress = wx.TextCtrl(framePanel, style = wx.TE_MULTILINE)
        dt = DropTargetForFilesToParse(textProgress)
        textProgress.SetDropTarget(dt)
        GBSizer.Add(textProgress, pos=(1, 0), span=(4, 6),
            flag=wx.EXPAND|wx.TOP|wx.RIGHT|wx.BOTTOM, 
            border=5)

        txtSelManual = wx.StaticText(framePanel, label="Or select file manually")
        GBSizer.Add(txtSelManual, pos=(5, 0), span=(1, 5),
            flag=wx.ALIGN_RIGHT|wx.TOP|wx.RIGHT|wx.BOTTOM, border=5)

        btnBrowse = wx.Button(framePanel, label="Browse", size=(90, 28))
        GBSizer.Add(btnBrowse, pos=(5, 5), flag=wx.RIGHT|wx.BOTTOM, border=5)
       
        GBSizer.AddGrowableCol(1)
        GBSizer.AddGrowableRow(2)

        framePanel.SetSizerAndFit(GBSizer)

app = wx.App()
ParseFiles(None, -1, 'Add Data to Database')
app.MainLoop()