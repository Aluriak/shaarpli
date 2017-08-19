"""Encapsulation of the page retrieving.

Allow caching.

"""


import threading
from itertools import islice
from functools import lru_cache
from urllib.parse import urlparse

from . import data
from . import config as config_module
from . import template


REDIRECTION = '<meta http-equiv="refresh" content="0; url={}" />'


def page_for(env) -> str:
    """API entry point. Wait for CGI environnement"""
    # parse env and get static data
    config, cached_page_generator, db = load_static()
    parameter = uri_parameter(env)

    # cache status request
    if parameter == 'cache':
        return str(cached_page_generator.cache_info())

    # other cases: show links
    page_number = 1
    if parameter.isnumeric():
        page_number = max(1, int(parameter))
    return generated_page(page_number, config, cached_page_generator, db)


def generated_page(page_number:int, config, cached_page_generator, db) -> str:
    if db.out_of_date():
        cached_page_generator.cache_clear()
    nb_link = int(db.nb_link or config.html.link_per_page)
    if nb_link // int(config.html.link_per_page) >= page_number - 1:
        return cached_page_generator(page_number, config, db)
    else:  # not enough links to be readed
        return redirection(config)


def redirection(config) -> str:
    return REDIRECTION.format(config.server.url)


def page_generator(page_number:int, config:dict, db:data.Reader) -> str:
    """Return the page after templating.

    page_number -- integer >= 1 giving the page requested by client
    config  -- namedtuple like object giving configuration
    db -- a data.Reader instance

    """
    link_per_page = int(config.html.link_per_page)
    if not db.exists():
        data.create_default_database()
    start = (page_number-1) * link_per_page
    db_reader = islice(db.links, start, start + link_per_page)
    return template.render_full_page(config, page_number, db_reader)


def uri_parameter(env) -> str:
    """Return parameter in URI

    >>> uri_parameter('/links')
    ''
    >>> uri_parameter('/links/')
    ''
    >>> uri_parameter('/links/4')
    '4'

    """
    url = env['REQUEST_URI']
    if '/' in url.lstrip('/'):
        return url[url.rfind('/')+1:]
    else:
        return ''


@lru_cache(maxsize=1)
def load_static() -> (tuple, callable, data.Reader):
    """Return all data that don't change between two call:

    Returns:
        config -- a config namedtuple (see config.py)
        page_generator -- a wrapper around the `page` function
        db -- a data.Reader instance

    Without its lru_cache, this function can't assure the caching
    of page generation (because creating a cached access to page generator
    at each call).
    Calling load_static.cache_clear will delete all cache,
    and lead to the reparsing of config data.

    """
    cfg = config_module.get()
    db = data.Reader(cfg.database.filepath)

    # caching
    if cfg.server.cache_size and int(cfg.server.cache_size) > 0:
        wrapper = lru_cache(maxsize=int(cfg.server.cache_size))
        cached_page_generator = wrapper(page_generator)
    else:
        cached_page_generator = page_generator

    return cfg, cached_page_generator, db
