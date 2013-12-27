import sqlite3
import sys
datConn = None
tmpConn = None

try:
    datConn = sqlite3.connect('sci_data.db')
    datConn.execute('pragma foreign_keys=ON') # enforce foreign keys
    # check that it was correctly set
    rslt = datConn.execute('pragma foreign_keys')
    # if foreign_keys is supported, should have one item that is either (1,) or (0,)
    rl = [r for r in rslt] # comprehend it as a list
    """
    # to do: fix up this error handling
    if len(rl) == 0: # foreign keys are not supported
        raise
    if rl[0] != (,1): # foreign keys supported but not set
        raise
    """
#    print rl
    
    datConn.execute('pragma auto_vacuum=ON')
    datConn.text_factory = str


except sqlite3.Error, e:
    print "Error %s:" % e.args[0]
    sys.exit(1)
    # figure out how to get a message back

try:
    tmpConn = sqlite3.connect('tmp.db')
    tmpConn.execute('pragma foreign_keys=ON')
    tmpConn.execute('pragma auto_vacuum=ON')
    tmpConn.text_factory = str
except sqlite3.Error, e:
    print "Error %s:" % e.args[0]
    sys.exit(1)
    # figure out how to get a message back

curT = tmpConn.cursor()

curT.executescript("""
    CREATE TABLE IF NOT EXISTS "Text"
    ("ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
    "Line" VARCHAR(50) NOT NULL UNIQUE);
    """)


if __name__ == "__main__":
    pass # nothing yet
