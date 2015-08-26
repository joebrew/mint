#!/usr/bin/env python
import datetime
import mintapi
import pandas as pd
import numpy as np

# Get username and password
fname = 'data/username_and_password.txt'
with open(fname) as f:
	content = [x.strip('\n') for x in f.readlines()]
email = content[0]
password = content[1]

# https://github.com/mrooney/mintapi
mint = mintapi.Mint(email, password)

# Get basic account information
accounts = mint.get_accounts()
checking = accounts[0]
savings = accounts[1]

# If account hasn't been updated today, upddate
time_since_last_update = datetime.datetime.now() - checking['lastUpdatedInDate']
if time_since_last_update.seconds > (60 * 60 * 24):
	# Initiate an account refresh
	mint.initiate_account_refresh()
	accounts = mint.get_accounts()
	checking = accounts[0]
	savings = accounts[1]

# # Get extended account detail at the expense of speed - requires an
# # additional API call for each account
# data2 = mint.get_accounts(True)

# # Get budget information
# budgets = mint.get_budgets()

# Get transactions
transactions = mint.get_transactions()
transactions = pd.DataFrame(transactions)

#####
# OUTPUT
#####

# Calculate changes over last week and month
today = datetime.datetime.today()
a_week_ago = today - datetime.timedelta(days = 6)
a_month_ago = today - datetime.timedelta(days = 30)

credits = transactions['amount'][transactions['transaction_type'] == 'credit']
debits = transactions['amount'][transactions['transaction_type'] == 'debit']

credits_last_week = int(credits[transactions['date'] >= a_week_ago].sum())
debits_last_week = int(debits[transactions['date'] >= a_week_ago].sum())

credits_last_month = int(credits[transactions['date'] >= a_month_ago].sum())
debits_last_month = int(debits[transactions['date'] >= a_month_ago].sum())

########
print '\n\n\n\n\n'
for i in range(10):
	print '.'

# WEEK
print('------------------------------------')
print 'You earned ' + str(credits_last_week) + ' dollars over the last 7 days (' + str(credits_last_week / 7) + ' per day).'
print 'You spent ' + str(debits_last_week) + ' dollars over the last 7 days (' + str(debits_last_week / 7) + ' per day).'
net_change = credits_last_week - debits_last_week
if net_change >= 0:
	direction = 'up'
else:
	direction = 'down'
print 'So, you are ' + direction + ' ' + str(abs(net_change)) + ' on the week. (' + str(net_change / 7) + ' per day).'
print('_________________\n')

# MONTH
print('------------------------------------')
print 'You have earned ' + str(credits_last_month) + ' dollars over the last 30 days (' + str(credits_last_month / 30) + ' per day).'
print 'You have spent ' + str(debits_last_month) + ' dollars over the last 30 days (' + str(debits_last_month / 30) + ' per day).'
net_change = credits_last_month - debits_last_month
if net_change >= 0:
	direction = 'up'
else:
	direction = 'down'
print 'So, you are ' + direction + ' ' + str(abs(net_change)) + ' on the month. (' + str(net_change / 30) + ' per day).'
print('_________________\n')

# Print current amount
print('------------------------------------')
print 'YOU HAVE ' + str(checking['currentBalance']) + ' DOLLARS.'
print 'At your current monthly spending rate, with no revenue at all, you would run out of money in ' + str(int(checking['currentBalance'] / (debits_last_month / 30))) + ' days.'
print('_________________\n')

