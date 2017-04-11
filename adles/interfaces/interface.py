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


class Interface:
    """ Generic interface used to uniformly interact with platform-specific interfaces. """

    def __init__(self, spec, infra):
        """ 
        :param spec: Full exercise specification
        :param infra: Full infrastructure configuration
        """
        self.interfaces = []
        self.metadata = spec["metadata"]
        self.platforms = infra["platforms"]
        self.num_plats = len(self.platforms)

        # TODO: possible better way to do this is have a dict for each platforms info in spec
        # Prompt user for missing information
        keys = ["hostnames", "ports", "login-files"]
        for k in keys:
            if k not in infra:
                infra[k] = []
            while len(infra[k]) < self.num_plats:
                infra[k].append(input("Enter %s for infrastructure: " % k[:-1]))

        # Load infrastructure login information from the files specified in infrastructure config
        from adles.utils import read_json
        logins = [read_json(f) for f in infra["login-files"]]  # TODO: is this secure?

        # Select the Interface to use based on the specified infrastructure platform
        # TODO: don't pass the whole infra to each interface
        for i in range(self.num_plats):
            if self.platforms[i] == "vmware vsphere":
                from .vsphere_interface import VsphereInterface
                infra["hostname"] = infra["hostnames"][i]  # HACK HACK
                infra["port"] = infra["ports"][i]  # HACK HACK  fix this by redoing infra spec
                self.interfaces.append(VsphereInterface(infra, logins[i], spec))
            elif self.platforms[i] == "docker":
                from .docker_interface import DockerInterface
                self.interfaces.append(DockerInterface(infra, logins[i], spec))
            else:
                logging.error("Invalid platform: %s", self.platforms[i])
                raise ValueError

    @time_execution
    def create_masters(self):
        """ Master creation phase """
        logging.info("Creating Master instances for %s", self.metadata["name"])
        # TODO: subprocess each interface call
        for i in self.interfaces:
            i.create_masters()

    @time_execution
    def deploy_environment(self):
        """ Environment deployment phase """
        logging.info("Deploying environment for %s", self.metadata["name"])
        # TODO: subprocess each interface call
        for i in self.interfaces:
            i.deploy_environment()

    @time_execution
    def cleanup_masters(self, network_cleanup=False):
        """
        Cleans up master instances
        :param network_cleanup: If networks should be cleaned up [default: False]
        """
        logging.info("Cleaning up Master instances for %s", self.metadata["name"])
        # TODO: subprocess each interface call
        for i in self.interfaces:
            i.cleanup_masters(network_cleanup=network_cleanup)

    @time_execution
    def cleanup_environment(self, network_cleanup=False):
        """
        Cleans up a deployed environment
        :param network_cleanup: If networks should be cleaned up [default: False]
        """
        logging.info("Cleaning up environment for %s", self.metadata["name"])
        # TODO: subprocess each interface call
        for i in self.interfaces:
            i.cleanup_masters(network_cleanup=network_cleanup)
