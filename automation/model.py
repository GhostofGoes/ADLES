#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from automation.interface import Interface


class Model:
    def __init__(self, metadata):
        """
        :param metadata: Dict containing metadata for the specification
        """
        self.metadata = metadata

        # Load infrastructure information
        if metadata["infrastructure-config-file"]:
            from automation.parser import parse_file
            self.infra = parse_file(metadata["infrastructure-config-file"])
        else:
            logging.error("No infrastructure configuration file specified!")
            exit(1)

        # Load login information
        from json import load
        try:
            logging.debug("Loading login information...")
            with open(self.infra["login-file"], "r") as login_file:
                logins = load(fp=login_file)
        except Exception as e:
            logging.error("Could not open login file %s. Error: %s", self.infra["login-file"], str(e))
            exit(1)

        logging.debug("Initializing interface...")
        self.interface = Interface(self.infra, logins)

    def load_groups(self, groups):
        pass

    def load_services(self, services):
        pass

    def load_resources(self, resources):
        pass

    def load_networks(self, networks):
        pass

    def load_folders(self, folders):
        pass

    def create_masters(self):
        logging.info("Creating Master instances for environment setup...")
        self.interface.create_masters()

    def deploy_environment(self):
        logging.info("Deploying environment...")
        self.interface.deploy_environment()


if __name__ == '__main__':
    pass  # RUN TESTS
