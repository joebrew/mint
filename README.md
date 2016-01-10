# Mint
tools for scraping data from mint

## How  
Within the repository, create a "data" directory.  In that directory, create a file named "username_and_password.txt".  This should be a simple 2-line file in which the first line is your username (email address) and the second line is your password.

Run `python money_update.py` to get a snapshot of your financial situation.  If you want to get summary statistics only for a certain period, append a start date and end date to the above command, ie `python money_update.py 2015-09-01 2015-11-15`.