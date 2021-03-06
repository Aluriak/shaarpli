"""Various definitions to be used accross the codebase.

"""


import time
import tempfile as tempfile_module


class Link():
    """A link with text, a title and publication date.
    """

    def __init__(self, title, description, url, publication_date):
        self._title = str(title)
        self._description = str(description)
        self._url = str(url)
        self._publication_date = int(float(publication_date))

    def __iter__(self):
        return iter((self._title, self._description,
                     self._url, self._publication_date))

    def publish(self):
        """Update publication_date to now"""
        self._publication_date = time.time()

    @staticmethod
    def from_dsv(line):
        return Link(*line)

    def to_dsv(self) -> tuple:
        return tuple(self)

    def asdict(self) -> dict:
        return {
            'title': self._title,
            'description': self._description,
            'url': self._url,
            'publication_date': self._publication_date,
        }

    @property
    def title(self) -> str: return self._title
    @property
    def description(self) -> str: return self._description
    @property
    def url(self) -> str: return self._url
    @property
    def publication_date(self) -> int: return self._publication_date

    def __str__(self):
        return '{}: {}: <a href="{}">{}</a><br>'.format(
            self.publication_date, self.title, self.url, self.description
        )


def file_content(filename:str, onfail='') -> str:
    """Return the content of given filename, or onfail
    if filename is not found."""
    try:
        with open(filename) as fd:
            content = fd.read()
    except FileNotFoundError:
        content = onfail
    return content


def tempfile() -> str:
    """Return the name of a writable temporary file"""
    return tempfile_module.NamedTemporaryFile(delete=False).name
