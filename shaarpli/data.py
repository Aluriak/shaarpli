"""Wrapper around the database handling, and around the database handler.

Database would be stored in DSV using standard delimiter,
so chances are you would never need to escape anything in your text.
However, because of csv limitation on record separator (only \\n
and \\r are valid, and synonymous), this perfect case can't be used.
Solution: assume that fields are enclosed in double quotes.

See https://en.wikipedia.org/wiki/Delimiter#ASCII_delimited_text


DatabaseHandler allow one to manipulate database itself.

HandlerAggregator allow one to manage DatabaseHandler at very high level,
and implements the autopublish funtionnality.

"""


import os
import csv
import time
import itertools
import functools


MEMORY_WISE = True  # define the method used to add links into database
DSV_FIELD_SEP = chr(31)
DSV_RECORD_SEP = chr(30)
CSV_PARAMS = {
    'delimiter': DSV_FIELD_SEP,
    # 'lineterminator': DSV_RECORD_SEP,  # NOT HANDLED BY PYTHON. NOT A JOKE. WTF PYTHON.
    'lineterminator': '\n',
}
TIME_EQUIVALENCE = {  # terms available for autopublish.every
    'minute': 60,
    'hour': 60*60,
    'day': 60*60*24,
    'week': 60*60*24*7,
    'year': 60*60*24*7*365
}


def add(title, desc, url, database:str):
    """Prepend given entry (title, desc, url) to given file"""
    lines = (title, desc, url),
    extend(lines, database=database)


def extend_memwise(lines:iter, database:str):
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

def extend_timewise(lines:iter, database:str):
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

def extend_append(lines:iter, database:str):
    """Append entries (title, desc, url) in given lines to given file

    This implementation simply push the data at the end of the file.
    Should not be used as main database, unless you want the last link added
    to be the last link on the last page.

    """
    with open(database, 'a') as fd:
        writer = csv.writer(fd, **CSV_PARAMS)
        for title, desc, url in lines:
            writer.writerow([title, desc, url])

# this choice should be made through a config file parameter
extend = extend_memwise if MEMORY_WISE else extend_timewise


def create_default_database(database:str):
    """Add default database : some example links for new users"""
    extend((
        ('first link', 'is also the first  \n in database\n\n- a\n- b\n- c', 'http://github.com/aluriak/shaarpli'),
        ('second link', 'is also the last\n in database', 'http://github.com/aluriak/shaarpli'),
    ), database=database)


class DatabaseHandler:
    """Access to database.

    Provides high-level methods allowing to probe database state,
    and to add data.

    Is also iterable over the data as 3-uplet (title, description, link).

    """

    def __init__(self, filename:str, extend_func:callable=extend) -> iter:
        self.name = filename
        assert self.exists()
        self.last_access_time = time.time()
        self._nb_link = None
        self.extend = functools.partial(extend_func, database=self.name)

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


class HandlerAggregator:
    """Aggregation of at most 2 DatabaseHandler,
    with full responsibility over it.

    One handler is the *source*, and the other the *target*.
    (the source one is optional since the autopublish feature is not
    necessarily activated)

    An aggregator can:
    - create handlers, based on a configuration (see config.py)
    - move one entry from source to target
    - detect, according to configuration, if a move must be performed
    - behave like the target DatabaseHandler, with consideration of the source if any

    """

    def __init__(self, config):
        self._config = config
        self.source = None
        self.target_file = config.database.filepath
        self.target = DatabaseHandler(
            self.target_file,
            extend_func=extend_memwise if config.database.memory_wise else extend_timewise
        )
        if config.autopublish.active:
            self.source = DatabaseHandler(
                self.source_file,
                extend_func=extend_append
            )
            self._source_entry_offset = 0
            self.source_file = config.autopublish.filepath
            self._max_source_offset = config.autopublish.maximal_data_duplication
            self._last_move = time.time()

    @property
    def hassource(self) -> bool: return bool(self.source)
    @property
    def handler(self) -> DatabaseHandler: return self.target

    def _move_expected(self) -> bool:
        """True iff an entry move is needed, according to configuration"""
        if config.autopublish.active:
            if isinstance(config.autopublish.every, int):
                minimal_wait_time = config.autopublish.every
            else:
                # TODO: handle key lookup fail
                if config.autopublish.every not in TIME_EQUIVALENCE:
                    print('ERROR: config.autopublish.every ({}) is not a valid time.'
                          'Expect an integer or one of {}.'
                          ''.format(config.autopublish.every,
                                    ', '.join(TIME_EQUIVALENCE)))
                    return False
                minimal_wait_time = TIME_EQUIVALENCE[config.autopublish.every]
            real_wait_time = time.time() - self._last_move
            return real_wait_time >= minimal_wait_time
        else:  # no autopublish
            return False

    def _iter_source(self, nb:int=None) -> iter:
        """Return a function source->lines, that yield nb lines of given source,
        skipping entries according to the offset"""
        first_entry_index = self._source_entry_offset
        last_entry_index = (self._source_entry_offset + nb) if nb else None
        return functools.partial(
            itertools.islice, first_entry_index, last_entry_index
        )

    def move_entry(self, nb:int=1):
        """Move *nb* entry from source handler to target handler"""
        assert self.hassource, "HandlerAggregator needs a source to move entries"
        # NB: Source handler adds the new entries at the end of the file.
        #  Consequently, entries extracted from source are in increasing order
        #  of age. While the target database is in decreasing order of age
        #  (most recent first).
        #  Therefore, the extracted entries must be inserted in reverse order.
        entries = reversed(tuple(self._iter_source(nb)(self.source)))
        self.target.extend(entries)
        if self._source_entry_offset > self._max_source_offset:
            self.clean_source()
        self._last_move = time.time()

    def clean_source(self):
        """Delete entries in source database that are skipped because of the
        entry offset.

        Calling this method at each entry move can be costly,
        so better call it when the offset is large.

        As long as offset is not zero, there is data duplication between
        the source and the target.
        (since the entry skipped by the offset are the entries already
        moved to target handler)

        """
        if self._source_entry_offset <= 0:
            self._source_entry_offset = 0
            return
        # non-zero offset
        database = self.source.name
        db_bak = database + '.bak'  # intermediate file containing previous entries
        os.rename(database, db_bak)
        # write new data in newly created file
        with open(database, 'w') as fd, open(db_bak) as prev_entries:
            writer = csv.writer(fd, **CSV_PARAMS)
            reader = csv.reader(prev_entries, **CSV_PARAMS)
            for title, desc, url in self._iter_source(None)(reader):
                writer.writerow([title, desc, url])
        os.remove(db_bak)


    def move_entry_if_expected(self):
        """If a move is expected according to configuration, then perform
        the move"""
        if self._move_expected():
            self.move_entry(nb=config.autopublish.link_per_publication)


    # Follows functions allowing HandlerAggregator to behave
    #  like the target DatabaseHandler

    def empty(self) -> bool:
        """True if both source and target are empty"""
        return self.target.empty() and (not self.source or self.source.empty())

    def out_of_date(self) -> bool:
        """Proxy of target DatabaseHandler"""
        return self.target.out_of_date()

    @property
    def name(self) -> str:
        """Proxy of target DatabaseHandler"""
        return self.target.name

    @property
    def links(self) -> iter:
        """Proxy of target DatabaseHandler"""
        return self.target.links

    @property
    def nb_link(self) -> iter:
        """Proxy of target DatabaseHandler"""
        return self.target.nb_link

