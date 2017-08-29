
import os
import sys
import csv
import time
from shaarpli.data import CSV_PARAMS
from shaarpli import config

CONFIG = config.get()
DATABASE = CONFIG.autopublish.filepath
try:
    DATA_TO_ADD = sys.argv[1]
except IndexError:
    print('Expect first arg to be path to the file containing the information to add to database.')
    exit(1)

# extract data
with open(DATA_TO_ADD) as fd:
    title = next(fd).strip()
    url = next(fd).strip()
    body = fd.read().strip()
    pubdate = int(time.time())


# write data into database
WORKING_DIR = os.path.dirname(os.path.realpath(sys.argv[0]))
os.chdir(WORKING_DIR)

with open(DATABASE, 'a') as fd:
    writer = csv.writer(fd, **CSV_PARAMS)
    writer.writerow((title, body, url, pubdate))

print('DONE')
