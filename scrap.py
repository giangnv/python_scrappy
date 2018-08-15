#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Scrap data from tuvi.cohoc.net
"""

import sys
import re
import unicodedata
import os
from collections import Counter
# Use for caching scrapped page id
import redis
from bs4 import BeautifulSoup
import requests
from time import gmtime, strftime
from subprocess import call
import time

REDIS_SCRAPPED_KEY_PREFIX = 'TUVI_SCRAPPED_PAGE_{}'
REDIS_PAGE_NOT_FOUND_KEY_PREFIX = 'TUVI_PAGE_NOT_FOUND_{}'
PAGE_ID_WAS_SCRAPPED = 'Page ID: {} is already scrapped!'
PAGE_ID_IS_NOT_FOUND = 'Page ID: {} is not found!'
ROOT_DIR = 'scrapped_results'
NUMBER_OF_RETRY = 5

conn = redis.StrictRedis(
    host='localhost',
    port=6379)

#'http://tuvi.cohoc.net/la-so-tu-vi-co-hoc-lid-' + id + '.html';
URL_SCRAPPER = 'http://tuvi.cohoc.net/la-so-tu-vi-co-hoc-lid-{}.html'
URL_PAGE_NOT_FOUND = 'http://tuvi.cohoc.net/404.html?ref=la-so-1'
#LOG_FILE
LOG_FILE = 'scrapping.log'

"""
Mậu Tuất => Mau Tuat
Ất Sửu => At Suu
"""
def no_accent_vietnamese(s):
    # s = s.decode('utf-8')
    s = re.sub(u'Đ', 'D', s)
    s = re.sub(u'đ', 'd', s)
    return unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('utf-8')

def create_folder_by_structure(year, month):
    directory = ROOT_DIR + '/' + year + '/' + month
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory


def save_to_redis(key, value):
    try:
        conn.set(key, value)
    except Exception as ex:
        print('Error:', ex)

def is_already_exist_key(key):
    try:
        value = conn.get(key)
        if (value is not None):
            return True
        return False
    except Exception as ex:
        print('Error:', ex)
        return False


def set_scraped(id):
    save_to_redis(REDIS_SCRAPPED_KEY_PREFIX.format(id), '1')

def is_already_scraped(id):
    return is_already_exist_key(REDIS_SCRAPPED_KEY_PREFIX.format(id))

def set_page_not_found(id):
    save_to_redis(REDIS_PAGE_NOT_FOUND_KEY_PREFIX.format(id), '1')


def is_already_set_page_not_found(id):
    return is_already_exist_key(REDIS_PAGE_NOT_FOUND_KEY_PREFIX.format(id))

"""
"Lá số giới tính Nam, sinh giờ Mùi, ngày 3, tháng 9, năm Ất Mùi" 
=> Counter({'birth_year': 'Ất Mùi', 'sex': 'Nam', 'birth_hour': 'Mùi', 'birth_month': '9', 'birth_date': '3'})
"""
def parser_date_from_title(s):
    result = Counter()
    s_array = s.split(',')
    keys = ['sex', 'birth_hour', 'birth_date', 'birth_month', 'birth_year']
    for i in range(len(keys)):
        if (i < len(keys) - 1):
            result[keys[i]] = s_array[i].split(' ')[-1]
        else:
            result[keys[i]] = s_array[-1].split(' ')[-2] + \
                ' ' + s_array[-1].split(' ')[-1]

    return result


"""
"Lá số giới tính Nam, sinh giờ Mùi, ngày 3, tháng 9, năm Ất Mùi" 
=> Nam_Mui_13_9_AtMui
"""
def get_filename_to_save(s):
    title_parser = parser_date_from_title(s)
    result = []
    for key, value in title_parser.items():
        result.append(no_accent_vietnamese(value).replace(' ', ''))

    return '_'.join(result)

def store_scrap_page(title, content):
    title_parser = parser_date_from_title(title)
    year = no_accent_vietnamese(title_parser['birth_year'].replace(' ', '_'))
    month = title_parser['birth_month']
    store_dir = create_folder_by_structure(year, month)
    file_path = store_dir + '/' + get_filename_to_save(title) + '.html'
    if not os.path.exists(file_path):
        with open(file_path, 'w') as scrap_file:
            scrap_file.write(content)
    

def write_log(message):
    line = '[' + strftime('%Y-%m-%d %H:%M:%S', gmtime()) + '] : ' + message + '\n'
    file = open(LOG_FILE, 'a')
    file.write(line)
    file.close()

"""
If redirected: 
    If page not found: => redirect to "http://tuvi.cohoc.net/404.html?ref=la-so-1"
    If page found: redirect to "http://tuvi.cohoc.net/404.html?ref=cache-not-found&id=1111"
if not redirected: "http://tuvi.cohoc.net/la-so-tu-vi-co-hoc-lid-" + id + ".html"
"""
def scrap_page_content(id):
    if (is_already_scraped(id)):
        write_log(PAGE_ID_WAS_SCRAPPED.format(id))
        return None

    if (is_already_set_page_not_found(id)):
        write_log(PAGE_ID_IS_NOT_FOUND.format(id))
        return None

    write_log('|====================================|')
    write_log('Start scrap page with id {}'.format(id))
    url = URL_SCRAPPER.format(id)
    response = requests.get(url)
    if response.history:
        for resp in response.history:
            print(resp.status_code, resp.url)
        print(response.status_code, response.url)
        if response.url == URL_PAGE_NOT_FOUND:
            write_log('Page ID: {} is not found! Already set to cache!!!'.format(id))
            set_page_not_found(id)
        else:
            # Retry again
            write_log('Page ID: {} is redirected!'.format(id))
            print('Redirected page: ' + response.url)
            phantomjs_cmd = 'phantomjs open_url.js "' + str(id) + '"'
            os.system(phantomjs_cmd)
            write_log('Retrying page ID {}...'.format(id))
            i = 1
            while i < NUMBER_OF_RETRY:
                time.sleep(2)
                try:
                    retry_response = requests.get(url)
                    print("Retrying page ID {} at {} time...".format(id, i))
                    do_scrap_exist_page(id, retry_response.text)
                    break
                except IndexError:
                    i += 1
    else:
        write_log("Page ID {} is exist. Do nothing!".format(id))
        #do_scrap_exist_page(id, response.text)
    write_log('End scrap page with id {}'.format(id))

def do_scrap_exist_page(id, response_text):
    write_log('Page ID: {} is exist'.format(id))
    ## Parse content
    soup = BeautifulSoup(response_text, 'html.parser')
    title = soup.find('h2', class_='alt text-center').get_text()
    laso = soup.find('div', class_='laso')
    vung_giai_doan = soup.find('div', class_='vung-giai-doan')
    content = str(laso) + str(vung_giai_doan)
    store_scrap_page(title, content)
    write_log('Page ID: {} was scrapped with name: {}'.format(id, title))
    set_scraped(id)

def execute(max_page_id):
    if (max_page_id < 1):
        print('Please use number greater than 0!!')
        sys.exit(1)
    
    for index in range(max_page_id):
        scrap_page_content(index + 1)
    print('Scrap data is done!')

if __name__ == '__main__':
    if (len(sys.argv) != 2):
        print('Use: python ' + sys.argv[0] + ' NUMBER_OF_MAX_ID')
        sys.exit(1)

    try:
        max_page_id = int(sys.argv[1])
        execute(max_page_id)
    except ValueError:
        print(sys.argv[1] + ' is not number!!!')
        sys.exit(1)
