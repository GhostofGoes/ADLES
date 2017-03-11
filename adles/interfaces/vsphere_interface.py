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
from sys import exit

import adles.vsphere.folder_utils as futils
import adles.vsphere.vm_utils as vm_utils
import adles.vsphere.vsphere_utils as vutils
from adles.utils import pad
from adles.vsphere import Vsphere
from adles.vsphere.network_utils import create_portgroup, get_net_obj


class VsphereInterface:
    """ Generic interface for the VMware vSphere platform """

    # Names/prefixes
    master_prefix = "(MASTER) "
    master_root_name = "MASTER_FOLDERS"

    # Values at which to warn or error when exceeded
    # TODO: make these per-instance and configurable in spec?
    service_warn = 50
    service_error = 70
    folder_warn = 25
    folder_error = 50

    def __init__(self, infrastructure, logins, groups, spec):
        """
        :param infrastructure: Dict of infrastructure information
        :param logins: Dict of infrastructure logins
        :param groups: List of Group objects
        :param spec: Dict of a parsed specification
        """
        logging.debug("Initializing VsphereInterface...")
        self.spec = spec
        self.metadata = spec["metadata"]
        self.groups = groups
        self.services = spec["services"]
        self.networks = spec["networks"]
        self.folders = spec["folders"]
        self.master_folder = None
        self.template_folder = None

        # Create the vSphere object to interact with
        self.server = Vsphere(datacenter=infrastructure["datacenter"],
                              username=logins["user"],
                              password=logins["pass"],
                              hostname=logins["host"],
                              port=int(logins["port"]),
                              datastore=infrastructure["datastore"])

        # Set the server root folder
        if "server-root" in infrastructure:
            self.server_root = self.server.get_folder(infrastructure["server-root"])
        else:
            self.server_root = self.server.datacenter.vmFolder  # Default to Datacenter VM folder root
        logging.info("Server root folder: %s", self.server_root.name)

        # Set environment root folder name
        if "folder-name" not in self.metadata:
            self.root_name = self.metadata["name"]
        else:
            self.root_name = self.metadata["folder-name"]
        logging.debug("Environment root folder name: %s", self.root_name)

        # Get the environment root folder, or create it if it doesn't already exist
        self.root_path = self.metadata["root-path"]  # Guaranteed to be in metadata
        self.root_folder = futils.traverse_path(self.server_root, self.root_path + self.root_name)
        if not self.root_folder:  # Create if it's not found
            parent = futils.traverse_path(self.server_root, self.root_path)
            self.root_folder = self.server.create_folder(self.root_name, parent)
        logging.info("Environment root folder: %s", self.root_folder.name)

        logging.debug("Finished initializing VsphereInterface")

    def create_masters(self):
        """ Master creation phase """

        # Get folder containing templates
        self.template_folder = futils.traverse_path(self.server_root, self.metadata["template-path"])
        if not self.template_folder:
            logging.error("Could not find template folder in path '%s'",
                          self.metadata["template-path"])
            return
        else:
            logging.debug("Found template folder: '%s'", self.template_folder.name)

        # Create master folder to hold base service instances
        self.master_folder = self.server.create_folder(
            VsphereInterface.master_root_name, self.root_folder)
        logging.info("Created master folder '%s' under folder '%s'",
                     VsphereInterface.master_root_name, self.root_name)

        # Create PortGroups for networks
        # Networks
        #   Create folder to hold portgroups (for easy deletion later)
        #   Create portgroup instances (ensure appending pad() to end of names)
        #   Create generic-networks
        #   Create base-networks
        # TODO: networks
        for net in self.networks:  # Iterate through the base types
            self._create_master_networks(net_type=net, default_create=True)

        # Create Master instances
        # TODO: Apply master-group permissions [default: group permissions]
        self._master_folder_gen(self.folders, self.master_folder)

        # Output fully deployed master folder tree to debugging
        logging.debug(futils.format_structure(
            futils.enumerate_folder(self.root_folder)))

    def _master_folder_gen(self, folder, parent):
        """
        Generates the Master tree of folders and instances
        :param folder: Dict with the folder tree structure as in spec
        :param parent: Parent vim.Folder
        :return:
        """
        for folder_name, folder_value in folder.items():
            logging.debug("Generating master folder %s", folder_name)
            folder_name = VsphereInterface.master_prefix + folder_name
            folder = self.server.create_folder(folder_name=folder_name,
                                               create_in=parent)
            # TODO: apply permissions

            if "services" in folder_value:  # It's a base folder
                for sname, sconfig in folder_value["services"].items():
                    logging.info("Creating Master for '%s' from service '%s'",
                                 sname, sconfig["service"])

                    vm = self._clone_service(folder=folder,
                                             service_name=sconfig["service"])

                    if not vm:
                        logging.error("Failed to clone Master for service '%s' in folder '%s'",
                                      sname, folder_name)
                        continue  # Skip to the next service

                    # NOTE: management interfaces matter here!
                    self._configure_nics(vm=vm, networks=sconfig["networks"])  # Configure VM NICs

                    # Post-creation snapshot
                    vm_utils.create_snapshot(vm, "mastering post-clone",
                                             "Clean Post-Master cloning snapshot")

            else:  # It's a parent folder, recurse
                self._master_folder_gen(folder=folder_value, parent=folder)

    def _clone_service(self, folder, service_name):
        """
        Retrieves and clones a service into a master folder
        :param folder: vim.Folder to clone into
        :param service_name: Name of the service to clone
        :return: The service vim.VirtualMachine instance
        """
        for name, config in self.services.items():
            if name == service_name and "template" in config:
                logging.debug("Cloning service '%s'", name)
                vm_name = VsphereInterface.master_prefix + service_name
                template = futils.traverse_path(self.template_folder, config["template"])
                if not template:
                    logging.error("Could not find template '%s' for service '%s'",
                                  config["template"], name)
                    return None
                vm_utils.clone_vm(vm=template, folder=folder, name=vm_name,
                                  clone_spec=self.server.gen_clone_spec())
                vm = futils.traverse_path(folder, vm_name)  # Get new cloned instance
                if vm:
                    logging.debug("Successfully cloned service '%s' to folder '%s'",
                                  service_name, folder.name)
                    if "note" in config:  # Set VM note if specified
                        vm_utils.set_note(vm=vm, note=config["note"])
                    return vm
                else:
                    logging.error("Failed to clone VM '%s' for service '%s'", vm_name, service_name)
                    return None
        logging.error("Could not find service '%s'", service_name)
        return None

    def _create_master_networks(self, net_type, default_create):
        """
        Creates a network as part of the Master creation phase
        :param net_type: Top-level type of the network (unique | generic | base)
        :param default_create: Whether to create networks if they don't already exist
        """
        host = self.server.get_host()  # TODO: define host/cluster to use in class
        host.configManager.networkSystem.RefreshNetworkSystem()  # Pick up any recent changes

        for name, config in self.networks[net_type].items():
            logging.info("Creating Master %ss", net_type)
            exists = get_net_obj(host=host, object_type="portgroup", name=name, refresh=False)
            if exists:
                logging.info("PortGroup '%s' already exists on host '%s'", name, host.name)
            else:  # NOTE: if monitoring, we want promiscuous=True
                logging.warning("PortGroup '%s' does not exist on host '%s'", name, host.name)
                if default_create:
                    logging.debug("Creating portgroup '%s' on host '%s'", name, host.name)
                    vlan = (int(config["vlan"]) if "vlan" in config else 0)  # Set the VLAN
                    create_portgroup(name=name, host=host, vswitch_name=config["vswitch"],
                                     vlan=vlan, promiscuous=False)

    def _configure_nics(self, vm, networks):
        """
        Configures Network Interfaces for a service instance
        :param vm: vim.VirtualMachine
        :param networks: List of networks to configure
        """
        logging.debug("Editing NICs for VM '%s'", vm.name)
        num_nics = len(list(vm.network))
        num_nets = len(networks)
        nets = networks  # Copy the passed variable so we can edit it later

        # Ensure number of NICs on VM matches number of networks configured for the service
        # Note that monitoring interfaces will be counted and included in the networks list
        if num_nics > num_nets:     # Remove excess interfaces
            diff = int(num_nics - num_nets)
            logging.debug("VM '%s' has %d extra NICs, removing...", vm.name, diff)
            for i, nic in zip(range(1, diff + 1), reversed(range(num_nics))):
                vm_utils.delete_nic(vm=vm, nic_number=nic)

        elif num_nics < num_nets:   # Create missing interfaces
            diff = int(num_nets - num_nics)
            logging.debug("VM '%s' is deficient %d NICs, adding...", vm.name, diff)
            for i in range(diff):   # Add NICs to VM and pop them from the list of networks
                nic_model = ("vmxnet3" if vm_utils.has_tools(vm) else "e1000")
                vm_utils.add_nic(vm=vm, network=self.server.get_network(network_name=nets.pop()),
                                 model=nic_model)
            num_nets = len(networks)

        # Edit the interfaces. NOTE: any NICs that were added earlier shouldn't be affected by this
        # TODO: traverse folder to get network?
        for net, i in zip(networks, range(1, num_nets + 1)):
            vm_utils.edit_nic(vm=vm, nic_number=i,
                              port_group=self.server.get_network(net), summary=net)

    def deploy_environment(self):
        """ Environment deployment phase """

        # Get the master folder root
        self.master_folder = futils.traverse_path(self.root_folder,
                                                  VsphereInterface.master_root_name)
        logging.debug("Master folder name: %s\tPrefix: %s",
                      self.master_folder.name, VsphereInterface.master_prefix)

        # Verify and convert to templates
        # This is to ensure they are preserved throughout creation and execution of exercise
        logging.info("Converting Masters to Templates")
        self._convert_and_verify(folder=self.master_folder)
        logging.info("Finished converting Masters to Templates")

        # Create base-networks

        # Deployment
        #   Create folder structure
        #   Apply permissions
        #   Clone instances
        # TODO: Need to figure out when/how to apply permissions
        # TODO: Base + Generic networks
        logging.info("Deploying environment...")
        self._deploy_folder_gen(self.folders, self.root_folder)
        logging.info("Finished deploying environment")

        # Output fully deployed environment tree to debugging
        logging.debug(futils.format_structure(futils.enumerate_folder(self.root_folder)))

    def _convert_and_verify(self, folder):
        """
        Converts masters to templates before deployment.
        This also ensures they are powered off before being cloned.
        :param folder: vim.Folder
        """
        logging.debug("Converting Masters in folder '%s' to templates", folder.name)
        for item in folder.childEntity:
            if vutils.is_vm(item):
                if vm_utils.powered_on(item):  # Power off VM before converting to template
                    vm_utils.change_vm_state(vm=item, state="off", attempt_guest=True)
                vm_utils.convert_to_template(item)  # Convert master to template
                logging.debug("Converted Master '%s' to Template. Verifying...", item.name)
                if not vm_utils.is_template(item):  # Check if it converted successfully
                    logging.error("Master '%s' did not convert to template", item.name)
                else:
                    logging.debug("Verified!")
            elif vutils.is_folder(item):  # Recurse into sub-folders
                self._convert_and_verify(folder=item)

    def _deploy_folder_gen(self, folders, parent):
        """
        Generates folder tree for deployment stage
        :param folders: dict of folders
        :param parent: Parent vim.Folder
        """
        for name, value in folders.items():
            num_instances, prefix = self._instances_handler(value)
            if num_instances > VsphereInterface.folder_error:
                logging.error("%d instances of folder '%s' is beyond threshold of %d",
                              num_instances, name, VsphereInterface.folder_error)
                exit(1)
            elif num_instances > VsphereInterface.folder_warn:
                logging.warning("%d instances of folder '%s' is beyond threshold of %d",
                                num_instances, name, VsphereInterface.folder_warn)

            logging.info("Generating folder '%s'", name)
            for instance in range(num_instances):
                instance_name = prefix + name + (" " + pad(instance) if num_instances > 1 else "")
                folder = self.server.create_folder(folder_name=instance_name, create_in=parent)
                # TODO: apply group permissions
                if "services" in value:  # It's a base folder
                    logging.debug("Generating base-type folder '%s'", instance_name)
                    self._gen_services(folder, value["services"])
                else:  # It's a parent folder
                    logging.debug("Generating parent-type folder '%s'", instance_name)
                    self._parent_folder_gen(folder, value)

    def _parent_folder_gen(self, folder, spec):
        """
        Generates parent-type folder trees
        :param folder: vim.Folder
        :param spec: Dict with folder specification
        """
        for sub_name, sub_value in spec.items():
            if sub_name == "instances":
                pass  # The instances are already being generated in the parent
            elif sub_name == "group":
                pass  # TODO: apply group permissions
            else:
                self._deploy_folder_gen(sub_value, folder)

    def _gen_services(self, folder, services):
        """
        Generates the services in a folder
        :param folder: vim.Folder
        :param services: The "services" dict in a folder
        """
        # Enumerate networks in folder
        #   Create generic networks
        #   Create next instance of a base network and increment base counter for folder

        for service_name, value in services.items():
            num_instances, prefix = self._instances_handler(value)
            if num_instances > VsphereInterface.service_error:
                logging.error("%d service instances in folder '%s' is beyond threshold of %d",
                              num_instances, folder.name, VsphereInterface.service_error)
                exit(1)
            elif num_instances > VsphereInterface.service_warn:
                logging.warning("%d service instances in folder '%s' is beyond threshold of %d",
                                num_instances, folder.name, VsphereInterface.service_warn)

            # TODO: need to track current path in folder tree, lookup master instance using the same path but with master_prefix in names
            service = futils.traverse_path(self.master_folder,
                                           VsphereInterface.master_prefix + value["service"])
            logging.info("Generating service '%s' in folder '%s'", service_name, folder.name)

            # TODO: base + generic networks

            for instance in range(num_instances):
                instance_name = prefix + service_name + \
                                (" " + pad(instance) if num_instances > 1 else "")
                vm_utils.clone_vm(vm=service, folder=folder, name=instance_name,
                                  clone_spec=self.server.gen_clone_spec())

    def _instances_handler(self, spec):
        """
        Determines number of instances and optional prefix using specification
        :param spec: Dict of folder
        :return: (Number of instances, Prefix)
        """
        num = 1
        prefix = ""
        if "instances" in spec:
            if "prefix" in spec["instances"]:
                prefix = str(spec["instances"]["prefix"])

            if "number" in spec["instances"]:
                num = int(spec["instances"]["number"])
            elif "size-of" in spec["instances"]:
                num = int(self._get_group(spec["instances"]["size-of"]).size)
            else:
                logging.error("Unknown instances specification: %s", str(spec["instances"]))
                num = 0
        return num, prefix

    def _get_group(self, group_name):
        """
        Provides a uniform way to get information about normal groups and template groups
        :param group_name: Name of the group
        :return: Group object
        """
        from adles.group import Group
        if group_name in self.groups:
            g = self.groups[group_name]
            if isinstance(g, Group):    # Normal groups
                return g
            elif isinstance(g, list):   # Template groups
                return g[0]
            else:
                logging.error("Unknown type for group '%s': %s", group_name, type(g))
        else:
            logging.error("Could not get group '%s' from VsphereInterface groups", group_name)

    def cleanup_masters(self, network_cleanup=False):
        """ Cleans up any master instances"""

        # Get the folder to cleanup in
        master_folder = futils.find_in_folder(self.root_folder, self.master_root_name)
        logging.info("Found master folder '%s' under folder '%s', proceeding with cleanup...",
                     master_folder.name, self.root_folder.name)

        # Recursively descend from master folder, destroying anything with the prefix
        futils.cleanup(folder=master_folder, vm_prefix=self.master_prefix,
                       recursive=True, destroy_folders=True, destroy_self=True)

        # Cleanup networks (TODO: use network folders to aid in this, during creation phase)
        if network_cleanup:
            pass

    def cleanup_environment(self, network_cleanup=False):
        """ Cleans up a deployed environment """

        # Get the root environment folder to cleanup in
        enviro_folder = futils.find_in_folder()

        # Cleanup networks (TODO: use network folders to aid in this, during creation phase)
        if network_cleanup:
            pass
