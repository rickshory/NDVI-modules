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


except sqlite3.Error, e:
    print "Error %s:" % e.args[0]
    sys.exit(1)
    # figure out how to get a message back

try:
    tmpConn = sqlite3.connect('tmp.db')
    tmpConn.execute('pragma foreign_keys=ON')
    tmpConn.execute('pragma auto_vacuum=ON')
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

def parseFileIntoDB(filename):
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
#            print line
            items = line.split()
            for i in items:
#                print(i)
                ct += 1
                stSQL = "INSERT INTO Text(Line) VALUES ('" + i + "');"
                try:
                    curT.execute(stSQL)
                except sqlite3.IntegrityError:
                    pass # message is: "column Line is not unique"
                    # catch these and count as duplicate lines ignored
                except sqlite3.OperationalError:
                    pass # message is: "unrecognized token: "'HOBO..."
                    # deal with these in binary file types
                tmpConn.commit()
#            file.close()
        return str(ct) + ' items parsed into database'
    except IOError, error:
        return 'Error opening file\n' + str(error)
    except UnicodeDecodeError, error:
         return 'Cannot open non ascii files\n' + str(error)


if __name__ == "__main__":
    pass # nothing yet
