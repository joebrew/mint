library(Quandl)
library(dplyr)
df <- Quandl("YAHOO/INDEX_GSPC")
plot(df$Date, df$Close, type = 'l')

# Order from old to young
df <- arrange(df, Date)

# Classify whether the last week has been negative or positive
df$last_week <- NA
for (i in 10:nrow(df)){
  df$last_week[i] <- 
    ifelse((df$Close[i-1] - df$Close[i-8]) > 0, 'positive', 'negative')
}
df <- df %>% filter(Date >= '2000-01-01')

# Write out function for strategy
strategize <- function(start_date = min(df$Date), 
                       end_date = max(df$Date),
                       buy_when = 'negative',
                       days_when = 1,
                       amount = 1000){
  
  # Subset data to b/w start and end dates
  sub_data <- df %>% filter
  
  # Dataframe to store results
  results <- 
  # Define which days are buy
  which(df$last_week == buy_when)
  
}