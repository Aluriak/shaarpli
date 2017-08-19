"""Wrapper around the database call

Database in stored in DSV using standard delimiter,
so chances are you never need to espace anything in your text.

See https://en.wikipedia.org/wiki/Delimiter#ASCII_delimited_text

"""


import os
import csv
import time


DATABASE_FILE = 'data/data.csv'
DSV_FIELD_SEP = chr(31)
DSV_RECORD_SEP = chr(30)
CSV_PARAMS = {
    'quoting': csv.QUOTE_NONE,
    'delimiter': DSV_FIELD_SEP,
    'lineterminator': DSV_RECORD_SEP
}


def add(title, desc, url, *, database=DATABASE_FILE):
    """Add given (title, desc, url) to given file"""
    with open(database, 'a') as fd:
        writer = csv.writer(fd, **CSV_PARAMS)
        writer.writerow([title, desc, url])


def extend(lines:iter, *, database=DATABASE_FILE):
    """Add (title, desc, url) in given iterable to given file"""
    with open(database, 'a') as fd:
        writer = csv.writer(fd, **CSV_PARAMS)
        for title, desc, url in lines:
            writer.writerow([title, desc, url])


def create_default_database(database=DATABASE_FILE):
    """Add default database : some example links for new users"""
    extend((
        ('first link', 'is also the first in database', 'http://github.com/aluriak/shaarpli'),
        ('second link', 'is also the last in database', 'http://github.com/aluriak/shaarpli'),
    ), database=database)


class Reader:
    """Access to database in reading mode"""

    def __init__(self, filename=DATABASE_FILE) -> iter:
        """Yield tuple (title, description, url)"""
        self.name = filename
        self.last_access_time = time.time()
        self._nb_link = None

    @property
    def links(self):
        return iter(self)

    @property
    def nb_link(self):
        if self._nb_link is None:
            self._nb_link = len(tuple(c for c in open(self.name)
                                      if c == DSV_RECORD_SEP))
        return self._nb_link

    def __iter__(self):
        self.last_access_time = time.time()
        with open(self.name) as fd:
            reader = csv.reader(fd, **CSV_PARAMS)
            for idx, line in enumerate(reader, start=1):
                self._nb_link = max(self._nb_link, idx)
                try:
                    title, desc, url = line
                except ValueError as e:  # unpack
                    print('ValueError:', e)
                    print(line.split(DSV_FIELD_SEP))
                    print('This line will be ignored.')
                    continue
                yield title, desc, url


    def exists(self) -> bool:
        """True if databate contains something"""
        return os.path.exists(self.name) and open(self.name).read().strip()

    def out_of_date(self) -> bool:
        """True if database have changed since last access"""
        change_time = os.path.getmtime(self.name)
        assert isinstance(change_time, float)
        if change_time > self.last_access_time:
            self._nb_link = None
            return True
        return False
