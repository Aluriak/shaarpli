"""Subclass of cachetools.LFUCache implementing a feedback solution.

"""

import collections
from cachetools import LFUCache


class SLFUCache(LFUCache):
    """Expose the cache, and provides high-level representation of data.

    - number of hit
    - number of miss
    - a barplot of the LFU (x: sorted keys of the dict ; y: number of access)

    """

    def __init__(self, maxsize:int):
        super().__init__(int(maxsize))

    def clear_cache(self):
        self.__data = {}
        self.__size = {}
        self.__counter = collections.Counter()
        self.__currsize = 0

    @property
    def counts(self) -> dict: return dict(self.__counter)

    def html_repr(self) -> str:
        return str({k: abs(v) for k, v in self._LFUCache__counter.items()})
