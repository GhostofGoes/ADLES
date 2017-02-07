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
        self.metadata = spec["metadata"]
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

        # Create top-level folder for the environment
        self.root_folder = self.metadata["name"]
        self.server.create_folder(folder_name=self.root_folder, create_in="script_testing")

    def create_masters(self):
        # Create folder to hold base service instances
        masters = "MASTER_VM_INSTANCES"
        self.server.create_folder(masters, self.root_folder)

        # TODO: apply setup permission
        # TODO: create roles

        # NOTE: not creating vswitch currently, assume created
        # Create portgroups

        # Create base service instances
        for key, value in self.services.items():
            if "template" in value:         # Virtual Machine template
                pass
            elif "image" in value:          # Docker Container
                pass
            elif "compose-file" in value:   # Docker Compose file
                pass

    def deploy_environment(self):

        # Create folder to hold portgroups (for easy deletion later)
        # Create portgroup instances
        pass

    def get_service_instance(self, service_name):
        pass

if __name__ == '__main__':
    pass  # Testing
