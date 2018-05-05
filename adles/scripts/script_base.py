# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import logging

from adles.__about__ import __url__, __email__


class Script(object):
    """Base class for all CLI scripts."""
    __version__ = '0.1.0'
    name = ''

    def __init__(self):
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

    def run(self, server):
        pass

    def __str__(self):
        return self.__doc__

    def __repr__(self):
        return self.name + ' ' + self.__version__

    def __hash__(self):
        return hash(self.name + self.__version__)

    def __eq__(self, other):
        return self.name == other.command \
               and self.__version__ == other.__version__

    def __ne__(self, other):
        return not self.__eq__(other)
