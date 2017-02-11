#!/usr/bin/env python3
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


class Model:
    def __init__(self, spec):
        """
        :param spec: Full specification
        """
        metadata = spec["metadata"]

        # Load infrastructure information
        if metadata["infrastructure-config-file"]:
            from automation.parser import parse_file
            infrastructure = parse_file(metadata["infrastructure-config-file"])
        else:
            logging.error("No infrastructure configuration file specified!")
            exit(1)

        # Load login information
        from json import load
        try:
            logging.debug("Loading login information...")
            with open(infrastructure["login-file"], "r") as login_file:
                logins = load(fp=login_file)
        except Exception as e:
            logging.error("Could not open login file %s. Error: %s", infrastructure["login-file"], str(e))
            exit(1)

        # Select the Interface to use for the platform
        if infrastructure["platform"] == "vmware vsphere":
            from automation.vsphere_interface import VsphereInterface
            self.interface = VsphereInterface(infrastructure, logins, spec)  # Create interface
        else:
            logging.error("Invalid platform {}".format(infrastructure["platform"]))
            exit(1)

    def create_masters(self):
        logging.info("Creating Master instances for environment setup...")
        self.interface.create_masters()

    def deploy_environment(self):
        logging.info("Deploying environment...")
        self.interface.deploy_environment()


if __name__ == '__main__':
    pass  # RUN TESTS
