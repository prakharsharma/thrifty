#!/usr/bin/python

import json
import dbWorker
import sys
import utils

class ExpenseManager:
    def __init__(self):
        self.m_dbWorker = dbWorker.DbWorker()

    def newExpense(self, cookie, category, amount = 0.0,
            description = None, date = utils.timestamp(False),
            billType = 'individual', tags = []):
        try:
            user = self.m_dbWorker.getUser(ck = cookie)
            members = [user['_id']]
            emails = [user['_email']]
            userAmounts = [amount]
            self.m_dbWorker.newBill(userCookie = cookie, amount = amount,
                    category = category, date = date,
                    reportedBy = user['_id'],
                    reportedAt = utils.timestamp(False),
                    billType = billType, tags = tags,
                    description = description, participants = members,
                    userAmounts = userAmounts, emails = emails)
        except:
            raise
        else:
            pass
        finally:
            pass

    def junk(self):
        pass


if __name__ == "__main__":
    pass

