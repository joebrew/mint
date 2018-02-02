#!/usr/bin/env python
import timestring
import datetime
import mintapi
import pandas as pd
import numpy as np
import os
import itertools
import matplotlib.pyplot as plt
import matplotlib
matplotlib.style.use('ggplot')
import sys
from ggplot import *
import numpy as np
import pylab
import time
import quandl as Quandl
from selenium import webdriver
from Cookie import SimpleCookie
driver_loc = "/usr/lib/chromium-browser/chromedriver"
os.environ["webdriver.chrome.driver"] = driver_loc
# driver = webdriver.Chrome(driver_loc)

# driver.get("http://stackoverflow.com")
# driver.quit()

pd.options.mode.chained_assignment = None

# Modify original mintapi code to get to work locally
def get_session_cookies2(username, password):
        try:
            from selenium import webdriver
            # driver = webdriver.Chrome(driver_loc)
            driver = webdriver.Chrome()
        except Exception as e:
            raise RuntimeError("ius_session not specified, and was unable to load "
                               "the chromedriver selenium plugin. Please ensure "
                               "that the `selenium` and `chromedriver` packages "
                               "are installed.\n\nThe original error message was: " +
                               (e.args[0] if len(e.args) > 0 else 'No error message found.'))

        driver.get("https://www.mint.com")
        driver.implicitly_wait(20)  # seconds
        driver.find_element_by_link_text("Log In").click()

        driver.find_element_by_id("ius-userid").send_keys(username)
        driver.find_element_by_id("ius-password").send_keys(password)
        driver.find_element_by_id("ius-sign-in-submit-btn").submit()

        # Wait until logged in, just in case we need to deal with MFA.
        while not driver.current_url.startswith('https://mint.intuit.com/overview.event'):
            time.sleep(1)

        try:
            return {
                'ius_session': driver.get_cookie('ius_session')['value'],
                'thx_guid': driver.get_cookie('thx_guid')['value']
            }
        finally:
            driver.close()

# Get username and password
fname = 'credentials/username_and_password.txt'
with open(fname) as f:
    content = [x.strip('\n') for x in f.readlines()]
email = content[0]
password = content[1]

# Get cookies
# had to manually do stuff here to get ius_session, 
# etc to work.
cookies = get_session_cookies2(username = email, password = password)
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


# https://github.com/mrooney/mintapi
# mint = mintapi.Mint(email, password)
mint = mintapi.Mint(email = email, password = password, ius_session = cookies['ius_session'], thx_guid = cookies['thx_guid'])

# Get basic account information
accounts = mint.get_accounts(True)
betterment = accounts[0]
checking = accounts[1]
savings = accounts[2]

# Get net worth
nw = mint.get_net_worth()
print 'Net worth in USA (savings + investments) is ' + str(nw) + ' dollars'

# If account hasn't been updated in last hour, upddate
time_since_last_update = datetime.datetime.now() - checking['lastUpdatedInDate']
if time_since_last_update.seconds > (60 * 60):
    # Initiate an account refresh
    mint.initiate_account_refresh()
    accounts = mint.get_accounts()
    betterment = accounts[0]
    checking = accounts[1]
    savings = accounts[2]

# # Get extended account detail at the expense of speed - requires an
# # additional API call for each account
# data2 = mint.get_accounts(True)

# # Get budget information
# budgets = mint.get_budgets()

#####
# READ IN SAVED DATA
#####
saved_checking = pd.read_csv('data/campus_checking.csv')
saved_savings = pd.read_csv('data/campus_savings.csv')
saved_caixa = pd.read_csv('data/caixa.csv')
saved_caixa_catalunya = pd.read_csv('data/caixa_catalunya.csv')
saved_betterment = pd.read_csv('data/betterment.csv')
saved_ing = pd.read_csv('data/ing.csv')

#####
# Update saved data
#####

# Checking account (campus)
today = time.strftime('%Y-%m-%d')
if saved_checking['date'].max() < today:
    saved_checking.loc[len(saved_checking)] = [today, checking['currentBalance']]

# Savings account (campus)
if saved_savings['date'].max() < today:
    saved_savings.loc[len(saved_savings)] = [today, savings['currentBalance']]

# Betterment
if saved_betterment['date'].max() < today:
    saved_betterment.loc[len(saved_betterment)] = [today, betterment['currentBalance']]

# Caixa
# (have to manually populate spreadsheet)
print 'Caixa last updated :' + saved_caixa['date'].max()

# Caixa catalunya
# (have to manually populate spreadsheet)
print 'Caixa Catalunya last updated :' + saved_caixa_catalunya['date'].max()

# ING
# (have to manually populate spreadsheet)
print 'ING last updated :' + saved_ing['date'].max()

#####
# OVERWRITE WITH NEW DATA
#####
saved_checking.to_csv('data/campus_checking.csv', index = False)
saved_savings.to_csv('data/campus_savings.csv', index = False)
saved_betterment.to_csv('data/betterment.csv', index = False)

#####
# COMBINE ALL TOGETHER
##### 

# Create a dataframe of unique dates
dates = pd.date_range(start = min(saved_checking['date']), end = max(saved_checking['date']))
dates = pd.Series(dates)
df = pd.DataFrame({'date' : dates})
# Sort by date (in case not already)
df = df.sort_values(by = 'date', ascending = True)
# Reset the index
df = df.reset_index(drop=True)

# Format dates
saved_savings['date'] = pd.to_datetime(saved_savings['date'])
saved_checking['date'] = pd.to_datetime(saved_checking['date'])
saved_caixa['date'] = pd.to_datetime(saved_caixa['date'])
saved_caixa_catalunya['date'] = pd.to_datetime(saved_caixa_catalunya['date'])
saved_betterment['date'] = pd.to_datetime(saved_betterment['date'])
saved_ing['date'] = pd.to_datetime(saved_ing['date'])

# Forward fill NAs
saved_savings = pd.merge(left = df, right = saved_savings, how = 'left', on = ['date'])
saved_savings['amount'] = saved_savings['amount'].fillna(method='pad')

saved_checking = pd.merge(left = df, right = saved_checking, how = 'left', on = ['date'])
saved_checking['amount'] = saved_checking['amount'].fillna(method='pad')

saved_caixa = pd.merge(left = df, right = saved_caixa, how = 'left', on = ['date'])
saved_caixa['amount'] = saved_caixa['amount'].fillna(method='pad')

saved_caixa_catalunya = pd.merge(left = df, right = saved_caixa_catalunya, how = 'left', on = ['date'])
saved_caixa_catalunya['amount'] = saved_caixa_catalunya['amount'].fillna(method='pad')

saved_betterment = pd.merge(left = df, right = saved_betterment, how = 'left', on = ['date'])
saved_betterment['amount'] = saved_betterment['amount'].fillna(method='pad')

saved_ing = pd.merge(left = df, right = saved_ing, how = 'left', on = ['date'])
saved_ing['amount'] = saved_ing['amount'].fillna(method='pad')

# Specify each data source
saved_savings['source'] = 'Illiquid - US Savings'
saved_checking['source'] = 'Liquid - US checking'
saved_caixa['source'] = 'Liquid - La Caixa'
saved_caixa_catalunya['source'] = 'Illiquid - Caixa Catalunya'
saved_betterment['source'] = 'Illiquid - US investments'
saved_ing['source'] = 'Liquid - ING'

#####
# CURRENCY CONVERSION
##### 
# Get quandl authentication
fname = 'credentials/quandl_auth.txt'
with open(fname) as f:
    content = [x.strip('\n') for x in f.readlines()]

# Specify Euros
# currency_code = 'BNP/USDEUR'
currency_code = 'CURRFX/USDEUR'
temp = Quandl.get(currency_code, authtoken = ''.join(content))
# Clean up / organize
temp = pd.DataFrame(temp)
temp['date'] = temp.index
temp['usd'] = temp.ix[:,0:1]
# temp = temp.drop('USD/EUR', axis = 1)
temp = temp.drop(['Rate', 'High (est)', 'Low (est)'], axis = 1)
temp = temp.reset_index(drop = True)
# Format date
temp['date'] = pd.to_datetime(temp['date'])
# Add a value for new days if needed
# WORKING HERE
the_day = today
while temp['date'].max().strftime('%Y-%m-%d') < the_day:
    # Bring the day back one
    the_day = str(timestring.Date(the_day) - 1)[:10]
    temp.loc[len(temp)] = [the_day, temp['usd'][len(temp)-1]]
    temp['date'] = pd.to_datetime(temp['date'])
# If no value for today, add:
if temp['date'].max().strftime('%Y-%m-%d') < today:
    temp.loc[len(temp)] = [today, temp['usd'][len(temp)-1]]
    temp['date'] = pd.to_datetime(temp['date'])

# Convert dataframes in euros
saved_caixa = pd.merge(left = saved_caixa, right = temp, how = 'left')
# forward fill NAs (weekends?)
saved_caixa['usd'] = saved_caixa['usd'].fillna(method='pad')
saved_caixa['amount'] = saved_caixa['amount'] / saved_caixa['usd']
saved_caixa = saved_caixa.drop('usd', axis = 1)

saved_caixa_catalunya = pd.merge(left = saved_caixa_catalunya, right = temp, how = 'left')
# forward fill NAs (weekends?)
saved_caixa_catalunya['usd'] = saved_caixa_catalunya['usd'].fillna(method='pad')
saved_caixa_catalunya['amount'] = saved_caixa_catalunya['amount'] / saved_caixa_catalunya['usd']
saved_caixa_catalunya = saved_caixa_catalunya.drop('usd', axis = 1)

saved_ing = pd.merge(left = saved_ing, right = temp, how = 'left')
# forward fill NAs (weekends?)
saved_ing['usd'] = saved_ing['usd'].fillna(method='pad')
saved_ing['amount'] = saved_ing['amount'] / saved_ing['usd']
saved_ing = saved_ing.drop('usd', axis = 1)


# Combine
combined = saved_savings.append(saved_checking)
combined = combined.append(saved_caixa)
combined = combined.append(saved_caixa_catalunya)
combined = combined.append(saved_betterment)
combined = combined.append(saved_ing)

#####
# VISUALIZE
#####
# p = ggplot(aes(x='date', fill='source', color='source', ymin=0, ymax='amount'), data = combined)
# # p = p + geom_point()
# p = p + geom_area(position='stack')
# # p = p + geom_line()
# plt = p.draw()
# plt.savefig('temp.png') 
# os.system('eog temp.png')

# p = ggplot(aes(x='date', color='source', y='amount'), data = combined)
# # p = p + geom_point()
# p = p + geom_line(alpha=0.9)
# # p = p + geom_line()
# plt = p.draw()
# plt.savefig('temp.png') 
# os.system('eog temp.png')

# ggplot(aes(x='date', ymin='total', ymax='total'), data=df) + geom_area()


tableau20 = [(31, 119, 180), (174, 199, 232), 
(255, 127, 14), (255, 187, 120), (44, 160, 44), 
(152, 223, 138), (214, 39, 40), (255, 152, 150), 
(148, 103, 189), (197, 176, 213), (140, 86, 75), 
(196, 156, 148), (227, 119, 194), (247, 182, 210), 
(127, 127, 127), (199, 199, 199), (188, 189, 34), 
(219, 219, 141), (23, 190, 207), (158, 218, 229)]

for i in range(len(tableau20)): 
    r, g, b = tableau20[i] 
    tableau20[i] = (r / 255., g / 255., b / 255.)

# Cast data
casted = pd.pivot_table(combined, values='amount', index = 'date', columns = 'source', aggfunc=np.mean)
ax = casted.plot(kind='area', color = tableau20, alpha=.7);
pylab.xlabel('Date')
pylab.ylabel('Dollars')
pylab.title('Net worth: ' + str(combined[combined['date'] == combined['date'].max()]['amount'].sum().round()) + ' dollars ' + 'on ' + str(datetime.datetime.now())) 

pylab.savefig('temp.png') 
print(combined[combined['date'] == max(combined['date'])])
os.system('eog temp.png')


# os.remove('temp.png')

# # Visualize transactions
# transactions = mint.get_transactions()
# transactions = pd.DataFrame(transactions)
# transactions = transactions.sort(columns = 'date', ascending = False)

# print transactions


# OLD STUFF
# #####
# # Get transactions
# #####
# transactions = mint.get_transactions()
# transactions = pd.DataFrame(transactions)
# # sort by date
# transactions = transactions.sort(columns = 'date', ascending = False)

# # Create a "multiplier" (to get true transaction amount)
# transactions['multiplier'] = list(itertools.repeat(1, len(transactions)))
# transactions['multiplier'][transactions['transaction_type'] == 'debit'] = -1

# # Create a dataframe of unique dates
# dates = pd.date_range(start = min(transactions['date']), end = max(transactions['date']))
# dates = pd.Series(dates)
# df = pd.DataFrame({'date' : dates})
# # Sort by date (in case not already)
# df = df.sort(columns = 'date', ascending = False)
# # Reset the index
# df = df.reset_index(drop=True)

# # Create column for total
# df['total'] = list(itertools.repeat(0, len(df)))

# # Make a "change" column
# df['change'] = list(itertools.repeat(0, len(df)))

# # How much now?
# df['total'][0] = checking['currentBalance'] + betterment['currentBalance'] + savings['currentBalance']

# # How much at any given time
# for i in range(1, len(df)):
#     print i
#     # Which date are we calculating for
#     the_date = df['date'][i]
#     # What transactions happened the next day
#     transactions_next_day = transactions[transactions['date']== df['date'][i-1]]
#     # What's the total change the next day
#     if(len(transactions_next_day['amount']) == 0):
#         change_next_day = 0
#     else:
#         change_next_day = sum(transactions_next_day['amount'] * transactions_next_day['multiplier'])
#     # Since we know the next day's change, the next day's
#     # final total plus the inverse of the change is this day's final total
#     df['total'][i] = df['total'][i-1] + (change_next_day * -1.0)


# # Visualize
# plt.plot_date(df['date'], df['total'], marker = None)
# plt.show()
# plt.savefig('temp.png') 
# os.system('eog temp.png')

# p = ggplot(aes(x='date', y='total'), data = df)
# p = p + geom_point()
# p = p + geom_line()
# plt = p.draw()
# plt.savefig('temp.png') 
# os.system('eog temp.png')

# ggplot(aes(x='date', ymin='total', ymax='total'), data=df) + geom_area()


# # How much at any given time?
# for i in range(1, len(transactions)):
#   val_before = transactions.ix[(i-1)]['total']
#   type_before = transactions.ix[(i-1)]['transaction_type']
#   change_before = transactions.ix[(i-1)]['amount']
#   if type_before == 'credit':
#       change_before = change_before * -1
#   #transactions['total'][i] = val_before + change_now
#   transactions.loc[i, 'total'] = val_before + change_before
# for i in range(0, len(transactions)):
#   type_now = transactions.ix[i]['transaction_type']
#   if type_now == 'debit':
#       transactions.loc[i, 'change'] = transactions.loc[i, 'amount'] * -1
#   else:
#       transactions.loc[i, 'change'] = transactions.loc[i, 'amount'] 

# # Subset transactions based on start and end dates
# if start:
#   start = datetime.datetime.strptime(start, '%Y-%m-%d')
# else:
#   start = transactions['date'].min()
# if end:
#   end = datetime.datetime.strptime(end, '%Y-%m-%d')
# else:
#   end = transactions['date'].max()
# transactions_subset = transactions.loc[(transactions.date >= start) & (transactions.date <= end),]

# # Make a trend line
# days_elapsed = (end - start).days + 1
# start_point = transactions_subset.total[len(transactions_subset.total)-1]
# end_point = transactions_subset.total.iloc[0]
# trend_line = (end_point - start_point) / days_elapsed
# transactions_subset['trend'] = list(itertools.repeat(0, len(transactions_subset)))
# unique_dates = transactions_subset.date.unique()
# for date in unique_dates:
#   time_ago = (date - unique_dates[len(unique_dates)-1])
#   days_ago = time_ago.astype('timedelta64[D]').astype(int)
#   transactions_subset.trend[transactions_subset['date'] == date] = start_point + (days_ago * trend_line)

# # Merge it all back together
# transactions = pd.merge(left = transactions, right = transactions_subset, how = 'left')

# #####
# # OUTPUT
# #####

# # Calculate changes over last week and month
# today = datetime.datetime.today()
# a_week_ago = today - datetime.timedelta(days = 6)
# a_month_ago = today - datetime.timedelta(days = 30)

# credits = transactions['amount'][transactions['transaction_type'] == 'credit']
# debits = transactions['amount'][transactions['transaction_type'] == 'debit']

# credits_last_week = int(credits[transactions['date'] >= a_week_ago].sum())
# debits_last_week = int(debits[transactions['date'] >= a_week_ago].sum())

# credits_last_month = int(credits[transactions['date'] >= a_month_ago].sum())
# debits_last_month = int(debits[transactions['date'] >= a_month_ago].sum())

# credits_period = transactions_subset['amount'][transactions_subset['transaction_type'] == 'credit'].sum()
# debits_period = transactions_subset['amount'][transactions_subset['transaction_type'] == 'debit'].sum()

# ########
# print '\n\n\n\n\n'
# for i in range(10):
#   print '.'

# # PRINT TABLE
# print('------------------------------------')
# print('TABLE')
# temp = transactions.loc[range(30)][['date', 'total', 'change','description']]
# print temp.iloc[::-1]
# print('_________________\n\n')


# # WEEK
# print('------------------------------------')
# print('WEEK')
# print 'You earned ' + str(credits_last_week) + ' dollars over the last 7 days (' + str(credits_last_week / 7) + ' per day).'
# print 'You spent ' + str(debits_last_week) + ' dollars over the last 7 days (' + str(debits_last_week / 7) + ' per day).'
# net_change = credits_last_week - debits_last_week
# if net_change >= 0:
#   direction = 'up'
# else:
#   direction = 'down'
# print 'So, you are ' + direction + ' ' + str(abs(net_change)) + ' on the week. (' + str(net_change / 7) + ' per day).'
# print('_________________\n\n')

# # MONTH
# print('------------------------------------')
# print('MONTH')
# print 'You have earned ' + str(credits_last_month) + ' dollars over the last 30 days (' + str(credits_last_month / 30) + ' per day).'
# print 'You have spent ' + str(debits_last_month) + ' dollars over the last 30 days (' + str(debits_last_month / 30) + ' per day).'
# net_change = credits_last_month - debits_last_month
# if net_change >= 0:
#   direction = 'up'
# else:
#   direction = 'down'
# print 'So, you are ' + direction + ' ' + str(abs(net_change)) + ' on the month. (' + str(net_change / 30) + ' per day).'
# print('_________________\n\n')

# # Print current amount
# print('CURRENT STATUS')
# print('------------------------------------')
# print 'YOU HAVE ' + str(checking['currentBalance']) + ' DOLLARS.'
# print 'At your current monthly spending rate, with no revenue at all, you would run out of money in ' + str(int(checking['currentBalance'] / (debits_last_month / 30))) + ' days.'
# print('_________________\n\n')

# # PERIOD
# daily_spending_period = debits_period / days_elapsed
# daily_income_period = credits_period / days_elapsed
# daily_savings_period = trend_line # why doesn't this equal: daily_income_perio
# print('------------------------------------')
# print('PERIOD OVERVIEW')
# print 'You have earned ' + str(credits_period) + ' dollars over the green period (' + str(round(credits_period / days_elapsed, 2)) + ' per day).'
# print 'You have spent ' + str(debits_period) + ' dollars over the green period (' + str(round(debits_period / days_elapsed, 2)) + ' per day).'
# print 'Your green period lifestyle cost is ' + str(round(debits_period / days_elapsed * 365.25, 2)) + ' dollars per year'
# print 'Your green period income rate is ' + str(round(daily_income_period * 365.25, 2)) + ' dollars per year'
# print 'Your green period savings rate is ' + str(round(daily_savings_period * 365.25, 2)) + ' dollars per year (' + str(round(daily_savings_period, 2)) + ' per day)'

# #####
# # MAKE TOTAL WORTH CHART
# #####
# plt.plot_date(transactions['date'], transactions['total'], marker=None, linestyle='--', color='r')
# plt.xlabel('Date')
# plt.ylabel('Dollars')
# plt.title('Savings rate during green period: ' + str(round(trend_line, 2)) + ' dollars per day')
# plt.plot_date(transactions['date'], transactions['change'], marker='o', linestyle='-', color='b')
# plt.plot_date(transactions['date'], transactions['trend'], marker=None, linestyle='-', color='g')

# plt.show()
# plt.savefig('temp.png') 
# os.system('eog temp.png')
# os.remove('temp.png')