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

from automation.vsphere.vsphere import vSphere
from automation.vsphere.network_utils import *
from automation.vsphere.vsphere_utils import *
from automation.vsphere.vm_utils import *


class VsphereInterface:
    """ Generic interface for the VMware vSphere platform """

    # Switches to tweak (these are global to ALL instances of this class)
    master_prefix = "(MASTER) "

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

        # Create root folder for the exercise
        environment_folder_name = "script_testing"
        self.root_name = self.metadata["name"]
        self.server.create_folder(folder_name=self.root_name, create_in=environment_folder_name)
        self.root_folder = self.server.get_folder(folder_name=self.root_name)

    def create_masters(self):
        """ Master creation phase """
        # Create folder to hold base service instances
        master_folder_name = "MASTER_VM_INSTANCES"
        self.server.create_folder(folder_name=master_folder_name, create_in=self.root_folder.name)
        master_folder = get_obj(self.root_folder, [vim.Folder], master_folder_name, recursive=False)
        logging.info("Created master folder {} under folder {}".format(master_folder_name, self.root_folder.name))

        # TODO: apply setup permission
        # TODO: create roles

        # NOTE: not creating vswitch currently, assume created
        # Create portgroups

        # Create base service instances (Docker containers and compose would be implemented here)

        for service_name, service_config in self.services.items():
            if "template" in service_config:         # Virtual Machine template
                logging.info("Creating master for service %s from template %s",
                             service_name, service_config["template"])
                vm = self.server.get_vm(service_config["template"])  # TODO: traverse path
                clone_vm(vm=vm, folder=master_folder, name=self.master_prefix + service_name,
                         clone_spec=self.server.generate_clone_spec())  # TODO: resource pools!

    def deploy_environment(self):
        """ Environment deployment phase """
        # Verify and convert to templates
        logging.info("Verifying masters and converting to templates...")
        for service_name, service_config in self.services.items():
            if "template" in service_config:
                vm = self.server.get_vm(self.master_prefix + service_name)  # TODO: traverse path
                if vm:  # Verify all masters exist
                    logging.debug("Verified master %s exists. Converting to template...", service_name)
                    convert_to_template(vm)  # Convert all masters to templates
                    logging.debug("Converted master %s to template. Verifying...", service_name)
                    if not is_template(vm):  # Verify converted successfully
                        logging.error("Master %s did not convert to template!", service_name)
                else:
                    logging.error("Could not find master %s", service_name)

        # Create folder to hold portgroups (for easy deletion later)
        # Create portgroup instances
