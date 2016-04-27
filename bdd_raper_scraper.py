#!/usr/bin/python2
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import pprint


#global variables
debug = True
next_enabled = True


data_queue = []

#config settings for each category for url , table, type mapping
cfg = {
    'PrimaryWeapon': {'url': 'weapon', 'table': 'Weapon', 'type': 'primary_weapon'},
    'SecondaryWeapon': {'url': 'subweapon', 'table': 'Weapon', 'type': 'secondary_weapon'},
    'Fish': {'url': 'items/fish', 'table': 'MainItem', 'type': 'seafood'}
}


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
def next_page(config):
    global next_enabled
    table=config['table']
    pages = br.find_elements_by_xpath("//div[@id='{table}Table_paginate']/ul/li".format(table=table))
    last = len(pages) - 1
    if 'disabled' not in pages[last].get_attribute('class'):
        dp('Clicking on {}'.format(pages[last].text))
        next_button = pages[last].find_element_by_tag_name('a')
        next_button.click()
        time.sleep(3)
        rows = br.find_elements_by_xpath("//table[@id='{table}Table']/tbody/tr".format(table=table))
        parse_category(config, rows)
        return
    else:
        next_enabled = False
        return


#parse out the data we need
def parse_category(config,rows):
    global data_queue
    table = config['table']
    if table == 'Weapon':
        for row in rows:
            cols = row.find_elements_by_tag_name('td')
            url = cols[2].find_element_by_tag_name('a')
            img = cols[1].find_element_by_tag_name('img')
            data = {'type': config['type'], 'bdd_id': cols[0].text, 'img': img.get_attribute('src'),
                    'url': url.get_attribute('href'), 'level': cols[3].text, 'AP': cols[4].text, 'DP': cols[5].text,
                    'name': url.text
                    }
            data_queue.append(data)
    #MainItem table has no AP/DP so it needs its own parsing
    elif table == 'MainItem':
        for row in rows:
            cols = row.find_elements_by_tag_name('td')
            url = cols[2].find_element_by_tag_name('a')
            img = cols[1].find_element_by_tag_name('img')
            data = {'type': config['type'], 'bdd_id': cols[0].text, 'img': img.get_attribute('src'),
                    'url': url.get_attribute('href'), 'level': cols[3].text, 'name': url.text
                    }
            data_queue.append(data)
    else:
        return


#hit the url, xpath to the appropriate table and pass up to parse_category, call next page.
def snarf_category(config):
    global next_enabled
    next_enabled = True
    dp('Starting scrape of {}'.format(config['type']))
    url = config['url']
    dp('URL is {}'.format(url))
    br.get("http://www.bddatabase.net/{lang}/{url}".format(lang=lang,url=url))
    table = config['table']
    br.find_element_by_xpath("//select[@name='{table}Table_length']/option[text()='100']".format(table=table)).click()
    time.sleep(3)
    rows = br.find_elements_by_xpath("//table[@id='{table}Table']/tbody/tr".format(table=table))

    parse_category(config,rows)
    while next_enabled:
        next_page(config)



br = webdriver.Chrome(chrome_options=chrome_options)
#categories = [ 'Fish', 'Weapon', 'SubWeapon' ]
categories = ['Fish', 'PrimaryWeapon', 'SecondaryWeapon']
for cat in categories:
    snarf_category(cfg[cat])

pp.pprint(data_queue)
print "Entries: {size}".format(size=len(data_queue))

br.quit()