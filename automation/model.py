#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging


class Spec:
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
            with open(self.infra["login-file"], "r") as login_file:
                logins = load(fp=login_file)
        except Exception as e:
            logging.error("Could not open login file %s. Error: %s", self.infra["login-file"], str(e))
            exit(1)

        # Select an API to use
        if self.infra["platform"] == "vmware vsphere":
            from automation.vsphere.vsphere import vSphere
            self.api = vSphere(datacenter=self.infra["datacenter"],
                               username=logins["user"],
                               password=logins["pass"],
                               hostname=logins["host"],
                               port=int(logins["port"]),
                               datastore=self.infra["datastore"])
        else:
            logging.error("Invalid platform {}".format(self.infra.platform))
            exit(1)

    def load_groups(self):
        pass

    def load_services(self):
        pass

    def load_networks(self):
        pass

    def load_folders(self):
        pass

    def main(self):
        pass


if __name__ == '__main__':
    pass  # RUN TESTS
