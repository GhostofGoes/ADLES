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
        self.server.create_folder(folder_name=self.metadata["name"], create_in=None)
        self.root_folder = self.server.get_folder(folder_name=self.metadata["name"])
        self.server.create_folder(folder_name=self.root_folder, create_in="script_testing")

    def create_masters(self):
        # Create folder to hold base service instances
        master_folder_name = "MASTER_VM_INSTANCES"
        self.server.create_folder(folder_name=master_folder_name, create_in=self.root_folder.name)
        master_folder = get_obj(self.root_folder, [vim.Folder], master_folder_name, recursive=False)
        logging.info("Created master folder {} under folder {}".format(master_folder_name, self.root_folder.name))

        # TODO: apply setup permission
        # TODO: create roles

        # NOTE: not creating vswitch currently, assume created
        # Create portgroups

        # Create base service instances
        logging.info("Creating masters...")
        master_prefix = "(MASTER) "
        for service_name, service_config in self.services.items():
            if "template" in service_config:         # Virtual Machine template
                logging.info("Creating master for service %s from template %s",
                             service_name, service_config["template"])
                vm = self.server.get_vm(service_config["template"])  # TODO: pull from specific location?
                clone_vm(vm=vm, folder=master_folder, name=master_prefix + service_name,
                         clone_spec=self.server.generate_clone_spec())  # TODO: resource pools!
            elif "image" in service_config:          # Docker Container
                pass
            elif "compose-file" in service_config:   # Docker Compose file
                pass

    def deploy_environment(self):
        # Verify all master's exist
        # Convert all master's to templates
        # Verify converted successfully

        # Create folder to hold portgroups (for easy deletion later)
        # Create portgroup instances
        pass

    def get_service_instance(self, service_name):
        # TODO
        pass

if __name__ == '__main__':
    pass  # Testing
