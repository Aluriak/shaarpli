"""Wrapper around configuration access.

Config is expected to be in config.ini file.

"""


import configparser
from collections import namedtuple


CONFIG_FILE = 'data/config.ini'
DEFAULT_CONFIG = """
[server]
url = localhost
cache_size = 128
cache_link = true

[html]
link_per_page = 10
title = shaarpli
page_access = /{}

[database]
filepath = data/data.csv
loopkup_timestamp = 1
"""


def as_namedtuple(config:configparser.ConfigParser) -> namedtuple:
    fields, values = zip(*tuple(
        (section + '_' + option, value)
        for section in config.sections()
        for option, value in config.items(section)
    ))
    cls = namedtuple('Config', fields)
    return cls(*values)


def get() -> namedtuple:
    """Return a namedtuple of configuration"""
    config = configparser.ConfigParser()
    config.read_string(DEFAULT_CONFIG)
    config.read(CONFIG_FILE)  # override
    return as_namedtuple(config)
