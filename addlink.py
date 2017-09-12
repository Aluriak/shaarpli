#!/usr/bin/python3
import os
import sys
import csv
import time
import codecs
from shaarpli.data import CSV_PARAMS
from shaarpli import config

CONFIG = config.get()
DATABASE = CONFIG.autopublish.filepath
try:
    DATA_TO_ADD = sys.argv[1]
except IndexError:
    print('Expect first arg to be path to the file containing the information to add to database.')
    exit(1)

print('ENCODING:', sys.stdout.encoding)
# extract data
with codecs.open(DATA_TO_ADD, 'r', encoding='utf_8_sig') as fd:
    title = next(fd).strip()
    url = next(fd).strip()
    body = fd.read().strip()
    pubdate = int(time.time())


# write data into database
WORKING_DIR = os.path.dirname(os.path.realpath(sys.argv[0]))
os.chdir(WORKING_DIR)

# NB: do not append the utf-8-sig at start (the codec is dumb: it would add it at the end)
with codecs.open(DATABASE, 'a', encoding='utf_8') as fd:
    writer = csv.writer(fd, **CSV_PARAMS)
    writer.writerow((title, body, url, pubdate))

print('DONE:', title)
