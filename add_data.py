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
        dctInfo = {'fullPath': filename}
        
        self.getFileInfo(dctInfo)
        print dctInfo
        if not ('dataFormat' in dctInfo):
            self.progressArea.SetInsertionPointEnd()
            self.progressArea.WriteText('Could not determine data format' + '\n')
            return "Could not determine data format"

        self.progressArea.SetInsertionPointEnd()
        self.progressArea.WriteText('Data format detected as: "' +
                                    dctInfo['dataFormat'] + '"\n')
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

    def getFileInfo(self, infoDict):
        """
        Data files have so many possible parameters, use a dictionary to track them
        Only requirement on entering this function is the dictionary has a
        member 'fullPath', which is a string that is a full file path
        """
        if (os.path.isdir(infoDict['fullPath'])):
            infoDict['fileErr'] = "Path is a directory"
            infoDict['isDir'] = True
            return
        if not os.path.exists(infoDict['fullPath']):
            infoDict['fileErr'] = "File does not exist"
            return
        if not os.path.isfile(infoDict['fullPath']):
            infoDict['fileErr'] = "Not a file"
            return
        infoDict['fileSize'] = os.path.getsize(infoDict['fullPath'])
        # splitext gives a 2-tuple of what's before and after the ext delim
        infoDict['fileExtension'] = os.path.splitext(infoDict['fullPath'])[1]
        # find first non-blank line, and keep track of which line it is
        iLineCt = 0
        iBytesSoFar = 0
        try:
            f = open(infoDict['fullPath'], 'rb')
            while True:
                iBytesSoFar = f.tell()
                sLine = f.readline()
                    
                if (sLine == ""): # empty when no more lines can be read
                    break
                iLineCt += 1
                # diagnostics
                if iLineCt == 1:
                    infoDict['firstLine'] = sLine
                # format can be determined in first few lines or not at all
                if iLineCt >= 6:
                    break
                if len(sLine.strip()) > 0: # not a blank line
                    # test if it is text file exported by Hoboware
                    # following kludges are because Onset changed output file format
                    # i.e. different bugs through various versions of Hoboware
                    # details are important to avoid glitches during actual import
                    # in 2010, header line had only "Time..."
#                    lDiagnostics.append("sLine[:14]= " + sLine[:14])
                    if iLineCt == 1 and sLine[:14] == '"#"\t"Time, GMT':
                        infoDict['dataFormat'] = "Hoboware text export"
                        infoDict['yearVersion'] = 2010
                        break
                    
                    # in 2011, header line had "Date Time...:
                    # 1st part of 1st line should be (including quotes): "#" "Date Time, GMT
#                    lDiagnostics.append("sLine[:19]= " + sLine[:19])
                    if iLineCt == 1 and sLine[:19] == '"#"\t"Date Time, GMT':
                        infoDict['dataFormat'] = "Hoboware text export"
                        infoDict['yearVersion'] = 2011
                        break
                    
                    # in version 3.5.0 (released 2013), header starts with additional characters:
                    # 1st part of 1st line after 3 junk characters
                    # should be (including quotes): "#" "Date Time, GMT
#                    lDiagnostics.append("sLine[3:22]= " + sLine[3:22])
                    if iLineCt == 1 and  (sLine[3:22] == '"#"\t"Date Time, GMT'):
                        infoDict['dataFormat'] = "Hoboware text export"
                        infoDict['yearVersion'] = 2013
                        break
                    
                    # Test for other data formats
                    
                    if iLineCt == 1 and ('PuTTY log' in sLine):
                        infoDict['dataFormat'] = "PuTTY log"
                        break

                    if ('Timestamp\tBBDn\tIRDn\tBBUp\tIRUp\tT(C)\tVbatt(mV)' in sLine):
                        infoDict['dataFormat'] = "Greenlogger text file"
                        infoDict['versionNumber'] = 13
                        # in versions <=13, header is 1st non-blank line
                        break

                    # test for iButton file
                    # look at 2nd line
                    f.seek(0)
                    sLine = f.readline()
                    iLineCt = 1 # prev verified 1st line existed
                    sLine = f.readline()
                    if (sLine == ""):
                        break
                    iLineCt += 1
                    #  1st part of 2nd line should be (including quotes): "Timezone",
#                    lDiagnostics.append("line " + str(iLineCt) + ", [:11]= " + sLine[:11])
                    if not (iLineCt == 2 and sLine[:11] == '"Timezone",'):
                        break
                    # look at 4th line, 3rd line should be blank
                    sLine = f.readline()
                    if (sLine == ""):
                        break
                    iLineCt += 1
                    sLine = f.readline()
                    if (sLine == ""):
                        break
                    iLineCt += 1
                    # 1st part of 4th line should be (including quotes): "Serial No.","
#                    lDiagnostics.append("line " + str(iLineCt) + ", [:14]= " + sLine[:14])
                    if not (iLineCt == 4 and sLine[:14] == '"Serial No.","'):
                        break
                    # look at 5th line 
                    sLine = f.readline()
                    if (sLine == ""):
                        break
                    iLineCt += 1
                    # 1st part of 5th line should be (including quotes): "Location:","
#                    lDiagnostics.append("line " + str(iLineCt) + ", [:13]= " + sLine[:13])
                    if iLineCt == 5 and sLine[:13] == '"Location:","':
                        infoDict['dataFormat'] = "iButton"
                        break


            f.close()
        except IOError, error:
            infoDict['fileErr'] = 'Error opening file\n' + str(error)
            try:
                f.close()
            except:
                pass
        except UnicodeDecodeError, error:
            infoDict['fileErr'] = 'Cannot open non ascii files\n' + str(error)
            try:
                f.close()
            except:
                pass


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
        wx.MessageBox('"Show Log" is not implemented yet', 'Info', 
            wx.OK | wx.ICON_INFORMATION)

    def onClick_BtnBrowse(self, event, strLabel):
        """"""
        wx.MessageBox('"Browse" is not implemented yet', 'Info', 
            wx.OK | wx.ICON_INFORMATION)


app = wx.App()
ParseFiles(None, -1, 'Add Data to Database')
app.MainLoop()