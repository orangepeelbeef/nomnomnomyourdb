#!/usr/bin/python2
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
import json
import time
import pprint
from hotqueue import HotQueue


#global variables

next_enabled = True
data_queue = []

#app configuration
appcfg = {
    'debug': True,
    'redis': True,
    'redis_host': 'localhost',
    'redis_port': 6379,
    'redis_db': 0,
    'queue_name': 'bdd'
}


#config settings for each category for url , table, type mapping
catmap = {
    'PrimaryWeapon': {'url': 'weapon', 'table': 'Weapon', 'type': 'primary_weapon'},
    'SecondaryWeapon': {'url': 'subweapon', 'table': 'Weapon', 'type': 'secondary_weapon'},
    'Fish': {'url': 'items/fish', 'table': 'MainItem', 'type': 'seafood'},
    'ProdRecipes': {'url': 'designs', 'table': 'Recipes', 'type': 'production'},
    'CookingRecipes': {'url': 'recipes/culinary', 'table': 'Recipes', 'type': 'cooking'}
}

#setup ublock origin adblocker cuz BDDatabase is horribly full of ads/adware
chrome_options = Options()
chrome_options.add_extension('ublock-origin_1_6_8.crx')

#language of site
lang = 'us'

#set up the data dumper style output for debuggins
pp = pprint.PrettyPrinter(indent=4)

#debug print function so final version is more quiet :)
def dp(message):
    global appcfg
    if appcfg['debug']:
        print message


def parse_icon_mats(mats):
    mat_data = []
    # this needs optimization, it takes quite a while to get all the data out of the mats
    for mat in mats:
        # dp(mat.get_attribute('innerHTML'))
        mat_img = mat.find_element_by_tag_name('img').get_attribute('src')
        try:
            mat_qty = mat.find_element_by_css_selector('div.quantity_small.nowrap').text
        except NoSuchElementException:
            mat_qty = "1"
        mat_url = mat.find_element_by_tag_name('a').get_attribute('href')
        mat_data.append({'img': mat_img, 'qty': mat_qty, 'url': mat_url})
    return mat_data



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


def output_category(cat,data):
    global redis_enabled, appcfg

    pp.pprint(data)
    print "{cat} Entries: {size}".format(cat=cat,size=len(data))
    if appcfg['redis']:
        queue = HotQueue(
            appcfg['queue_name'], host=appcfg['redis_host'], port=appcfg['redis_port'], db=appcfg['redis_db']
        )
        for item in data:
            queue.put(item)



#parse out the data we need
def parse_category(config,rows):
    global data_queue
    table = config['table']
    #WeaponTable parsing
    if table == 'Weapon':
        for row in rows:
            #cols  id, image, title, level, ap, dp
            cols = row.find_elements_by_tag_name('td')
            url = cols[2].find_element_by_tag_name('a')
            img = cols[1].find_element_by_tag_name('img')
            data = {'type': config['type'], 'bdd_id': cols[0].text, 'img': img.get_attribute('src'),
                    'url': url.get_attribute('href'), 'level': cols[3].text, 'AP': cols[4].text, 'DP': cols[5].text,
                    'name': url.text
                    }
            data_queue.append(data)
    #MainItemTable parsing
    elif table == 'MainItem':
        for row in rows:
            #cols  id, image, title, level,
            cols = row.find_elements_by_tag_name('td')
            url = cols[2].find_element_by_tag_name('a')
            img = cols[1].find_element_by_tag_name('img')
            data = {'type': config['type'], 'bdd_id': cols[0].text, 'img': img.get_attribute('src'),
                    'url': url.get_attribute('href'), 'level': cols[3].text, 'name': url.text
                    }
            data_queue.append(data)
    #RecipeTable parsing
    elif table == 'Recipes':
        for row in rows:
            #cols   id, image, title, skill level, materials, products
            cols = row.find_elements_by_tag_name('td')
            url = cols[2].find_element_by_tag_name('a')
            img = cols[1].find_element_by_tag_name('img')
            #mats are displayed as icons with quantity in a separate div
            mats = cols[4].find_elements_by_css_selector('div.iconset_wrapper_medium')
            mat_data = parse_icon_mats(mats)
            data = {'type': config['type'], 'bdd_id': cols[0].text, 'img': img.get_attribute('src'),
                    'url': url.get_attribute('href'), 'skill_level': cols[3].text, 'name': url.text,
                    'mats': mat_data
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
    time.sleep(5)
    rows = br.find_elements_by_xpath("//table[@id='{table}Table']/tbody/tr".format(table=table))

    parse_category(config,rows)
    while next_enabled:
        next_page(config)




br = webdriver.Chrome(chrome_options=chrome_options)

#categories = ['Fish', 'PrimaryWeapon', 'SecondaryWeapon']
categories = ['ProdRecipes','CookingRecipes']
for cat in categories:
    snarf_category(catmap[cat])
    output_category(cat, data_queue)
    data_queue=[]

br.quit()
