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

from .commons import Link, file_content


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


def add(link:Link, database:str):
    """Prepend given entry (title, desc, url) to given file"""
    lines = link,
    extend(lines, database=database)


def extend_memwise(links:iter, database:str):
    """Prepend Link instances to given file

    This implementation is memory-wise : it uses an intermediate file to avoid
    loading the full data in memory.
    (so it is, consequently, potentially slow)

    """
    db_bak = database + '.bak'  # intermediate file containing previous entries
    os.rename(database, db_bak)
    # write new data in newly created file
    with open(database, 'w') as fd:
        writer = csv.writer(fd, **CSV_PARAMS)
        for link in links:
            writer.writerow([*link])
        with open(db_bak) as prev_entries:
            reader = csv.reader(prev_entries, **CSV_PARAMS)
            for entry in reader:
                writer.writerow(entry)
    os.remove(db_bak)

def extend_timewise(links:iter, database:str):
    """Prepend Link instances to given file

    This implementation is time-wise : it loads the full file in memory
    in order to easily add the new data, then append the previous data.
    (so it is, consequently, potentially hard on memory)

    """
    with open(database) as fd:
        prev_entries = fd.read()
    with open(database, 'w') as fd:
        writer = csv.writer(fd, **CSV_PARAMS)
        for link in links:
            writer.writerow([*link])
        fd.write(prev_entries)

def extend_append(links:iter, database:str):
    """Append Link instances to given file

    This implementation simply push the data at the end of the file.
    Should not be used as main database, unless you want the last link added
    to be the last link on the last page.

    """
    with open(database, 'a') as fd:
        writer = csv.writer(fd, **CSV_PARAMS)
        for link in links:
            writer.writerow([*link])

# this choice should be made through a config file parameter
extend = extend_memwise if MEMORY_WISE else extend_timewise


def create_default_database(database:str):
    """Add default database : some example links for new users"""
    extend((
        ('second link', 'is also the last\n in database', 'http://github.com/aluriak/shaarpli', time.time()),
        ('first link', 'is also the first  \n in database\n\n- a\n- b\n- c', 'http://github.com/aluriak/shaarpli', time.time() - 25*3600),
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
        self._compute_nb_link()
        self.extend = functools.partial(extend_func, database=self.name)

    def _compute_nb_link(self):
        self._nb_link = sum(1 for c in open(self.name) if c == DSV_RECORD_SEP)


    @property
    def links(self):
        return iter(self)

    @property
    def nb_link(self):
        return self._nb_link

    def __iter__(self):
        self.last_access_time = time.time()
        with open(self.name) as fd:
            reader = csv.reader(fd, **CSV_PARAMS)
            for idx, line in enumerate(reader, start=1):
                self._nb_link = max(self._nb_link, idx)
                try:
                    yield Link.from_dsv(line)
                except ValueError as e:  # unpack
                    print('ValueError:', e)
                    print(line)
                    print('This line will be ignored.')
                    continue


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
            self._compute_nb_link()
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
    - allow publishing (add to target) and publishing later (add to source)

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
            self.source_file = config.autopublish.filepath
            self.source = DatabaseHandler(
                self.source_file,
                extend_func=extend_append
            )


    def last_link(self) -> Link or None:
        """Return the last published link in target database, or None if no link
        in database."""
        try:
            return next(iter(self.target))
        except StopIteration:
            return None


    @property
    def hassource(self) -> bool: return bool(self.source)
    @property
    def handler(self) -> DatabaseHandler: return self.target

    def _move_expected(self) -> bool:
        """True iff an entry move is needed, according to configuration"""
        if config.autopublish.active:
            if self.last_link() is None:  # no initial publication
                return True
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
            real_wait_time = time.time() - self.last_link.publication_date
            return real_wait_time >= minimal_wait_time
        else:  # no autopublish
            return False

    def move_entry(self, nb:int=1):
        """Move *nb* entry from source handler to target handler"""
        assert self.hassource, "HandlerAggregator needs a source to move entries"
        # NB: Source handler adds the new entries at the end of the file.
        #  Consequently, entries extracted from source are in increasing order
        #  of age. While the target database is in decreasing order of age
        #  (most recent first).
        #  Therefore, the extracted entries must be inserted in reverse order.
        entries = reversed(tuple(itertools.islice(self.source, 0, nb)))
        self.publish(entries)
        self._clean_source(nb)

    def publish(self, links:iter):
        """Add given Link instances to the database (target handler)
        in given order.

        Will tell the links they are published.

        """
        links = tuple(links)
        for link in links:
            link.publish()
        self.target.extend(links)

    def publish_later(self, links:iter):
        """Add given Link instances to the unpublished database (source handler)
        in given order.

        """
        self.source.extend(links)

    def _clean_source(self, nb:int):
        """Remove the *nb* first entries from source database.

        Calling this method at each entry move can be costly.
        A system of offset on source was once implemented, but since
        the offset value was not saved between two runs of the codebase,
        it just leads to bugs.

        """
        database = self.source.name
        db_bak = database + '.bak'  # intermediate file containing previous entries
        os.rename(database, db_bak)
        # write new data in newly created file
        with open(database, 'w') as fd, open(db_bak) as prev_entries:
            writer = csv.writer(fd, **CSV_PARAMS)
            reader = csv.reader(prev_entries, **CSV_PARAMS)
            # ignore the first *nb* links
            for entry in itertools.islice(reader, nb, None):
                writer.writerow([*entry])
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

