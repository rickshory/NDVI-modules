 NDVI-modules
======
**NDVI-modules** is part of the Greenlogger project. The main repository is **AVRGreenlogger**, which contains the code to for data recording instruments. 
 
 This is the code for generic data management. The immediate purpose is to get the season-long NDVI traces from the data loggers used in the various branches of the Greenlogger project.

 Needs are:
Persistent storage (some kind of database) because the datasets are so large, come in in various pieces and formats, and need post-processing.
Something cross-platform, and an alternative to MS Access which many potential users don't have and/or won't deal with.

 The code is in Python, heavily using the GUI package wxPython.

 The database system is SQLite.
 
 ## Contact
#### Developer/Company
* Project of: http://www.rickshory.com/
* e-mail: rickshory@gmail.com
