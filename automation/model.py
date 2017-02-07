#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
        if infrastructure["platform"] is "vmware vsphere":
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
