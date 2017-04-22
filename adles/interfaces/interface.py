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

from adles.utils import time_execution


# TODO: subclass this for platform-specific interfaces
class Interface:
    """ Generic interface used to uniformly interact with platform-specific interfaces. """

    __version__ = "1.0.1"  # This should match version of infrastructure-specification.yaml

    def __init__(self, spec, infra):
        """ 
        :param spec: Full exercise specification
        :param infra: Full infrastructure configuration
        """
        self._log = logging.getLogger('PlatformInterface')
        self.interfaces = []  # List of instantiated platform interfaces
        self.metadata = spec["metadata"]  # Save the exercise specification metadata
        self.infra = infra  # Save the infrastructure configuration

        # Select the Interface to use based on the specified infrastructure platform
        for platform, config in infra.items():
            if platform == "vmware-vsphere":
                from .vsphere_interface import VsphereInterface
                self.interfaces.append(VsphereInterface(config, spec))
            elif platform == "docker":
                from .docker_interface import DockerInterface
                self.interfaces.append(DockerInterface(config, spec))
            else:
                self._log.error("Invalid platform: %s", str(platform))
                raise ValueError

    @time_execution
    def create_masters(self):
        """ Master creation phase """
        self._log.info("Creating Master instances for %s", self.metadata["name"])
        # TODO: subprocess each interface call
        for i in self.interfaces:
            i.create_masters()

    @time_execution
    def deploy_environment(self):
        """ Environment deployment phase """
        self._log.info("Deploying environment for %s", self.metadata["name"])
        # TODO: subprocess each interface call
        for i in self.interfaces:
            i.deploy_environment()

    @time_execution
    def cleanup_masters(self, network_cleanup=False):
        """
        Cleans up master instances
        :param network_cleanup: If networks should be cleaned up [default: False]
        """
        self._log.info("Cleaning up Master instances for %s", self.metadata["name"])
        # TODO: subprocess each interface call
        for i in self.interfaces:
            i.cleanup_masters(network_cleanup=network_cleanup)

    @time_execution
    def cleanup_environment(self, network_cleanup=False):
        """
        Cleans up a deployed environment
        :param network_cleanup: If networks should be cleaned up [default: False]
        """
        self._log.info("Cleaning up environment for %s", self.metadata["name"])
        # TODO: subprocess each interface call
        for i in self.interfaces:
            i.cleanup_masters(network_cleanup=network_cleanup)

    def __repr__(self):
        return "Interface(%s,%s" % (str(self.interfaces), str(self.infra))

    def __str__(self):
        return str([x for x in self.infra.keys()])

    def __hash__(self):
        return hash(self.interfaces)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.interfaces == other.interfaces

    def __ne__(self, other):
        return not self.__eq__(other)
