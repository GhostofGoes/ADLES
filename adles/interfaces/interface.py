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
    """ Generic interface used to uniformly interact with platform-specific interface implementations. """

    def __init__(self, spec):
        """ :param spec: Full specification """
        from sys import exit
        self.metadata = spec["metadata"]

        if not self.metadata["infrastructure-config-file"]:
            logging.error("No infrastructure configuration file specified!")
            exit(1)

        # Load infrastructure information
        from adles.parser import parse_file
        # infrastructure = parse_file(metadata["infrastructure-config-file"])
        infrastructure = parse_file("vsphere.yaml")  # TODO: testing only, either make this a CMD arg or remove

        # Load login information
        from adles.utils import read_json
        logging.debug("Loading login information from file %s", infrastructure["login-file"])
        logins = read_json(infrastructure["login-file"])
        if not logins:
            exit(1)

        # Instantiate groups
        from adles.group import Group
        groups = []
        for name, config in spec["groups"]:
            if "instances" in config:  # Template groups
                for i in range(1, config["instances"] + 1):
                    groups.append(Group(name=name, group=config, instance=i))
            else:
                groups.append(Group(name=name, group=config))

        # Select the Interface to use for the platform
        if infrastructure["platform"] == "vmware vsphere":
            from .vsphere_interface import VsphereInterface
            self.interface = VsphereInterface(infrastructure, logins, spec, groups)  # Create interface
        else:
            logging.error("Invalid platform %s", infrastructure["platform"])
            exit(1)

    @time_execution
    def create_masters(self):
        """ Master creation phase """
        logging.info("Creating Master instances for %s", self.metadata["name"])
        self.interface.create_masters()

    @time_execution
    def deploy_environment(self):
        """ Environment deployment phase """
        logging.info("Deploying environment for %s", self.metadata["name"])
        self.interface.deploy_environment()

    @time_execution
    def cleanup_masters(self, network_cleanup=False):
        """
        Cleans up master instances
        :param network_cleanup: If networks should be cleaned up [default: False]
        """
        logging.info("Cleaning up Master instances for %s", self.metadata["name"])
        self.interface.cleanup_masters(network_cleanup=network_cleanup)

    @time_execution
    def cleanup_environment(self, network_cleanup=False):
        """
        Cleans up a deployed environment
        :param network_cleanup: If networks should be cleaned up [default: False]
        """
        logging.info("Cleaning up environment for %s", self.metadata["name"])
        self.interface.cleanup_masters(network_cleanup=network_cleanup)
