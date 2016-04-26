#!/usr/bin/python2
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import pprint


#global variables
debug = True

data_queue = []

chrome_options = Options()
chrome_options.add_extension('ublock-origin_1_6_8.crx')

#language of site
lang = 'us'


pp = pprint.PrettyPrinter(indent=4)

#debug print function
def dp(message):
    if debug:
        print message

def next_page():
    br.find_element_by_

br = webdriver.Chrome(chrome_options=chrome_options)
br.get('http://www.bddatabase.net/{lang}/weapon/'.format(lang=lang))

#click 100 listing of items
br.find_element_by_xpath("//select[@name='WeaponTable_length']/option[text()='100']").click()
time.sleep(3)

#grab weapon table rows
rows = br.find_elements_by_xpath("//table[@id='WeaponTable']/tbody/tr")

for row in rows:
    cols = row.find_elements_by_tag_name('td')
    url = cols[2].find_element_by_tag_name('a')
    img = cols[1].find_element_by_tag_name('img')
    data = {'type': 'weapon', 'bdd_id': cols[0].text, 'img': img.get_attribute('src'),
            'url': url.get_attribute('href'), 'level': cols[3].text, 'AP': cols[4].text, 'DP': cols[5].text,
            'name': url.text
            }
    data_queue.append(data)

pp.pprint(data_queue)
br.quit()