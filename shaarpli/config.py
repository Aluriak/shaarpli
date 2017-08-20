"""Wrapper around configuration access.

Config is expected to be in config.ini file.

"""


import configparser
from collections import namedtuple


CONFIG_FILE = 'data/config.ini'
DEFAULT_CONFIG = """\
[server]
url = localhost
cache_size = 128
cache_link = true

[html]
link_per_page = 10
title = shaarpli
additional_header =
additional_footer =

[template]
link = templates/link.mkd
page = templates/page.mkd
link_separator = templates/link_separator.mkd

[database]
filepath = data/data.csv
loopkup_timestamp = 1
memory_wise = true

[autopublish]
active = false
filepath = data/topublish.csv
every = day
link_per_publication = 1
"""


def as_namedtuple(config:configparser.ConfigParser) -> namedtuple:
    def namedtuple_of_section(section):
        """Return namedtuple containing fields and their values
        for given section"""
        options = dict(config.items(section))
        return namedtuple(section.lower(), options.keys())(**options)
    sections = {section: namedtuple_of_section(section)
                for section in config.sections()}
    return namedtuple('Config', sections.keys())(**sections)


def get() -> namedtuple:
    """Return a namedtuple of configuration"""
    config = configparser.ConfigParser()
    config.read_string(DEFAULT_CONFIG)
    # TODO: enforce that config file do not add options or sections over
    #  the default config (to avoid badly named options to lead dev to despair)
    config.read(CONFIG_FILE)  # override
    return as_namedtuple(config)
