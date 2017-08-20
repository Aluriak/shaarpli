"""Encapsulation of the page retrieving.

Allow caching.

"""


from itertools import islice
from functools import lru_cache

import cachetools

from shaarpli import data
from shaarpli import cache as cache_module
from shaarpli import config as config_module
from shaarpli import template
from shaarpli.commons import Link


REDIRECTION = '<meta http-equiv="refresh" content="0; url={}" />'


def page_for(env) -> str:
    """API entry point. Wait for CGI environnement"""
    # parse env and get static data
    config, cached_page_generator, db = load_static()
    parameters = uri_parameters(env['REQUEST_URI'])
    parameter = parameters[0] if len(parameters) > 0 else '1'

    # cache status request
    if parameter == 'cache':
        return cached_page_generator.cache.html_repr()

    # At this point, parameters are invalid: replace them with default.
    parameters = ()

    # create default data if none available
    if db.empty():
        data.create_default_database(db.name)

    # move the next link if needed
    db.move_entry_if_expected()

    # other cases: show links
    try:
        page_number = int(parameter)
    except ValueError:
        page_number = 1

    # requesting for non-published links
    if page_number <= 0:
        return '<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/Back-to-the-future-logo.svg/2000px-Back-to-the-future-logo.svg.png" alt="back to the future">'

    # cache invalidation if data changed
    if db.out_of_date():
        cached_page_generator.cache_clear()

    # return the requested page
    return cached_page_generator(page_number, config, db)


def page_generator(page_number:int, config, db) -> str:
    """Return the html content of the page of given number.

    page_number -- integer >= 1 giving the page requested by client
    config  -- namedtuple like object giving configuration
    db -- the database of links

    """
    nb_link_per_page = int(config.html.link_per_page)
    page_of_link = lambda n: (n // nb_link_per_page) + 1  # link idx -> page number
    links = iter(db.links)
    next_links = lambda: islice(links, 0, nb_link_per_page)

    # explore the links before those in requested page
    page = 0  # fallback if page_number is 1
    for page in range(1, page_number):
        nb_link = sum(1 for link in next_links())
        # redirect user if not enough links to continue
        if nb_link < nb_link_per_page:
            return redirection(config)

    # now the *nb_link_per_page* next links must be rendered in the requested page
    assert page == page_number - 1, "the last treated page is not just before the requested one"
    return template.render_full_page(config, page_number, next_links())


def redirection(config) -> str:
    return REDIRECTION.format(config.server.url)


def uri_parameters(uri) -> str:
    """Return parameter in URI

    >>> uri_parameters('/links')
    ()
    >>> uri_parameters('/links/')
    ()
    >>> uri_parameters('/links/4')
    ('4',)
    >>> uri_parameters('/links/page/4')
    ('page', '4')

    """
    return tuple(uri.strip('/').split('/')[1:])


@lru_cache(maxsize=1)
def load_static() -> (tuple, callable, data.DatabaseHandler):
    """Return all data that don't change between two call:

    Returns:
        config -- a config namedtuple (see config.py)
        page_generator -- a wrapper around the `page_generator` function
        db -- a data.DatabaseHandler instance

    Without its lru_cache, this function can't assure the caching
    of page generation (because creating a cached access to page generator
    at each call).
    Calling load_static.cache_clear will delete all cache,
    and lead to the reparsing of config data.

    """
    cfg = config_module.get()
    db = data.HandlerAggregator(cfg)

    # caching
    if cfg.server.cache_size and int(cfg.server.cache_size) > 0:
        # this cache only consider the page number among
        #  the parameters of page_generator
        wrapper_key = lambda page, config, db: cachetools.keys.hashkey(page)
        cache = cache_module.SLFUCache(int(cfg.server.cache_size))
        wrapper = cachetools.cached(cache=cache, key=wrapper_key)
                                    # maxsize=int(cfg.server.cache_size))

        cached_page_generator = wrapper(page_generator)
        cached_page_generator.cache = cache
    else:
        cached_page_generator = page_generator
        cached_page_generator.cache = None

    return cfg, cached_page_generator, db
