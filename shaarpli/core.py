"""Encapsulation of the page retrieving.

Allow caching.

"""

from itertools import islice

from shaarpli import data as data_module
from shaarpli import config as config_module
from shaarpli import template
from shaarpli.commons import Link


REDIRECTION = '<meta http-equiv="refresh" content="0; url={}" />'
UNIQID = 0

# GLOBAL DATA (conserved between two calls)
PAGES = {}
RENDERING = {}
CONFIG = config_module.get()
DB = data_module.HandlerAggregator(CONFIG)
LAST_LINK_RENDERED = None


def page_for(env) -> str:
    """API entry point. Wait for CGI environnement.

    Returns the html string to show to end-user.

    """
    # parse env and get static data
    global PAGES, RENDERING
    parameters = uri_parameters(env['REQUEST_URI'])
    parameter = parameters[0] if len(parameters) > 0 else '1'

    global UNIQID
    if parameter == 'stack':
        for _ in range(int(parameters[1]) if len(parameters) > 1 else 1):
            UNIQID += 1
            DB.publish_later([Link(*([str(UNIQID)] * 4))])
        return str(UNIQID)
    if parameter == 'push':
        for _ in range(int(parameters[1]) if len(parameters) > 1 else 1):
            UNIQID += 1
            DB.publish([Link(*([str(UNIQID)] * 4))])
        return str(UNIQID)
    if parameter == 'move':
        DB.move_entry(int(parameters[1]) if len(parameters) > 1 else 1)
        return str(UNIQID)
    if parameter == 'print':
        return '\n<hr>\n'.join(map(str, DB.links))

    # At this point, parameters are invalid: replace them with default.
    parameters = ()

    # create default data if none available
    if DB.empty():
        data_module.create_default_database(DB.name)

    # move the next link if needed
    DB.move_entry_if_expected()

    # other cases: parameter is the page number
    try:
        page_number = int(parameter)
    except ValueError:
        page_number = 1

    # requesting for non-published links
    if page_number <= 0:
        return '<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/Back-to-the-future-logo.svg/2000px-Back-to-the-future-logo.svg.png" alt="back to the future">'

    # cache invalidation if data changed
    last_link_rendered = PAGES[1][0] if 1 in PAGES else None
    if last_link_rendered and DB.out_of_date(last_link_rendered):
        print('DB OUT OF DATE')
        PAGES, RENDERING = {}, {}

    # render the page, or get a redirection to the base site
    render_page(page_number, CONFIG, DB)
    html = RENDERING.get(page_number, redirection(CONFIG))

    # handle the cache size
    if int(CONFIG.server.cache_size) <= 0:
        PAGES, RENDERING = {}, {}
    else:
        while len(RENDERING) > int(CONFIG.server.cache_size):
            del RENDERING[max(RENDERING.keys())]
        while len(PAGES) > int(CONFIG.server.cache_size):
            del PAGES[max(PAGES.keys())]

    # send the html to end-user
    return html


def create_page(nb:int, config, db):
    """Create pages from first to nb. Populate PAGES."""
    global PAGES
    assert nb > 0
    if nb in PAGES: return  # no page need to be created

    nb_link_per_page = int(config.html.link_per_page)
    links = iter(db.links)
    next_links = lambda: islice(links, 0, nb_link_per_page)

    for page_number in range(1, nb + 1):
        if page_number in PAGES:  # page already generated
            nb_link = sum(1 for link in next_links())
        else:  # page not generated
            all_link = tuple(next_links())
            nb_link = len(all_link)
            PAGES[page_number] = all_link
        if nb_link < nb_link_per_page:
            return  # not enough links to feed the next page


def render_page(nb:int, config, db):
    """Compute the html version of given page, populating RENDERING.

    If the page do not exists, it will create it first with create_page function.

    """
    if nb in RENDERING: return  # already rendered
    create_page(nb, config, db)
    if nb not in PAGES: return  # not created because too few links
    # the page exists, so the rendering is possible
    RENDERING[nb] = template.render_full_page(config, nb, PAGES[nb])


def redirection(config) -> str:
    """Return an html code that redirect to the base url of the website"""
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
