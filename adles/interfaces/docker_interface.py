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
    import docker
except ImportError:
    logging.error("Could not import docker module. "
                  "Install it using 'pip install docker'")
    exit(0)

import adles.utils as utils
from adles.interfaces import Interface


class DockerInterface(Interface):
    """ Generic interface for the Docker platform """

    __version__ = "0.2.1"

    # noinspection PyMissingConstructor
    def __init__(self, infra, spec):
        """
        :param dict infra: Dict of infrastructure information
        :param dict spec: Dict of a parsed specification
        """
        self._log = logging.getLogger('DockerInterface')
        self._log.debug("Initializing DockerInterface %s",
                        DockerInterface.__version__)

        self.infra = infra
        self.spec = spec
        self.metadata = spec["metadata"]
        self.services = spec["services"]
        self.networks = spec["networks"]
        self.folders = spec["folders"]

        # If needed, a wrapper class that simplifies
        # the creation of containers will be made
        # Reference:
        # https://docker-py.readthedocs.io/en/stable/client.html#client-reference
        # Initialize the Docker client
        self.client = docker.DockerClient(base_url=infra.get("url",
                                                             "unix:///var/run/"
                                                             "docker.sock"),
                                          tls=bool(infra.get("tls", True)))

        # Verify the connection to the client
        self.client.ping()

        self._log.debug("System info      : %s", str(self.client.info()))
        self._log.debug("System version   : %s", str(self.client.version()))

        # Authenticate to registry, if configured
        if "registry" in self.infra:
            reg = self.infra["registry"]
            reg_logins = utils.read_json(reg["login-file"])
            self.client.login(username=reg_logins["user"],
                              password=reg_logins["pass"],
                              registry=reg["url"])

        # List images currently on the server
        self._log.debug("Images: %s", str(self.client.images.list()))

    def create_masters(self):
        pass

    def deploy_environment(self):
        pass

    def cleanup_masters(self, network_cleanup=False):
        pass

    def cleanup_environment(self, network_cleanup=False):
        pass

    def __str__(self):
        return str(self.client.info() + "\nVersion:\t" + self.client.version())

    def __eq__(self, other):
        return super(DockerInterface, self).__eq__(other) \
               and self.client == other.client
