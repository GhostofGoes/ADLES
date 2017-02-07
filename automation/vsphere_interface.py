#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

from automation.vsphere.vsphere import vSphere
from automation.vsphere.network_utils import *
from automation.vsphere.vsphere_utils import *
from automation.vsphere.vm_utils import *


class VsphereInterface:
    def __init__(self, infrastructure, logins, spec):
        logging.debug("Initializing interface...")
        self.spec = spec
        self.groups = spec["groups"]
        self.services = spec["services"]
        # TODO: how do resources fit in here? Ignoring for now...
        self.networks = spec["networks"]
        self.folders = spec["folders"]
        self.server = vSphere(datacenter=infrastructure["datacenter"],
                           username=logins["user"],
                           password=logins["pass"],
                           hostname=logins["host"],
                           port=int(logins["port"]),
                           datastore=infrastructure["datastore"])

    def create_masters(self):
        # Create base service instances
        for service in self.services:
            pass

    def deploy_environment(self):
        pass


if __name__ == '__main__':
    pass  # Testing
