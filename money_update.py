#!/usr/bin/env python
import datetime
import mintapi
import pandas as pd
import numpy as np
import os
import itertools
import matplotlib.pyplot as plt
import matplotlib
import sys

matplotlib.style.use('ggplot')

pd.options.mode.chained_assignment = None


#####
# DATE OPTION FROM COMMAND LINE
#####
try:
    start = sys.argv[1]
except:
    start = None
try:
	end = sys.argv[2]
except:
	end = None

# Get username and password
fname = 'credentials/username_and_password.txt'
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

#####
# Get transactions
#####
transactions = mint.get_transactions()
transactions = pd.DataFrame(transactions)
# sort by date (in case not already)
transactions = transactions.sort(columns = 'date', ascending = False)

# Create column for total
transactions['total'] = list(itertools.repeat(0, len(transactions)))

# Make a "change" column
transactions['change'] = list(itertools.repeat(0, len(transactions)))

# How much now?
transactions['total'][0] = checking['currentBalance']

# How much at any given time?
for i in range(1, len(transactions)):
	val_before = transactions.ix[(i-1)]['total']
	type_before = transactions.ix[(i-1)]['transaction_type']
	change_before = transactions.ix[(i-1)]['amount']
	if type_before == 'credit':
		change_before = change_before * -1
	#transactions['total'][i] = val_before + change_now
	transactions.loc[i, 'total'] = val_before + change_before
for i in range(0, len(transactions)):
	type_now = transactions.ix[i]['transaction_type']
	if type_now == 'debit':
		transactions.loc[i, 'change'] = transactions.loc[i, 'amount'] * -1
	else:
		transactions.loc[i, 'change'] = transactions.loc[i, 'amount'] 

# Subset transactions based on start and end dates
if start:
	start = datetime.datetime.strptime(start, '%Y-%m-%d')
else:
	start = transactions['date'].min()
if end:
	end = datetime.datetime.strptime(end, '%Y-%m-%d')
else:
	end = transactions['date'].max()
transactions_subset = transactions.loc[(transactions.date >= start) & (transactions.date <= end),]

# Make a trend line
days_elapsed = (end - start).days + 1
start_point = transactions_subset.total[len(transactions_subset.total)-1]
end_point = transactions_subset.total.iloc[0]
trend_line = (end_point - start_point) / days_elapsed
transactions_subset['trend'] = list(itertools.repeat(0, len(transactions_subset)))
unique_dates = transactions_subset.date.unique()
for date in unique_dates:
	time_ago = (date - unique_dates[len(unique_dates)-1])
	days_ago = time_ago.astype('timedelta64[D]').astype(int)
	transactions_subset.trend[transactions_subset['date'] == date] = start_point + (days_ago * trend_line)

# Merge it all back together
transactions = pd.merge(left = transactions, right = transactions_subset, how = 'left')

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

credits_period = transactions_subset['amount'][transactions_subset['transaction_type'] == 'credit'].sum()
debits_period = transactions_subset['amount'][transactions_subset['transaction_type'] == 'debit'].sum()

########
print '\n\n\n\n\n'
for i in range(10):
	print '.'

# PRINT TABLE
print('------------------------------------')
print('TABLE')
temp = transactions.loc[range(30)][['date', 'total', 'change','description']]
print temp.iloc[::-1]
print('_________________\n\n')


# WEEK
print('------------------------------------')
print('WEEK')
print 'You earned ' + str(credits_last_week) + ' dollars over the last 7 days (' + str(credits_last_week / 7) + ' per day).'
print 'You spent ' + str(debits_last_week) + ' dollars over the last 7 days (' + str(debits_last_week / 7) + ' per day).'
net_change = credits_last_week - debits_last_week
if net_change >= 0:
	direction = 'up'
else:
	direction = 'down'
print 'So, you are ' + direction + ' ' + str(abs(net_change)) + ' on the week. (' + str(net_change / 7) + ' per day).'
print('_________________\n\n')

# MONTH
print('------------------------------------')
print('MONTH')
print 'You have earned ' + str(credits_last_month) + ' dollars over the last 30 days (' + str(credits_last_month / 30) + ' per day).'
print 'You have spent ' + str(debits_last_month) + ' dollars over the last 30 days (' + str(debits_last_month / 30) + ' per day).'
net_change = credits_last_month - debits_last_month
if net_change >= 0:
	direction = 'up'
else:
	direction = 'down'
print 'So, you are ' + direction + ' ' + str(abs(net_change)) + ' on the month. (' + str(net_change / 30) + ' per day).'
print('_________________\n\n')

# Print current amount
print('CURRENT STATUS')
print('------------------------------------')
print 'YOU HAVE ' + str(checking['currentBalance']) + ' DOLLARS.'
print 'At your current monthly spending rate, with no revenue at all, you would run out of money in ' + str(int(checking['currentBalance'] / (debits_last_month / 30))) + ' days.'
print('_________________\n\n')

# PERIOD
daily_spending_period = debits_period / days_elapsed
daily_income_period = credits_period / days_elapsed
daily_savings_period = trend_line # why doesn't this equal: daily_income_perio
print('------------------------------------')
print('PERIOD OVERVIEW')
print 'You have earned ' + str(credits_period) + ' dollars over the green period (' + str(round(credits_period / days_elapsed, 2)) + ' per day).'
print 'You have spent ' + str(debits_period) + ' dollars over the green period (' + str(round(debits_period / days_elapsed, 2)) + ' per day).'
print 'Your green period lifestyle cost is ' + str(round(debits_period / days_elapsed * 365.25, 2)) + ' dollars per year'
print 'Your green period income rate is ' + str(round(daily_income_period * 365.25, 2)) + ' dollars per year'
print 'Your green period savings rate is ' + str(round(daily_savings_period * 365.25, 2)) + ' dollars per year (' + str(round(daily_savings_period, 2)) + ' per day)'

#####
# MAKE TOTAL WORTH CHART
#####
plt.plot_date(transactions['date'], transactions['total'], marker=None, linestyle='--', color='r')
plt.xlabel('Date')
plt.ylabel('Dollars')
plt.title('Savings rate during green period: ' + str(round(trend_line, 2)) + ' dollars per day')
plt.plot_date(transactions['date'], transactions['change'], marker='o', linestyle='-', color='b')
plt.plot_date(transactions['date'], transactions['trend'], marker=None, linestyle='-', color='g')

plt.show()
plt.savefig('temp.png') 
os.system('eog temp.png')
os.remove('temp.png')

