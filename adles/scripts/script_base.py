from abc import ABC, abstractmethod
from distutils.version import StrictVersion
import functools
import logging

from humanfriendly.prompts import prepare_friendly_prompts

from adles.__about__ import __url__, __email__


@functools.total_ordering
class Script(ABC):
    """Base class for all CLI scripts."""
    __version__ = '0.1.0'
    name = ''

    def __init__(self):
        prepare_friendly_prompts()  # Make input() more user friendly
        self._log = logging.getLogger(self.name)
        self._log.debug("Script name      %s", self.name)
        self._log.debug("Script version   %s", self.__version__)
        self._log.info(
            '\n***** YOU RUN THIS SCRIPT AT YOUR OWN RISK *****\n'
            '\n** Help and Documentation **'
            '\n+ "<script> --help": flags, arguments, and usage'
            '\n+ Read the latest documentation  : https://adles.readthedocs.io'
            '\n+ Open an issue on GitHub        : %s'
            '\n+ Email the script author        : %s'
            '\n', __url__, __email__)

    @classmethod
    def get_ver(cls):
        return cls.name.capitalize() + ' ' + cls.__version__

    @abstractmethod
    def run(self):
        pass

    def __str__(self):
        return self.__doc__

    def __repr__(self):
        return self.get_ver()

    def __hash__(self):
        return hash(repr(self))

    def __eq__(self, other):
        return self.name == other.name \
               and self.__version__ == other.__version__

    def __gt__(self, other):
        return StrictVersion(self.__version__) > StrictVersion(other.__version__)
