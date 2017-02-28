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

from automation.vsphere.vsphere import Vsphere
from automation.vsphere.network_utils import create_portgroup
import automation.vsphere.vsphere_utils as vutils
import automation.vsphere.vm_utils as vm_utils
from automation.utils import pad


# TODO: separate interfaces module
class VsphereInterface:
    """ Generic interface for the VMware vSphere platform """

    # Switches to tweak (these are global to ALL instances of this class)
    master_prefix = "(MASTER) "
    master_folder_name = "MASTER_FOLDERS"
    warn_threshold = 100  # Point at which to warn if many instances are being created

    def __init__(self, infrastructure, logins, spec):
        logging.debug("Initializing VsphereInterface...")
        self.spec = spec
        self.metadata = spec["metadata"]
        self.groups = spec["groups"]
        self.services = spec["services"]
        self.networks = spec["networks"]
        self.folders = spec["folders"]

        # Create the vSphere object to interact with
        self.server = Vsphere(datacenter=infrastructure["datacenter"],
                              username=logins["user"],
                              password=logins["pass"],
                              hostname=logins["host"],
                              port=int(logins["port"]),
                              datastore=infrastructure["datastore"])

        # Set the server root (TODO: put this in infra-spec, default to server root.vmFolder)
        server_root = "script_testing"  # STATICALLY SETTING FOR NOW WHILE USING TEST ENVIRONMENT
        self.server_root = self.server.get_folder(server_root)

        # Set root folder for the exercise, or create if it doesn't yet exist
        self.root_name = (self.metadata["name"] if "folder-name" not in self.metadata else self.metadata["folder-name"])
        self.root_path = self.metadata["root-path"]
        root = vutils.traverse_path(self.server_root, self.root_path + self.root_name)
        if not root:
            parent = vutils.traverse_path(self.server_root, self.root_path)
            self.root_folder = self.server.create_folder(folder_name=self.root_name, create_in=parent)
        else:
            self.root_folder = root

    def create_masters(self):
        """ Master creation phase """

        # TODO: for the time being, just doing a flat "MASTER_FOLDERS" folder with all the masters, regardless of depth
        #   Will eventually do hierarchically based on folders and not just the services
        #   Will write a function to do this, so we can recursively descend for complex environments

        # Get folder containing templates
        template_folder = vutils.traverse_path(self.server_root, self.metadata["template-path"])
        if not template_folder:
            logging.error("Could not find template folder in path %s", self.metadata["template-path"])
            return

        # Create master folder to hold base service instances
        master_folder = self.server.create_folder(folder_name=self.master_folder_name, create_in=self.root_folder)
        logging.info("Created master folder %s under folder %s", self.master_folder_name, self.root_folder.name)

        # Create portgroups for networks
        for net_type in self.networks:
            self._create_master_networks(net_type)

        # Create base service instances (Docker containers and compose will be implemented here)
        for service_name, service_config in self.services.items():
            if "template" in service_config:         # Virtual Machine template
                logging.info("Creating master for %s from template %s", service_name, service_config["template"])
                vm_name = self.master_prefix + service_name
                template = vutils.traverse_path(template_folder, service_config["template"])
                vm_utils.clone_vm(vm=template, folder=master_folder, name=vm_name,
                                  clone_spec=self.server.generate_clone_spec())

                # Get new cloned instance
                new_vm = vutils.traverse_path(master_folder, vm_name)

                if not new_vm:
                    logging.error("Did not successfully clone VM %s for service %s", vm_name, service_name)
                    continue  # Skip to the next service, so one error doesn't stop the whole show

                # Configure VM networks
                # NOTE: management interfaces matter here!
                self._configure_nics(vm=new_vm, networks=service_config["networks"])

                # Set VM note if specified
                if "note" in service_config:
                    vm_utils.set_note(vm=new_vm, note=service_config["note"])

                # Post-creation snapshot
                logging.debug("Creating post-clone snapshot")
                vm_utils.create_snapshot(new_vm, "post-clone", "Clean snapshot taken after cloning and configuration.")

        # Apply master-group permissions [default: group permissions]

    def _create_master_networks(self, net_type):
        """
        Creates a network as part of the Master phase
        :param net_type:
        """
        host = self.server.get_host()
        host.configManager.networkSystem.RefreshNetworkSystem()  # Pick up any changes that might have occurred

        for name, config in self.networks[net_type].items():
            if "vlan" in config:
                vlan = config["vlan"]
            else:
                vlan = 0
            logging.debug("Creating portgroup %s", name)
            create_portgroup(name, host, config["vswitch"], vlan=vlan)

    def _configure_nics(self, vm, networks):
        """
        Configures Network Interfaces for a service instance
        :param vm:
        :param networks:
        :return:
        """
        num_nics = len(list(vm.network))
        num_nets = len(networks)
        nets = networks  # Copy the passed variable, in case we have to deal with NIC deficiencies
        logging.debug("Editing NICs for VM %s", vm.name)

        # Ensure number of NICs on VM matches number of networks configured for the service
        # Note that monitoring interfaces will be counted and included in the networks list (hopefully)
        if num_nics > num_nets:  # Remove excess interfaces
            diff = int(num_nics - num_nets)
            logging.debug("VM %s has %d extra NICs, removing...", vm.name, diff)
            # TODO: verify NIC numbers start at 0
            for i, nic in zip(range(diff), reversed(range(num_nics))):
                vm_utils.delete_nic(vm=vm, nic_number=nic)
        elif num_nics < num_nets:  # Create missing interfaces
            diff = int(num_nets - num_nics)
            logging.debug("VM %s is deficient %d NICs, adding...", vm.name, diff)
            for i in range(diff):  # Add NICs to VM and pop them from the list of networks
                vm_utils.add_nic(vm=vm, port_group=self.server.get_network(nets.pop()), model="e1000")
            num_nets = len(networks)

        # Edit the interfaces. NOTE: any NICs that were added earlier should not be affected by this...
        for net, i in zip(networks, num_nets):  # TODO: traverse folder to get network?
            vm_utils.edit_nic(vm=vm, nic_number=i, port_group=self.server.get_network(net), summary=net)

    def deploy_environment(self):
        """ Environment deployment phase """

        # Get the master folder root (TODO: sub-masters or multiple masters?)
        master_folder = vutils.traverse_path(self.root_folder, self.master_folder_name)
        logging.debug("Master folder name: %s\tPrefix: %s", master_folder.name, self.master_prefix)

        # Verify and convert to templates.
        # This is to ensure they are preserved throughout creation and execution of exercise.
        logging.info("Verifying masters and converting to templates...")
        for service_name, service_config in self.services.items():
            if "template" in service_config:
                vm = vutils.traverse_path(master_folder, self.master_prefix + service_name)
                if vm:  # Verify all masters exist
                    logging.debug("Verified master %s exists as %s. Converting to template...", service_name, vm.name)
                    vm_utils.convert_to_template(vm)  # Convert master to template
                    logging.debug("Converted master %s to template. Verifying...", service_name)
                    if not vm_utils.is_template(vm):  # Verify converted successfully
                        logging.error("Master %s did not convert to template!", service_name)
                    else:
                        logging.debug("Verified!")
                else:
                    logging.error("Could not find master %s", service_name)

        # NOTE: use fill_zeros when appending instance number!
        # Create folder to hold portgroups (for easy deletion later)
        # Create portgroup instances
        #   Create generic-networks
        #   Create base-networks

        # Create folder structure
        # if "services" in folder: then normal-folder
        # else: parent-folder
        # So, need to iterate and create folders.
        # if "instances" in folder: then create range(instances) folder.name + pad + prefix <-- Optional prefix
        #                                           ^ resolve "size-of" if specified instead of "number"
        # else: create folder
        #       Creating functions for normal and parent folders that can call each other
        #       Need to also figure out when/how to apply permissions
        self._folder_gen(self.folders, self.root_folder)

        # Enumerate folder tree to debugging
        logging.debug(vutils.format_structure(vutils.enumerate_folder(self.root_folder)))

        # Clone instances (use function for numbering)(use prefix if specified)

        # Take snapshots post-clone

        # Enumerate tree with VMs to debugging
        logging.debug(vutils.format_structure(vutils.enumerate_folder(self.root_folder)))

    def _normal_folder_gen(self, folder, spec):
        """
        Generates normal-type folder trees
        :param folder: vim.Folder
        :param spec:
        """
        for key, value in spec:
            if key == "instances" or key == "master-group":
                pass
            elif key == "group":
                pass  # TODO: apply group permissions
            elif key == "description":
                pass  # TODO: ?
            elif key == "services":
                pass  # TODO: services?
            else:
                logging.error("Unknown key in normal-type folder %s: %s", folder.name, key)

    def _parent_folder_gen(self, folder, spec):
        """
        Generates parent-type folder trees
        :param folder: vim.Folder
        :param spec:
        """
        for sub_name, sub_value in spec.items():
            if sub_name == "instances":
                pass
            elif sub_name == "group":
                pass  # TODO: apply group permissions
            else:
                self._folder_gen(sub_value, folder)

    def _folder_gen(self, folders, parent):
        """
        Generates folder tree for deployment stage
        :param folders: dict of folders
        :param parent: Parent vim.Folder
        """
        for name, value in folders.items():
            num_instances = self._instances_handler(value["instances"])
            logging.debug("Generating folder %s", name)
            for instance in range(num_instances):
                instance_name = name + (" " + pad(instance) if num_instances > 1 else "")
                folder = self.server.create_folder(folder_name=instance_name, create_in=parent)
                if "services" in value:  # It's a base folder
                    logging.debug("Generating base-type folder %s", instance_name)
                    self._normal_folder_gen(folder, value)
                else:  # It's a parent folder
                    logging.debug("Generating parent-type folder %s", instance_name)
                    self._parent_folder_gen(folder, value)

    def _instances_handler(self, instances):
        """
        Determines number of instances in accordance with the specification
        :param instances:
        :return: number of instances
        """
        # TODO: interface_utils file possibly?
        if "instances" in instances:
            if "number" in instances["instances"]:
                return int(instances["instances"]["number"])
            elif "size-of" in instances["instances"]:
                return int(self._group_size(self.groups[instances["instances"]["size-of"]]))
            else:
                logging.error("Unknown instances specification")
                return 0
        else:
            return 1  # Default value

    def _group_size(self, group):
        """
        Determines number of individuals in a group
        :param group:
        :return: int
        """
        # TODO: move into parent class? or utils?
        return 1  # TODO: IMPLEMENT

    def cleanup_masters(self, network_cleanup=False):
        """ Cleans up any master instances"""

        # Get the folder to cleanup in
        master_folder = vutils.find_in_folder(self.root_folder, self.master_folder_name)
        logging.info("Found master folder %s under folder %s, proceeding with cleanup...",
                     master_folder.name, self.root_folder.name)

        # Recursively descend from master folder, destroying anything with the prefix
        vutils.cleanup(folder=master_folder, prefix=self.master_prefix,
                recursive=True, destroy_folders=True, destroy_self=True)

        # Cleanup networks (TODO: use network folders to aid in this, during creation phase)
        if network_cleanup:
            pass

    def cleanup_environment(self, network_cleanup=False):
        """ Cleans up a deployed environment """

        # Cleanup networks (TODO: use network folders to aid in this, during creation phase)
        if network_cleanup:
            pass
