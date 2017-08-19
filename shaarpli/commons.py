"""Various definitions to be used accross the codebase.

"""


from collections import namedtuple


Link = namedtuple('Link', 'title, description, url, publication_date')


def file_content(filename:str, onfail='') -> str:
    """Return the content of given filename, or onfail
    if filename is not found."""
    try:
        with open(filename) as fd:
            content = fd.read()
    except FileNotFoundError:
        content = onfail
    return content
