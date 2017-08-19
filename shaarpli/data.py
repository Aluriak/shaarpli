"""Wrapper around the database call

Database would be stored in DSV using standard delimiter,
so chances are you would never need to escape anything in your text.
However, because of csv limitation on record separator (only \\n
and \\r are valid, and synonymous), this perfect case can't be used.
Solution: assume that fields are enclosed in double quotes.

See https://en.wikipedia.org/wiki/Delimiter#ASCII_delimited_text

"""


import os
import csv
import time


MEMORY_WISE = True  # define the method used to add links into database
DATABASE_FILE = 'data/data.csv'
DSV_FIELD_SEP = chr(31)
DSV_RECORD_SEP = chr(30)
CSV_PARAMS = {
    'delimiter': DSV_FIELD_SEP,
    # 'lineterminator': DSV_RECORD_SEP,  # NOT HANDLED BY PYTHON. NOT A JOKE. WTF PYTHON.
    'lineterminator': '\n',
}


def add(title, desc, url, *, database=DATABASE_FILE):
    """Prepend given entry (title, desc, url) to given file"""
    lines = (title, desc, url),
    extend(lines, database=database)


def extend_memwise(lines:iter, *, database=DATABASE_FILE):
    """Prepend entries (title, desc, url) in given lines to given file

    This implementation is memory-wise : it uses an intermediate file to avoid
    loading the full data in memory.
    (so it is, consequently, potentially slow)

    """
    db_bak = database + '.bak'  # intermediate file containing previous entries
    os.rename(database, db_bak)
    # write new data in newly created file
    with open(database, 'w') as fd:
        writer = csv.writer(fd, **CSV_PARAMS)
        for title, desc, url in lines:
            writer.writerow([title, desc, url])
        with open(db_bak) as prev_entries:
            reader = csv.reader(prev_entries, **CSV_PARAMS)
            for entry in reader:
                writer.writerow(entry)
    os.remove(db_bak)

def extend_timewise(lines:iter, *, database=DATABASE_FILE):
    """Prepend entries (title, desc, url) in given lines to given file

    This implementation is time-wise : it loads the full file in memory
    in order to easily add the new data, then append the previous data.
    (so it is, consequently, potentially hard on memory)

    """
    with open(database) as fd:
        prev_entries = fd.read()
    with open(database, 'w') as fd:
        writer = csv.writer(fd, **CSV_PARAMS)
        for title, desc, url in lines:
            writer.writerow([title, desc, url])
        fd.write(prev_entries)

# this choice should be made through a config file parameter
extend = extend_memwise if MEMORY_WISE else extend_timewise


def create_default_database(database=DATABASE_FILE):
    """Add default database : some example links for new users"""
    extend((
        ('first link', 'is also the first  \n in database\n\n- a\n- b\n- c', 'http://github.com/aluriak/shaarpli'),
        ('second link', 'is also the last\n in database', 'http://github.com/aluriak/shaarpli'),
    ), database=database)


class Reader:
    """Access to database in reading mode"""

    def __init__(self, filename=DATABASE_FILE) -> iter:
        """Yield tuple (title, description, url)"""
        self.name = filename
        self.last_access_time = time.time()
        self._nb_link = None
        assert self.exists()

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
        with open(self.name, 'a') as fd:
            pass
        try:
            return os.path.exists(self.name)
        except FileNotFoundError:
            return False

    def empty(self) -> bool:
        """True if databate contains nothing"""
        return not self.exists() or not open(self.name).read().strip()

    def out_of_date(self) -> bool:
        """True if database have changed since last access"""
        change_time = os.path.getmtime(self.name)
        assert isinstance(change_time, float)
        if change_time > self.last_access_time:
            self._nb_link = None
            return True
        return False
