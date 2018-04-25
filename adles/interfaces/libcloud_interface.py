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

try:
    from libcloud.compute.types import Provider
    from libcloud.compute.providers import get_driver
except ImportError as ex:
    logging.error("Could not import apache-libcloud. "
                  "Install it using 'pip install apache-libcloud'")

from adles.interfaces import Interface


class LibcloudInterface(Interface):
    """Base class for all interfaces that use Apache libcloud."""
    __version__ = "0.1.0"

    # noinspection PyMissingConstructor
    def __init__(self, infra, spec, provider_name=None):
        """
        :param dict infra: Dict of infrastructure information
        :param dict spec: Dict of a parsed specification
        :param str provider_name: Name of provider, if not in "provider" key
        """
        super(self.__class__, self).__init__(infra=infra, spec=spec)
        self._log = logging.getLogger(str(self.__class__))
        self._log.debug("Initializing %s %s", self.__class__, self.__version__)

        # Used for interfaces such as libvirt
        if provider_name is None:
            self.provider_name = self.infra["provider"]
        else:
            self.provider_name = provider_name
        self.driver = get_driver(getattr(Provider, self.provider_name))

        # TODO: temporary for testing
        self.username = "test"
        self.api_key = "key"
        self.provider = self.driver(user_id=self.username, key=self.api_key)
