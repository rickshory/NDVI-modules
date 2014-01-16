import wx, panel_test
"""
needs the file "panel_test.py" in the same folder or otherwise importable
"""

app = wx.App(False)
frame = wx.Frame(None, title="Demo with Notebook")
nb = wx.Notebook(frame)


nb.AddPage(panel_test.ExamplePanel(nb), "Absolute Positioning")
nb.AddPage(panel_test.ExamplePanel(nb), "Page Two")
nb.AddPage(panel_test.ExamplePanel(nb), "Page Three")
frame.Show()
app.MainLoop()