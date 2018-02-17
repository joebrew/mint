library(RColorBrewer)
library(tidyverse)
files <- dir('data')
data_list <- list()
today <- Sys.Date()
for (i in 1:length(files)){
  this_file <- files[i]
  this_data <- read_csv(paste0('data/', this_file))
  # Forward fill
  left <- data_frame(date = seq(min(this_data$date), 
                                today,
                                by = 1))
  this_data <- left_join(left,
                         this_data,
                         by = 'date')
  this_data <- this_data %>% tidyr::fill(amount, .direction = 'down')
  this_data$src <- unlist(lapply(strsplit(this_file, '.', fixed = TRUE), function(x){x[1]}))
 
  data_list[[i]] <- this_data
}
df <- bind_rows(data_list)

df$src <- factor(df$src,
                 levels = rev(c('ing',
                            'caixa',
                            'campus_checking',
                            'campus_savings',
                            'betterment',
                            'caixa_catalunya')))

df <- df %>%
  group_by(src) %>%
  mutate(md = max(date)) %>%
  ungroup %>%
  filter(date <= md) %>%
  dplyr::select(-md)

# Get currency
Quandl::Quandl.auth(readLines('credentials/quandl_auth.txt'))
fx <- Quandl::Quandl('CURRFX/USDEUR')
fx <- fx %>% dplyr::select(Date, Rate)
names(fx) <- c('date', 'eur')
fx <- fx %>% arrange(date)
left <- data_frame(date = seq(min(fx$date),
                              max(df$date),
                              by = 1))
fx <- left_join(left, fx, by = 'date')
fx <- fx %>% arrange(date)
fx <- fx %>% tidyr::fill(eur, .direction = 'down')

# Convert everything to usd
df <- df %>%
  left_join(fx,
            by = 'date')
df <- df %>%
  mutate(usd = ifelse(src %in% c('caixa_catalunya', 'caixa', 'ing'),
                      amount * (1/eur),
                      amount))


total <- df %>% group_by(src) %>% filter(date == max(date)) %>% ungroup %>% summarise(x = sum(usd)) %>% .$x


g <- ggplot(data = df) +
  geom_area(stat = 'identity',
            position = 'stack',
            color = 'black',
            size = 0.2,
            aes(x = date,
                y = usd,
                group = src,
                fill = src)) +
  theme_bw() +
  theme(legend.position = 'bottom') +
  scale_fill_manual(name = '',
                    values = brewer.pal(n = 6, name = 'Spectral')) +
  labs(x = 'Date',
       y = 'Dollars',
       title = paste0('We currently have ', prettyNum(round(total), big.mark = ','), ' USD'))
# Linear models
df$year <- as.numeric(format(df$date, '%Y'))
years <- sort(unique(df$year))
yl <- list()
for (i in 1:length(years)){
  this_year <- years[i]
  this_data <- df %>% filter(year == this_year)
  sub_data <- this_data %>% 
    # group_by(src) %>%
    filter(date == min(date) | date == max(date)) %>%
    ungroup
  sub_data <- sub_data %>%
    group_by(date) %>%
    summarise(usd = sum(usd))
  saved <- sub_data$usd[2] - sub_data$usd[1] 
  days <- as.numeric(sub_data$date[2] - sub_data$date[1]) + 1
  saved <- data.frame(date = as.Date(paste0(this_year, '-07-01')),
                      value = saved,
                      y = mean(sub_data$usd))
  word <- ifelse(saved$value > 0, 'Saved', 'Lost')
  saved$word <- word
  saved$days <- days
  saved$rate <- paste0('\n(', round(saved$value / saved$days, digits = 2), ' per day)')
  yl[[i]] <- saved
    g <- g +
    geom_line(data = sub_data,
              aes(x = date,
                  y = usd),
              lty = 2,
              alpha = 0.8,
              color = 'black') +
    # geom_label(data = saved,
    #            aes(x = date,
    #                y = 82000,
    #                # y = y + 10000,
    #                label = paste0(this_year, ':\n', word, ' ', round(saved$value), ' USD')),
    #            size = 3,
    #            alpha = 0.8,
    #            lty = 2) +
    geom_vline(xintercept = sub_data$date,
               color = 'black',
               alpha = 0.7)
    
}
yl <- bind_rows(yl)
g +
  ylim(0, 85000) +
  geom_text(data = yl,
             aes(x = date,
                 y = 82000,
                 # y = y + 10000,
                 label = paste0(format(date, '%Y'), ':\n', word, ' ', prettyNum(abs(round(value)), big.mark = ','), ' USD', rate)),
             size = 2.5,
             alpha = 0.8,
             lty = 2) +
  xlim(min(df$date),
       # max(df$date))
       as.Date(paste0(max(df$year), '-12-31')))

ggplot(data = df,
       aes(x = date,
           y = usd,
           fill = src)) +
  facet_wrap(~src) +
  geom_area(color = 'black', alpha = 0.7) +
  theme_bw() +
  theme(legend.position = 'none') +
  scale_fill_manual(name = '',
                    values = brewer.pal(n = 6, name = 'Spectral')) +
  labs(x = 'Date',
       y = 'Dollars') +
  geom_vline(xintercept = as.Date(paste0(2015:2018, '-01-01')),
             alpha = 0.6, lty = 2)
