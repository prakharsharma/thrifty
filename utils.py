#!/usr/bin/python

import sys
import time
import hashlib
import random

class LogicalError(Exception): pass

def allOrNone(i): return ((i is None or len(str(i)) == 0) and [None]
        or [i])[0]

def nullForNone(i): return ((allOrNone(i) is None) and ['NULL'] or
        [allOrNone(i)])[0]

def joinOrNone(l, delim = ","): return ((l is None or len(l) == 0) and
        [None] or
        [delim.join([str(x) for x in l])])[0]

def dbgMsg(msg, dbgLevel, dbgThreshold, _func = "", _line = 0
        , _file = ""):
    if dbgLevel >= dbgThreshold:
        print "[File:%s, Func:%s, line:%d] %s" % (_file, _func, _line
                , msg)

def dateFromTimestamp(timestamp, miliSecs = True, style = 'yyyymmdd'):
    t = timestamp
    if miliSecs == True:
        t = int(t/1000)
    if style == 'mm/dd/yyyy' or style == 'MM/DD/YYYY':
        return time.strftime("%m/%d/%Y", time.localtime(t))
    if style == 'dd/mm/yyyy' or style == 'DD/MM/YYYY':
        return time.strftime("%d/%m/%Y", time.localtime(t))
    else:
        return time.strftime("%Y%m%d", time.localtime(t))

def timestampFromDate(date, miliSecs = True):
    if (len(date) != 8):
        raise LogicalError("Length of date should be 6")
    if miliSecs == True:
        return int(time.mktime((int(date[:4]), int(date[4:6]),
                        int(date[6:8]),
                0, 0, 0, 0, 0, 0)) * 1000)
    else:
        return int(time.mktime((int(date[:4]), int(date[4:6]),
                        int(date[6:8]),
                0, 0, 0, 0, 0, 0)))

def timestamp(miliSecs = True):
    if miliSecs:
        return int(time.time() * 1000)
    else:
        return int(time.time());

def printDict(d = {}, name = None):
    if name is None:
        return
    print "%s = {" % name
    for k, v in d.items():
        print "\t%s => %s" % (k, v)
    print "}"

def genIdentifier(keys, algo = "sha256"):
    msg = "".join(keys)
    if algo == "sha256":
        m = hashlib.sha256()
        m.update(msg)
        s = "%s" % m.hexdigest()
        a = long(s[:16], 16)
        b = long(s[16:32], 16)
        c = long(s[32:48], 16)
        d = long(s[48:], 16)
        return a ^ b ^ c ^ d
    elif algo == "md5":
        m = hashlib.md5()
        m.update(msg)
        s = "%s" % m.hexdigest()
        a = long(s[:16], 16)
        b = long(s[16:], 16)
        return a ^ b
    else:
        return None

def genRandom():
    return random.randrange(-sys.maxint - 1, sys.maxint)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: %s <email>\n" % sys.argv[0])
        sys.exit(1)
    print "timestamp(miliSecs = True) = %s" % timestamp()
    print "timestamp(miliSecs = False) = %s" % timestamp(False)
    print "random = %d" % genRandom()
    print "id = %d" % genIdentifier(["%d" % genRandom(),
            sys.argv[1], "%d" % timestamp()])
    print "Date = %s" % dateFromTimestamp(timestamp())
    print "timestamp = %d" % timestampFromDate(
            dateFromTimestamp(timestamp()))
    print "timestamp = %d" % timestampFromDate(
            dateFromTimestamp(timestamp()), False)
