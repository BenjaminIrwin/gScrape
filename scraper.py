import time

import undetected_chromedriver as uc

driver = uc.Chrome()
driver.get('https://nowsecure.nl')

# Sleep for 120 seconds
time.sleep(120)
