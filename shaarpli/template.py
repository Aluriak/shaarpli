"""Provides API for template generation"""


import time

import markdown
from shaarpli.commons import Link, file_content


TEMPLATE_LINK = """
## [{title}]({url})
{publication_date}  
{description}
"""
TEMPLATE_LINK_SEP = """
<hr>
"""
TEMPLATE_PAGE = """
# {title}
> {subtitle}
{additional_header}
  
{body}

  
<hr>
{footer}
{additional_footer}
"""


def render_link(link:Link, template:str, config) -> str:
    """Render a single link in markdown"""
    fields = link.asdict()
    t = time.localtime(fields['publication_date'])
    if config.template.time_format:
        fields['publication_date'] = time.strftime(config.template.time_format, t)
    else:  # no time format -> user do not want time
        fields['publication_date'] = ''
    return template.format(**fields)


def footer(config, page_number, links) -> str:
    """Build and return the footer in markdown"""
    base_url = config.server.url
    prev_page, next_page = page_number - 1, page_number + 1
    link_prev = '/{}'.format(prev_page) if prev_page > 0 else ''
    link_next = '/{}'.format(next_page) if next_page > 0 else ''
    footer = ''
    if prev_page > 0:
        footer += '[prev]({})'.format(base_url + link_prev)
    if next_page > 0 and len(links) == int(config.html.link_per_page):
        footer += (' || ' if prev_page > 0 else '')
        footer += '[next]({})'.format(base_url + link_next)
    return footer


def subtitle(config, db) -> str:
    """Build and return the subtitle defined in config file"""
    if not config.autopublish.active:
        message = config.autopublish.message_noautopublish
    else:
        unpub = db.nb_unpublished_links()
        if unpub >= 2:
            message = config.autopublish.message_2
        elif unpub == 1:
            message = config.autopublish.message_1
        elif unpub == 0:
            message = config.autopublish.message_0
    try:
        every = int(config.autopublish.every)
    except ValueError:
        every = config.autopublish.every
    else:
        every = '{} second'.format(every) + ('s' if every > 1 else '')
    return message.format(remaining=unpub, every=every)


def render_full_page(config, page_number:int, links:tuple, db,
                     *, as_html:bool=True) -> str:
    """Full page in html (or markdown if not as_html).

    config -- a namedtuple containing the configuration (see config.py)
    page_number -- integer >= 1 giving the page number
    links -- tuple of Link instances
    as_html -- return markdown if False, html if True

    """
    template_link = file_content(config.template.link, onfail=TEMPLATE_LINK)
    template_page = file_content(config.template.page, onfail=TEMPLATE_PAGE)
    template_link_sep = file_content(config.template.page, onfail=TEMPLATE_LINK_SEP)

    all_links = tuple(render_link(link, template_link, config) for link in links)
    merged_links = template_link_sep.join(all_links)

    md = template_page.format(
        title=config.html.title,
        body=merged_links,
        footer=footer(config, page_number, all_links),
        additional_header=file_content(config.html.additional_header),
        additional_footer=file_content(config.html.additional_footer),
        subtitle=subtitle(config, db),
    )
    print('Page {} generated with {} links.'.format(page_number, len(all_links)))
    return markdown.markdown(md) if as_html else md
