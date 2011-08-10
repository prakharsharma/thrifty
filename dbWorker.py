#!/usr/bin/python

import ConfigParser
import sys
import MySQLdb
import utils
import json
import inspect

basePath = '/home/prakhar/devel'
appName = 'thrifty'
cfgFilePath = basePath + '/' + appName + '/getThrifty.cfg'

def parseCfgFile(_path = cfgFilePath, _dbCfg = {}, _globalCfg = {}):
    config = ConfigParser.ConfigParser()
    config.read(_path)
    for k, v in config.items('database'):
        _dbCfg[k] = v
    for k, v in config.items('global'):
        _globalCfg[k] = v
    if (int(_globalCfg['debug']) >= int(_globalCfg['debug.info'])):
        utils.printDict(_globalCfg, '_globalCfg')
        utils.printDict(_dbCfg, '_dbCfg')

class BadArgs(Exception): pass
class LogicalError(Exception): pass
class DbError(Exception): pass
class RecordNotFound(DbError): pass
class UniqueViolation(DbError): pass

class DbWorker:
    dbCfg = {}
    globalCfg = {}
    parsedCfg = False
    currFrame = None

    def parseCfg(self):
        if DbWorker.parsedCfg == False:
            parseCfgFile(_dbCfg = DbWorker.dbCfg,
                    _globalCfg = DbWorker.globalCfg)
            DbWorker.parsedCfg = True

    def __init__(self):
        self.parseCfg()
        #utils.printDict(DbWorker.dbCfg, 'dbCfg')
        self.__conn = MySQLdb.connect(host = DbWorker.dbCfg['host'],
                port = int(DbWorker.dbCfg['port']),
                db = DbWorker.dbCfg['name'],
                user = DbWorker.dbCfg['user'],
                passwd = DbWorker.dbCfg['passwd'])
        DbWorker.currFrame = inspect.currentframe()

    def __del__(self):
        self.__conn.close()

    def getUser(self, uid = None, ck = None, email = None):
        if uid is None and ck is None and email is None:
            raise BadArgs("At least one of uid, ck, and email must be" +
                    " given to getUser")
        try:
            cursor = self.__conn.cursor(MySQLdb.cursors.DictCursor)
            if uid is None and email is None:
                cursor.execute("""
                    SELECT _id, _email, _openid, _firstName, _lastName,
                    _cellPhone, _memberSince, _lastSeen, _type, _cookie
                    FROM """
                    + DbWorker.dbCfg['table.user'] + """ WHERE _cookie = %s
                    """, (ck,))
            elif ck is None and email is None:
                cursor.execute("""
                    SELECT _id, _email, _openid, _firstName, _lastName,
                    _cellPhone, _memberSince, _lastSeen, _type, _cookie
                    FROM """
                    + DbWorker.dbCfg['table.user'] + """ WHERE _id = %s
                    """ , (uid,))
            elif ck is None and uid is None:
                cursor.execute("""
                    SELECT _id, _email, _openid, _firstName, _lastName,
                    _cellPhone, _memberSince, _lastSeen, _type, _cookie
                    FROM """
                    + DbWorker.dbCfg['table.user'] + """ WHERE _email = %s
                    """ , (email,))
            else:
                cursor.execute("""
                    SELECT _id, _email, _openid, _firstName, _lastName,
                    _cellPhone, _memberSince, _lastSeen, _type, _cookie
                    FROM """
                    + DbWorker.dbCfg['table.user'] + """ WHERE _id = %s 
                    AND _cookie = %s
                    """ , (uid, ck))
            if cursor.rowcount == 0:
                raise RecordNotFound("""
                        Record not found for user in table %s with 
                        _id = %s and _cookie = %s
                        """ % (DbWorker.dbCfg['table.user'],
                        utils.nullForNone(uid), utils.nullForNone(ck)))
            if cursor.rowcount > 1:
                raise UniqueViolation("""
                        More than one record in table %s for _id = %d and
                        ck = %d 
                        """ % (DbWorker.dbCfg['table.user'],uid,ck))
            user = cursor.fetchone()
            cursor.close()
            utils.dbgMsg("User = %s" % json.dumps(user),
                    DbWorker.globalCfg['debug'],
                    DbWorker.globalCfg['debug.info'], __name__,
                    DbWorker.currFrame.f_lineno,
                    DbWorker.currFrame.f_code.co_filename)
            return user
        except:
            raise

    def userLogin(self, userId, userCookie,
            lastSeen = utils.timestamp(False),
            email = None, openid = None,
            firstName = None, lastName = None, cellPhone = None,
            memberSince = utils.timestamp(False), uType = 'manual'):
        cursor = self.__conn.cursor()
        try:
            uid = self.getUser(uid = userId, ck = userCookie)['_id']
            cursor.execute("""UPDATE """
                    + DbWorker.dbCfg['table.user'] +
                    """ 
                    SET _firstName = %s
                    , _lastName = %s
                    , _cellPhone = %s
                    , _lastSeen = %s
                    , _type = %s
                    , _cookie = %s
                     WHERE _id = %s
                    """ , (firstName, lastSeen,
                    cellPhone, lastSeen, uType, userCookie, uid))
        except RecordNotFound as e:
            cursor.execute("""
                    INSERT INTO """ + DbWorker.dbCfg['table.user'] + 
                    """ VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (userId,
                    email, openid, firstName, lastName, cellPhone,
                    memberSince, lastSeen, uType, userCookie))
        finally:
            self.__conn.commit()
            cursor.close()

    def newBill(self, userCookie, amount, category, date,
            reportedBy, reportedAt = utils.timestamp(False),
            billType = 'individual', participants = [],
            tags = [], description = None, userAmounts = [],
            emails = []):
        cursor = self.__conn.cursor()
        try:
            uid = self.getUser(ck = userCookie)['_id']
            ppl = participants
            if len(ppl) == 0:
                ppl.append(reportedBy)
            bill_id = utils.genIdentifier(["%d" % utils.genRandom(),
                    "%d" % date, "%d" % reportedBy, category])
            cursor.execute("""
            INSERT INTO """ + DbWorker.dbCfg['table.bill'] + """ 
             VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """ , (bill_id,
            amount, category,
            date, reportedAt, reportedBy, billType,
            ",".join([str(x) for x in ppl]),
            utils.joinOrNone(tags), description))
            utils.dbgMsg("Inserted %d rows to table %s" %
                    (cursor.rowcount, DbWorker.dbCfg['table.bill']),
                    DbWorker.globalCfg['debug'],
                    DbWorker.globalCfg['debug.info'], __name__,
                    DbWorker.currFrame.f_lineno,
                    DbWorker.currFrame.f_code.co_filename)
            amnts = userAmounts
            if (len(amnts) == 0):
                amnts.append(amount)
            if (len(ppl) != len(amnts) and len(ppl) != len(emails)):
                raise LogicalError("""#ppl and #amount #emails should be
                        same.
                         ppl = [%s], amnts = [%s], emails = [%s]
                        """ % (",".join(["%d" % x for x in ppl]),
                        ",".join(["%f" % x for x in amnts])),
                        ",".join(emails))
            idAmntComb = map(lambda x, y: (x, y), ppl, amnts)
            idAMntEmailComb = map(lambda (x, y), z: (x, y, z), idAmntComb,
                    emails)
            for uid, amt, email in idAMntEmailComb:
                uid = int(uid)
                amt = float(amt)
                try:
                    self.getUser(uid = uid)
                except (BadArgs, RecordNotFound):
                    tstmp = utils.timestamp(False)
                    tmpCookie = utils.genIdentifier(["%d" %
                            utils.genRandom(), "%d" % uid, "%d" %
                            tstmp])
                    self.userLogin(userId = uid,
                            userCookie = tmpCookie, lastSeen = tstmp,
                            email = email, openid = None,
                            firstName = None, lastName = None,
                            cellPhone = None, memberSince = tstmp,
                            uType = 'auto')
                cursor.execute("""
                INSERT INTO """ + DbWorker.dbCfg['table.expense'] +"""
                 VALUES(%s, %s, %s, %s, %s, %s)
                """ , (bill_id,
                uid, amt, date, category, utils.joinOrNone(tags)))
        except:
            raise
        finally:
            self.__conn.commit()
            cursor.close()

    def reportRequest(self, userCookie, startDate,
            endDate = utils.timestamp(False),
            category = None):
        try:
            uid = self.getUser(ck = userCookie)['_id']
            if uid is None:
                return
            cursor = self.__conn.cursor(MySQLdb.cursors.DictCursor)
            if category is None:
                cursor.execute("""
                SELECT _billId, _amount, _date, _category 
                FROM """ + DbWorker.dbCfg['table.expense'] + """ 
                WHERE _userId = %s AND _date >= %s 
                AND _date <= %s
                """ , (uid, startDate, endDate))
            else:
                cursor.execute("""
                SELECT _billId, _amount, _date, _category 
                FROM """ + DbWorker.dbCfg['table.expense'] + """ 
                WHERE _userId = %s AND _date >= %s 
                AND _date <= %s AND _category = %s
                """ , (uid, startDate, endDate, category))
            result = cursor.fetchall()
            expenses = [self.__transformDateInRec(row) for row in result]
            cursor.close()
            return json.dumps(expenses)
        except:
            raise

    def __transformDateInRec(self, rec):
        rec['_date'] = utils.dateFromTimestamp(rec['_date'], False,
                'mm/dd/yyyy')
        return rec

    def userIdFromCookie(self, cookie):
        user = self.getUser(ck = cookie, uid = None)
        return user['_id']

    def junk(self):
        pass

if __name__ == "__main__":
    worker = DbWorker()
    email = raw_input("Email: ")
    ck = raw_input("Cookie: ")
    email = (len(email) and [email] or [None])[0]
    ck = (len(ck) and [long(ck)] or [utils.genIdentifier([email, "%d" %
                utils.timestamp()])])[0]
    print "Cookie = %d" % ck
    uid = (email is None and [None] or [(utils.genIdentifier(
                    ["%d" % utils.genRandom(), email, "%d" %
            utils.timestamp()]))])[0]
    worker.userLogin(uid, ck, utils.timestamp(False), email,
            "xyz__nnnn", "Prakhar",
            "Sharma", "631-885-4602", utils.timestamp(False), 'manual')
    cont = raw_input("wanna report an expense (y/n): ")
    if cont == "y" or cont == "Y":
        amnt = float(raw_input("bill amount: "))
        catg = raw_input("bill category: ")
        uid = worker.userIdFromCookie(ck)
        if uid is None:
            sys.stderr.write("User for cookie %s not present" % ck)
            sys.exit(1)
        listify = lambda tags: ((tags is None or len(tags) == 0)
                and [[]] or [tags.split(",")])[0]
        tags = listify(raw_input("tags (csv list): "))
        desc = utils.allOrNone(raw_input("desc: "))
        members = listify(raw_input("participants: "))
        amounts = listify(raw_input("participants contributions: "))
        emails = listify(raw_input("emails: "))
        btype = raw_input("bill type [individual, shared, itemized]: ")
        tstmp = utils.timestamp(False)
        worker.newBill(userCookie = ck, amount = amnt, category = catg,
                date = tstmp, reportedBy = uid, reportedAt = tstmp,
                billType = btype, participants = members, tags = tags,
                description = desc, userAmounts = amounts,
                emails = emails)
    cont = raw_input("wanna see report (y/n): ")
    if cont == "y" or cont == "Y":
        date = raw_input("date (YYYYMMDD): ")
        category = utils.allOrNone(raw_input("category: "))
        print worker.reportRequest(userCookie = ck,
                startDate = utils.timestampFromDate(date, False),
                category = category)
    sys.stdout.write("Goodbye!\n")



