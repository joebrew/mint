library(tidyverse)

costs <- 
  data_frame(number = 1:12,
             month = as.Date('2017-08-01') + months(1:12),
             rent = 1700,
             phone = 100,
             food = 1000,
             misc = 1000) %>%
  mutate(total = rent + phone + food + misc) %>%
  mutate(total_cum = cumsum(total)) %>%
  mutate(income = 1500) %>%
  mutate(income_cum = cumsum(income)) %>%
  mutate(diff = total_cum - income_cum)

wb <- 50 * 50
