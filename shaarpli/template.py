"""Provides API for template generation"""


import markdown
from .commons import Link, file_content


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
{additional_header}
  
{body}

  
<hr>
{footer}
{additional_footer}
"""


def render_link(link:Link, template:str, *, as_html:bool=True) -> str:
    md = template.format(**link._asdict())
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
    links -- tuple of Link instances
    as_html -- return markdown if False, html if True

    """
    template_link = file_content(config.template.link, onfail=TEMPLATE_LINK)
    template_page = file_content(config.template.page, onfail=TEMPLATE_PAGE)
    template_link_sep = file_content(config.template.page, onfail=TEMPLATE_LINK_SEP)

    all_links = tuple(render_link(link, template_link, as_html=False) for link in links)
    merged_links = template_link_sep.join(all_links)

    md = template_page.format(
        title=config.html.title,
        body=merged_links,
        footer=footer(config, page_number, all_links),
        additional_header=file_content(config.html.additional_header),
        additional_footer=file_content(config.html.additional_footer),
    )
    print('Page {} generated with {} links.'.format(page_number, len(all_links)))
    return markdown.markdown(md) if as_html else md
