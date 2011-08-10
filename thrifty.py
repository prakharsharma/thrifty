#!/usr/bin/python

import web, web.webopenid
import urllib2
import json
import os
import openid.consumer.consumer
import hashlib
import utils
import expense
import dbWorker

urls = (
        '/newExpense', 'NewExpense',
        '/', 'Index'
        )
app = web.application(urls, globals());

providers = {
  'google': 'https://www.google.com/accounts/o8/id',
  'gmail': 'https://www.google.com/accounts/o8/id',
  'yahoo': 'https://me.yahoo.com'
}

basePath = '/home/prakhar/devel'
appName = 'thrifty'
loginFile = open(basePath + '/' + appName + '/index.html');
loginHtml = loginFile.read()
loginFile.close()
userFile = open(basePath + '/' + appName + '/placeholder.html')
userHtml = userFile.read()
userFile.close()
cookieBase = '__thriftyApp'
loggedInCookie = cookieBase + '.1'

def clearCookie(cookie):
    web.setcookie(cookie, '', expires = -1)

def delSession(sessionNumber):
    del web.webopenid.sessions[sessionNumber]

def logout():
    global loggedInCookie
    clearCookie(loggedInCookie)
    clearCookie('openid_identity_hash')

def getLoggedCookie(email):
    print "[DBG] email = " + email
    val = "%d" % utils.genIdentifier([email, "%d" % utils.timestamp()])
    print "[DBG] loggedInCookie value = " + val
    return val

def genUserId(email):
    uid = (email is None and [None] or [(utils.genIdentifier(
                    ["%d" % utils.genRandom(), email, "%d" %
                    utils.timestamp()]))])[0]
    print "[DBG] uid = %d" % uid
    return uid

class Index:
  sm_dbWorker = None

  def __init__(self):
        if Index.sm_dbWorker is None:
            Index.sm_dbWorker = dbWorker.DbWorker()

  def GET(self):
      print "[DBG] start of GET"
      global loggedInCookie
      try:
          print "[DBG] Testing logged in-1"
          cks = web.cookies()
          cookie = cks[loggedInCookie]
          print "[DBG] %s cookie = %s" % (loggedInCookie, cookie)
          if len(cookie):
              #TODO get actual email id from cookie
              user = Index.sm_dbWorker.getUser(ck = long(cookie))
              email = user['_email']#'prakhar.sharma@gmail.com'
              print "[DBG] Testing logged in-2"
              return userHtml % email
      except:
          try:
              print "[DBG] here-0.1"
              cookie = web.cookies().get('openid_identity_hash')
              if (len(cookie)):
                  print "[DBG] here-0.3"
                  n = web.cookies().get('openid_session_id')
                  print "[DBG] here-0.4"
                  email = web.webopenid.sessions[n]['email']
                  ck = getLoggedCookie(email)
                  web.setcookie(loggedInCookie, ck)
                  m_id = urllib2.unquote(cookie).split('?id=')[1]
                  uid = genUserId(email)
                  Index.sm_dbWorker.userLogin(userId = uid,
                          userCookie = ck,
                          lastSeen = utils.timestamp(False),
                          email = email, openid = m_id)
                  body = userHtml % email
                  delSession(n)
                  clearCookie('openid_session_id')
                  clearCookie('openid_identity_hash')
                  return body
          except:
              print "[DBG] here-1"
              try:
                  n = web.cookies().get('openid_session_id')
                  if (len(n)):
                      pass
                  print "[DBG] here-1.1"
                  return_to = web.webopenid.sessions[n]['webpy_return_to']
                  print "[DBG] return_to = " + return_to
                  c = openid.consumer.consumer.Consumer(
                      web.webopenid.sessions[n], web.webopenid.store)
                  print "[DBG] here-1.2"
                  i = web.input()
                  a = c.complete(web.input(),
                          web.ctx.home + web.ctx.fullpath)
                  print "[DBG] here-1.3"

                  if a.status.lower() == 'success':
                      web.setcookie('openid_identity_hash',
                          web.webopenid._hmac(a.identity_url) + ','
                          + a.identity_url)
                      print "[DBG] here-1.4"

                  print "[DBG] here-1.5"
                  return web.redirect(return_to)
              except:
                  print "[DBG] here-2.1"
                  return loginHtml
#
  def POST(self):
      print "[DBG] start of POST"
      try:
          cookie = web.cookies().get('openid_identity_hash')
          if (len(cookie)):
              m_id = urllib2.unquote(cookie).split('?id=')[1]
              print 'user id = ' + m_id
              web.webopenid.logout()
      except:
          i = web.input()
          email = i.email
          print "[DBG] email = " + email
          returnTo = '/'
          n = web.webopenid._random_session()
          web.webopenid.sessions[n] = {'webpy_return_to': returnTo,
              'email': email}
          c = openid.consumer.consumer.Consumer(
              web.webopenid.sessions[n], web.webopenid.store)
          a = c.begin(providers['gmail'])
          f = a.redirectURL(web.ctx.home, web.ctx.home + web.ctx.fullpath)
          print "[DBG] redirectURL = " + f
          web.setcookie('openid_session_id', n)
          return web.redirect(f)

class NewExpense:
    def __init__(self):
        self.m_worker = expense.ExpenseManager()
        pass

    def GET(self):
        pass

    def POST(self):
        cookie = web.cookies()[loggedInCookie]
        if len(cookie):
            i = web.input()
            print "[DBG] web.input() = %s" % (json.dumps(i),)
            print "[DBG] web.data() = %s" % (json.dumps(web.data()),)
            _amnt = i.amount
            _cat = i.category
            _desc = utils.allOrNone(i.description)
            _date = utils.timestampFromDate(i.date, False)
            print "[DBG] (amount, category, description, date) = (%s, %s, %s, %s)" % (_amnt, _cat, _desc, _date)
            self.m_worker.newExpense(amount = _amnt, category = _cat,
                    description = _desc, date = _date,
                    cookie = long(cookie))
        else:
            pass
        pass

    def junk(self):
        pass

# Tell web.py explicitly that it has to act as a FastCGI server
#web.wsgi.runwsgi = lambda func, addr = None: web.wsgi.runfcgi(func, addr)

if __name__ == "__main__":
    app.run()

