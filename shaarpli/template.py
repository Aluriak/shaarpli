"""Provides API for template generation"""


import markdown


TEMPLATE_LINK = """
## [{title}]({url})
{desc}
"""
TEMPLATE_PAGE = """
# {title}
  
{body}

  
<hr>
{footer}
{additional_footer}
"""


def render_link(title, desc, url, *, as_html:bool=True) -> str:
    md = TEMPLATE_LINK.format(url=url, title=title, desc=desc)
    return markdown.markdown(md) if as_html else md


def footer(config, page_number, links) -> str:
    base_url, page_access = config.server.url, config.server.page_access
    prev_page, next_page = page_number - 1, page_number + 1
    link_prev = page_access.format(prev_page) if prev_page > 0 else ''
    link_next = page_access.format(next_page) if next_page > 0 else ''
    footer = ''
    if prev_page > 0:
        footer += '[prev]({})'.format(base_url + link_prev)
    if next_page > 0 and len(links) == int(config.html.link_per_page):
        footer += (' || ' if prev_page > 0 else '')
        footer += '[next]({})'.format(base_url + link_next)
    return footer


def render_full_page(config, page_number:int, links:tuple, *, as_html:bool=True) -> str:
    """Full page in html (or markdown if not as_html).

    config -- a namedtuple containing the configuration (see config.py)
    page_number -- integer >= 1 giving the page number
    links -- tuple of (title, desc, url)
    as_html -- return markdown if False, html if True

    """
    title = config.html.title
    all_links = tuple(render_link(*args, as_html=False) for args in links)
    nb_links = len(all_links)
    merged_links = '\n<hr>\n'.join(all_links)

    additional_footer = ''
    if config.html.additional_footer:
        with open(config.html.additional_footer) as fd:
            additional_footer = fd.read()

    md = TEMPLATE_PAGE.format(
        title=title,
        body=merged_links,
        footer=footer(config, page_number, all_links),
        additional_footer=additional_footer,
    )
    print('Page {} generated with {} links.'.format(page_number, nb_links))
    return markdown.markdown(md) if as_html else md
