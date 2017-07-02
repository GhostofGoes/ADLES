# -*- coding: utf-8 -*-

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
except ImportError:
    logging.error("Could not import apache-libcloud. "
                  "Install it using 'pip install apache-libcloud'")
    exit(0)

import adles.utils as utils
from adles.interfaces import Interface


class CloudInterface(Interface):
    """ Generic interface for all cloud platforms. """

    __version__ = "0.1.0"

    # noinspection PyMissingConstructor
    def __init__(self, infra, spec):
        """
        :param dict infra: Dict of infrastructure information
        :param dict spec: Dict of a parsed specification
        """
        self._log = logging.getLogger('CloudInterface')
        self._log.debug("Initializing CloudInterface %s",
                        CloudInterface.__version__)

        # Keys will be as specified for "Cloud" in infrastructure specification
        self.infra = infra
        self.spec = spec
        self.metadata = spec["metadata"]
        self.services = spec["services"]
        self.networks = spec["networks"]
        self.folders = spec["folders"]

        # TODO: temporary for testing
        self.username = "test"
        self.api_key = "lol"

        # TODO: temporary for testing
        # provider_name = self.infra["cloud-provider"]
        self.provider_name = "EC2"

        driver = get_driver(getattr(Provider, self.provider_name))
        cloud = driver(user_id=self.username, key=self.api_key)

        self._log.debug(cloud.list_images())
        self._log.debug(cloud.list_sizes())

    def create_masters(self):
        pass

    def deploy_environment(self):
        pass

    def cleanup_masters(self, network_cleanup=False):
        pass

    def cleanup_environment(self, network_cleanup=False):
        pass

    def __str__(self):
        return str(self.provider_name)

    def __eq__(self, other):
        return super(CloudInterface, self).__eq__(other) \
               and self.provider_name == other.provider_name \
               and self.username == other.username \
               and self.api_key == other.api_key
