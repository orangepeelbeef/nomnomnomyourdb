#!/usr/bin/python2
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import pprint


#global variables
debug = True
next_enabled = True


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

#click on the Next button if it isn't disabled and kick off another parsing.
def next_page(category):
    global next_enabled
    pages = br.find_elements_by_xpath("//div[@id='{category}Table_paginate']/ul/li".format(category=category))
    if 'disabled' not in pages[7].get_attribute('class'):
        dp('Clicking on {}'.format(pages[7].text))
        next_button = pages[7].find_element_by_tag_name('a')
        next_button.click()
        time.sleep(3)
        rows = br.find_elements_by_xpath("//table[@id='{category}Table']/tbody/tr".format(category=category))
        parse_category(category, rows)
        return
    else:
        next_enabled = False
        return


#parse out the data we need
def parse_category(category,rows):
    global data_queue
    if category == 'Weapon':
        for row in rows:
            cols = row.find_elements_by_tag_name('td')
            url = cols[2].find_element_by_tag_name('a')
            img = cols[1].find_element_by_tag_name('img')
            data = {'type': 'weapon', 'bdd_id': cols[0].text, 'img': img.get_attribute('src'),
                    'url': url.get_attribute('href'), 'level': cols[3].text, 'AP': cols[4].text, 'DP': cols[5].text,
                    'name': url.text
                    }
            data_queue.append(data)
    else:
        return


#hit the url, xpath to the appropriate table and pass up to parse_category, call next page.
def snarf_category(category):
    global next_enabled
    br.get("http://www.bddatabase.net/{lang}/{category}".format(lang=lang,category=category.lower()))
    br.find_element_by_xpath("//select[@name='{category}Table_length']/option[text()='100']".format(category=category)).click()
    time.sleep(3)
    rows = br.find_elements_by_xpath("//table[@id='{category}Table']/tbody/tr".format(category=category))

    parse_category(category,rows)
    while next_enabled:
        next_page(category)



br = webdriver.Chrome(chrome_options=chrome_options)
snarf_category('Weapon')

pp.pprint(data_queue)
print "Entries: {size}".format(size=len(data_queue))

br.quit()