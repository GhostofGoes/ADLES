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
import os.path

import adles.vsphere.folder_utils as futils
from adles.utils import pad, read_json, is_folder, is_vm, get_vlan
from adles.vsphere import Vsphere
from adles.vsphere.network_utils import create_portgroup
from adles.vsphere.vm import VM
from adles.interfaces import Interface


class VsphereInterface(Interface):
    """ Generic interface for the VMware vSphere platform """
    __version__ = "1.0.1"

    # noinspection PyMissingConstructor
    def __init__(self, infra, spec):
        """
        NOTE: it is assumed that the infrastructure and spec are both valid,
        and thus checks on key existence and types are not performed for REQUIRED elements.
        :param dict infra: Infrastructure information
        :param dict spec: The parsed exercise specification
        """
        self._log = logging.getLogger('VsphereInterface')
        self._log.debug("Initializing VsphereInterface %s", VsphereInterface.__version__)

        self.spec = spec
        self.metadata = spec["metadata"]
        self.services = spec["services"]
        self.networks = spec["networks"]
        self.folders = spec["folders"]
        self.infra = infra
        self.master_folder = None
        self.template_folder = None
        self.net_table = {}  # Used to do lookups of Generic networks during deployment
        self.masters = {}  # Cache containing Master instances (TODO: potential naming conflicts)

        if "thresholds" in infra:
            self.thresholds = infra["thresholds"]
        else:
            self.thresholds = {
                "folder": {
                    "warn": 25,
                    "error": 50},
                "service": {
                    "warn": 50,
                    "error": 70}
            }

        # Read infrastructure login information
        if "login-file" in infra:
            logins = read_json(infra["login-file"])  # TODO: is this secure?
        else:
            self._log.warning("No login-file specified, defaulting to user prompts...")
            logins = {}

        # Instantiate the vSphere vCenter server instance class
        self.server = Vsphere(username=logins.get("user"),
                              password=logins.get("pass"),
                              hostname=infra.get("hostname"),
                              port=int(infra.get("port")),
                              datastore=infra.get("datastore"),
                              datacenter=infra.get("datacenter"))

        # Acquire ESXi hosts (TODO: make these their own classes /w network, etc methods)
        if "hosts" in infra:
            hosts = infra["hosts"]
            self.host = self.server.get_host(hosts[0])  # TODO: temporary hack
            self.hosts = [self.server.get_host(h) for h in hosts]  # Gather all the ESXi hosts
        else:
            self.host = self.server.get_host()  # First host found in Datacenter

        # Instantiate and initialize Groups
        self.groups = self._init_groups()

        # Set the server root folder (TODO: network folder in infrastructure spec)
        if "server-root" in infra:
            self.server_root = self.server.get_folder(infra["server-root"])
            if not self.server_root:
                self._log.error("Could not find server-root folder '%s'", infra["server-root"])
                exit(1)
        else:
            self.server_root = self.server.datacenter.vmFolder  # Default to Datacenter VM folder
        self._log.info("Server root folder: %s", self.server_root.name)

        # Set environment root folder (TODO: this can be simplified and consolidated)
        if "folder-name" not in self.metadata:
            self.root_path, self.root_name = ("", self.metadata["name"])
            self.root_folder = futils.traverse_path(folder=self.server_root,
                                                    path=self.root_name,
                                                    generate=True)
        else:
            self.root_path, self.root_name = os.path.split(self.metadata["folder-name"])
            self.root_folder = futils.traverse_path(folder=self.server_root,
                                                    path=self.metadata["folder-name"],
                                                    generate=True)

        self._log.debug("Environment root folder name: %s", self.root_name)
        if not self.root_folder:  # Create if it's not found
            parent = futils.traverse_path(self.server_root, self.root_path)
            self.root_folder = self.server.create_folder(self.root_name, parent)
            if not self.root_folder:
                self._log.error("Could not create root folder '%s'", self.root_name)
                exit(1)
        self._log.info("Environment root folder: %s", self.root_folder.name)

        # Set default vSwitch name
        if "vswitch" in infra:
            self.vswitch_name = infra["vswitch"]
        else:  # TODO: is this a good default? (If you have to ask this, it's probably not)
            from pyVmomi import vim
            self.vswitch_name = self.server.get_item(vim.Network).name

        self._log.debug("Finished initializing VsphereInterface")

    def _init_groups(self):
        """
        Instantiate and initialize Groups
        :return: Initialized Groups
        :rtype: dict(:class:`Group`)
        """
        from adles.group import Group, get_ad_groups
        groups = {}

        # Instantiate Groups
        for name, config in self.spec["groups"].items():
            if "instances" in config:  # Template groups
                groups[name] = [Group(name, config, i) for i in range(1, config["instances"] + 1)]
            else:  # Standard groups
                groups[name] = Group(name=name, group=config)

        # Initialize Active Directory-type Group user names
        ad_groups = get_ad_groups(groups)
        for g in ad_groups:
            # res = self.server.get_users(belong_to_group=g.ad_group, find_users=True) (TODO)
            res = None
            if res is not None:
                for r in res:
                    if r.group is True:  # Reference: pyvmomi/docs/vim/UserSearchResult.rst
                        self._log.error("Result '%s' is not a user", str(r))
                    else:
                        g.users.append(r.principal)
                g.size = (len(g.users) if len(g.users) > 1 else 1)  # Set the size, default to 1
            else:
                self._log.error("Could not initialize AD-group %s", str(g.ad_group))

        if hasattr(self.server.user_dir, "domainList"):
            self._log.debug("Domains on server: %s", str(self.server.user_dir.domainList))

        return groups

    def create_masters(self):
        """ Exercise Environment Master creation phase """

        # Get folder containing templates
        self.template_folder = futils.traverse_path(self.server_root, self.infra["template-folder"])
        if not self.template_folder:
            self._log.error("Could not find template folder in path '%s'",
                            self.infra["template-folder"])
            return
        else:
            self._log.debug("Found template folder: '%s'", self.template_folder.name)

        # Create master folder to hold base service instances
        self.master_folder = futils.traverse_path(self.root_folder, self.master_root_name)
        if not self.master_folder:
            self.master_folder = self.server.create_folder(self.master_root_name, self.root_folder)
            self._log.info("Created Master folder '%s' in '%s'",
                           self.master_root_name, self.root_name)

        # TODO: implement configuration of "network-interface" in the "services" top-level section
        # Create networks for master instances
        for net in self.networks:  # Iterate through the base types
            self._create_master_networks(net_type=net, default_create=True)

        # Create Master instances
        # TODO: Apply master-group permissions [default: group permissions]
        self._master_parent_folder_gen(self.folders, self.master_folder)

        # Output fully deployed master folder tree to debugging
        self._log.debug(futils.format_structure(futils.enumerate_folder(self.root_folder)))

    def _master_parent_folder_gen(self, folder, parent):
        """
        Generates parent-type Master folders
        :param dict folder: Dict with the folder tree structure as in spec
        :param parent: Parent folder
        :type parent: vim.Folder
        """
        skip_keys = ["instances", "description", "enabled"]
        if not self._is_enabled(folder):  # Check if disabled
            self._log.warning("Skipping disabled parent-type folder %s", parent.name)
            return

        group = None
        master_group = None

        # We have to check every item, as they could be either keywords or sub-folders
        for sub_name, sub_value in folder.items():
            if sub_name in skip_keys:  # Skip configurations that are not relevant
                continue
            elif sub_name == "group":
                group = self._get_group(sub_value)
            elif sub_name == "master-group":
                master_group = self._get_group(sub_value)
            else:
                folder_name = self.master_prefix + sub_name
                new_folder = self.server.create_folder(folder_name, create_in=parent)

                if "services" in sub_value:  # It's a base folder
                    if self._is_enabled(sub_value):
                        self._log.info("Generating Master base-type folder %s", sub_name)
                        self._master_base_folder_gen(sub_name, sub_value, new_folder)
                    else:
                        self._log.warning("Skipping disabled base-type folder %s", sub_name)
                else:  # It's a parent folder, recurse
                    if self._is_enabled(sub_value):
                        self._master_parent_folder_gen(sub_value, parent=new_folder)
                        self._log.info("Generating Master parent-type folder %s", sub_name)
                    else:
                        self._log.warning("Skipping disabled parent-type folder %s", sub_name)

        # TODO: apply master group permissions
        if master_group is None:
            master_group = group

    def _master_base_folder_gen(self, folder_name, folder_dict, parent):
        """
        Generates base-type Master folders
        :param str folder_name: Name of the base folder
        :param dict folder_dict: Dict with the base folder tree as in spec
        :param parent: Parent folder
        :type parent: vim.Folder
        """
        # Set the group to apply permissions for (TODO: apply permissions)
        if "master-group" in folder_dict:
            master_group = self._get_group(folder_dict["master-group"])
        else:
            master_group = self._get_group(folder_dict["group"])

        # Create Master instances
        for sname, sconfig in folder_dict["services"].items():
            if not self._is_vsphere(sconfig["service"]):
                self._log.debug("Skipping non-vsphere service '%s'", sname)
                continue

            self._log.info("Creating Master instance '%s' from service '%s'",
                           sname, sconfig["service"])

            vm = self._create_service(parent, sconfig["service"], sconfig["networks"])
            if vm is None:
                self._log.error("Failed to create Master instance '%s' in folder '%s'",
                                sname, folder_name)
                continue  # Skip to the next service

    def _create_service(self, folder, service_name, networks):
        """
        Retrieves and clones a service into a master folder
        :param folder: Folder to create service in
        :type folder: vim.Folder
        :param str service_name: Name of the service to clone
        :param list networks: Networks to configure the service with
        :return: The service VM instance
        :rtype: :class:`VM`
        """
        if not self._is_vsphere(service_name):
            self._log.debug("Skipping non-vsphere service '%s'", service_name)
            return None

        config = self.services[service_name]
        vm_name = self.master_prefix + service_name

        test = futils.traverse_path(folder, vm_name)  # Check service already exists
        if test is None:
            # Find the template that matches the service definition
            template = futils.traverse_path(self.template_folder, config["template"])
            if not template:
                self._log.error("Could not find template '%s' for service '%s'",
                                config["template"], service_name)
                return None
            self._log.info("Creating service '%s'", service_name)
            vm = VM(name=vm_name, folder=folder, resource_pool=self.server.get_pool(),
                    datastore=self.server.datastore, host=self.host)
            if not vm.create(template=template):
                return None
        else:
            self._log.warning("Service %s already exists", service_name)
            vm = VM(vm=test)
            # TODO: we're assuming the template's configuration is valid, need a way to check
            if vm.is_template():  # Check if it's been converted already
                self._log.warning("Service %s is a Template, skipping configuration", service_name)
                return vm

        if "resource-config" in config:  # Resource configurations (minus storage currently)
            vm.edit_resources(**config["resource-config"])

        if "note" in config:  # Set VM note if specified
            vm.set_note(config["note"])

        # NOTE: management interfaces matter here!
        self._configure_nics(vm, networks=networks)  # Configure VM NICs

        # Post-creation snapshot (TODO: more descriptive description using metadata)
        vm.create_snapshot("Start of Mastering", "Beginning of Mastering phase ")

        return vm

    def _create_master_networks(self, net_type, default_create):
        """
        Creates a network as part of the Master creation phase
        :param str net_type: Top-level type of the network (unique | generic | base)
        :param bool default_create: Whether to create networks if they don't already exist
        """
        self.host.configManager.networkSystem.RefreshNetworkSystem()  # Pick up any recent changes
        self._log.info("Creating %s", net_type)

        for name, config in self.networks[net_type].items():
            exists = self.server.get_network(name)
            if exists:
                self._log.info("PortGroup '%s' already exists on host '%s'", name, self.host.name)
            else:  # NOTE: if monitoring, we want promiscuous=True
                self._log.warning("PortGroup '%s' does not exist on host '%s'",
                                  name, self.host.name)
                if default_create:
                    self._log.info("Creating portgroup '%s' on host '%s'", name, self.host.name)
                    create_portgroup(name=name, host=self.host, promiscuous=False,
                                     vlan=int(config.get("vlan", next(get_vlan()))),
                                     vswitch_name=config.get("vswitch", self.vswitch_name))

    def _configure_nics(self, vm, networks, instance=None):
        """
        Configures Virtual Network Interfaces Cards (vNICs) for a service instance
        :param vm: Virtual Machine to configure vNICs on
        :type vm: vim.VirtualMachine
        :param list networks: List of networks to configure
        :param int instance: Current instance of a folder for Deployment purposes [default: None]
        """
        self._log.info("Editing NICs for VM '%s'", vm.name)
        num_nics = len(list(vm.network))
        num_nets = len(networks)
        nets = networks  # Copy the passed variable so we can edit it later

        # Ensure number of NICs on VM matches number of networks configured for the service
        # Note that monitoring interfaces will be counted and included in the networks list
        if num_nics > num_nets:     # Remove excess interfaces
            diff = int(num_nics - num_nets)
            self._log.debug("VM '%s' has %d extra NICs, removing...", vm.name, diff)
            for i, nic in zip(range(1, diff + 1), reversed(range(num_nics))):
                vm.remove_nic(nic)

        elif num_nics < num_nets:   # Create missing interfaces
            diff = int(num_nets - num_nics)
            self._log.debug("VM '%s' is deficient %d NICs, adding...", vm.name, diff)
            for i in range(diff):   # Add NICs to VM and pop them from the list of networks
                nic_model = ("vmxnet3" if vm.has_tools() else "e1000")  # Select NIC hardware
                net_name = nets.pop()
                vm.add_nic(network=self.server.get_network(net_name),
                           model=nic_model, summary=net_name)
            num_nets = len(networks)

        # Edit the interfaces
        # NOTE: any NICs that were added earlier shouldn't be affected by this
        # TODO: traverse folder to get network? (need to switch to DVswitches I think)
        for net_name, i in zip(networks, range(1, num_nets + 1)):
            # Setting the summary to network name allows viewing of name without requiring
            # read permissions to the network itself
            if instance is not None:  # Resolve generic networks for deployment phase
                net_name = self._get_net(net_name, instance)
            network = self.server.get_network(net_name)
            if vm.get_nic_by_id(i).backing.network == network:
                continue  # Skip NICs that are already configured
            else:
                vm.edit_nic(nic_id=i, network=network, summary=net_name)

    def deploy_environment(self):
        """ Exercise Environment deployment phase """
        self.master_folder = futils.traverse_path(self.root_folder, self.master_root_name)
        if self.master_folder is None:  # Check if Master folder was found
            self._log.error("Could not find Master folder '%s'. "
                            "Please ensure the  Master Creation phase has been run "
                            "and the folder exists before attempting Deployment",
                            self.master_root_name)
            exit(1)
        self._log.debug("Master folder name: %s\tPrefix: %s",
                        self.master_folder.name, self.master_prefix)

        # Verify and convert Master instances to templates
        self._log.info("Validating and converting Masters to Templates")
        self._convert_and_verify(folder=self.master_folder)
        self._log.info("Finished validating and converting Masters to Templates")

        self._log.info("Deploying environment...")
        self._deploy_parent_folder_gen(spec=self.folders, parent=self.root_folder, path="")
        self._log.info("Finished deploying environment")

        # Output fully deployed environment tree to debugging
        self._log.debug(futils.format_structure(futils.enumerate_folder(self.root_folder)))

    def _convert_and_verify(self, folder):
        """
        Converts Masters to Templates before deployment.
        This also ensures they are powered off before being cloned.
        :param folder: Folder containing Master instances to convert and verify
        :type folder: vim.Folder
        """
        self._log.debug("Converting Masters in folder '%s' to templates", folder.name)
        for item in folder.childEntity:
            if is_vm(item):
                vm = VM(vm=item)
                self.masters[vm.name] = vm
                if vm.is_template():  # Skip if they already exist from a previous run
                    self._log.debug("Master '%s' is already a template", vm.name)
                    continue

                # Cleanly power off VM before converting to template
                if vm.powered_on():
                    vm.change_state("off", attempt_guest=True)

                # Take a snapshot to allow reverts to the start of the exercise
                vm.create_snapshot("Start of exercise",
                                   "Beginning of deployment phase, post-master configuration")

                # Convert Master instance to Template
                vm.convert_template()
                if not vm.is_template():
                    self._log.error("Master '%s' did not convert to Template", vm.name)
                else:
                    self._log.debug("Converted Master '%s' to Template", vm.name)
            elif is_folder(item):  # Recurse into sub-folders
                self._convert_and_verify(item)
            else:
                self._log.debug("Unknown item found while templatizing Masters: %s", str(item))

    def _deploy_parent_folder_gen(self, spec, parent, path):
        """
        Generates parent-type folder trees
        :param dict spec: Dict with folder specification
        :param parent: Parent folder
        :type parent: vim.Folder
        :param str path: Folders path at the current level
        """
        skip_keys = ["instances", "description", "master-group", "enabled"]
        if not self._is_enabled(spec):  # Check if disabled
            self._log.warning("Skipping disabled parent-type folder %s", parent.name)
            return

        for sub_name, sub_value in spec.items():
            if sub_name in skip_keys:  # Skip configurations that are not relevant
                continue
            elif sub_name == "group":  # Configure group
                group = self._get_group(sub_value)  # TODO: apply group permissions
            else:  # Create instances of the parent folder
                self._log.debug("Deploying parent-type folder '%s'", sub_name)
                num_instances, prefix = self._instances_handler(spec, sub_name, "folder")
                for i in range(num_instances):
                    # If prefix is undefined or there's a single instance, use the folder's name
                    instance_name = (sub_name if prefix == "" or num_instances == 1 else prefix)

                    # If multiple instances, append padded instance number
                    instance_name += (pad(i) if num_instances > 1 else "")

                    # Create a folder for the instance
                    new_folder = self.server.create_folder(instance_name, create_in=parent)

                    if "services" in sub_value:  # It's a base folder
                        if self._is_enabled(sub_value):
                            self._deploy_base_folder_gen(folder_name=sub_name,
                                                         folder_items=sub_value, parent=new_folder,
                                                         path=self._path(path, sub_name))
                        else:
                            self._log.warning("Skipping disabled base-type folder %s", sub_name)
                    else:  # It's a parent folder
                        if self._is_enabled(sub_value):
                            self._deploy_parent_folder_gen(parent=new_folder, spec=sub_value,
                                                           path=self._path(path, sub_name))
                        else:
                            self._log.warning("Skipping disabled parent-type folder %s", sub_name)

    def _deploy_base_folder_gen(self, folder_name, folder_items, parent, path):
        """
        Generates folder tree for deployment stage
        :param str folder_name: Name of the folder
        :param dict folder_items: Dict of items in the folder
        :param parent: Parent folder
        :type parent: vim.Folder
        :param str path: Folders path at the current level
        """
        # Set the group to apply permissions for (TODO: apply permissions)
        group = self._get_group(folder_items["group"])

        # Get number of instances and check if it exceeds configured limits
        num_instances, prefix = self._instances_handler(folder_items, folder_name, "folder")

        # Create instances
        self._log.info("Deploying base-type folder '%s'", folder_name)
        for i in range(num_instances):
            # If no prefix is defined or there's only a single instance, use the folder's name
            instance_name = (folder_name if prefix == "" or num_instances == 1 else prefix)

            # If multiple instances, append padded instance number
            instance_name += (pad(i) if num_instances > 1 else "")

            if num_instances > 1:  # Create a folder for the instance
                new_folder = self.server.create_folder(instance_name, create_in=parent)
            else:  # Don't duplicate folder name for single instances
                new_folder = parent

            # Use the folder's name for the path, as that's what matches the Master version
            self._log.info("Generating services for base-type folder instance '%s'", instance_name)
            self._deploy_gen_services(services=folder_items["services"], parent=new_folder,
                                      path=path, instance=i)

    def _deploy_gen_services(self, services, parent, path, instance):
        """
        Generates the services in a folder
        :param dict services: The "services" dict in a folder
        :param parent: Parent folder
        :type parent: vim.Folder
        :param str path: Folders path at the current level
        :param int instance: What instance of a base folder this is
        """
        # Iterate through the services
        for service_name, value in services.items():
            if not self._is_vsphere(value["service"]):  # Ignore non-vsphere services
                self._log.debug("Skipping non-vsphere service '%s'", service_name)
                continue
            self._log.info("Generating service '%s' in folder '%s'", service_name, parent.name)

            # Get number of instances for the service and check if it exceeds configured limits
            num_instances, prefix = self._instances_handler(value, service_name, "service")

            # Get the Master template instance to clone from
            master = self.masters.get(self.master_prefix + value["service"], None)
            if master is None:  # Check if the lookup was successful
                self._log.error("Couldn't find Master for service '%s' in this path:\n%s",
                                value["service"], path)
                continue  # Skip to the next service

            # Clone the instances of the service from the master
            for i in range(num_instances):
                instance_name = prefix + service_name + (" " + pad(i) if num_instances > 1 else "")
                vm = VM(name=instance_name, folder=parent, resource_pool=self.server.get_pool(),
                        datastore=self.server.datastore, host=self.host)
                if not vm.create(template=master.get_vim_vm()):
                    self._log.error("Failed to create instance %s", instance_name)
                else:
                    self._configure_nics(vm, value["networks"], instance=instance)

    def _is_vsphere(self, service_name):
        """
        Checks if a service instance is defined as a vSphere service
        :param str service_name: Name of the service to lookup in list of defined services
        :return: If a service is a vSphere-type service
        :rtype: bool
        """
        # TODO: make "template" and other platform identifiers global keywords
        if service_name not in self.services:
            self._log.error("Could not find service %s in list of services", service_name)
        elif "template" in self.services[service_name]:
            return True
        return False

    def _get_net(self, name, instance=-1):
        """
        Resolves network names. This is mainly to handle generic-type networks.
        If a generic network does not exist, it is created and added to the interface lookup table.
        :param str name: Name of the network
        :param int instance: Instance number (Only applies to generic-type networks)
        :return: Resolved network name
        :rtype: str
        """
        # TODO: could use this to do network lookups on the server as well
        net_type = self._determine_net_type(name)
        if net_type == "unique-networks":
            return name
        elif net_type == "generic-networks":
            if instance == -1:
                self._log.error("Invalid instance for _get_net: %d", instance)
                raise ValueError
            net_name = name + "-GENERIC-" + pad(instance)  # Generate full name for the generic net
            if net_name not in self.net_table:
                exists = self.server.get_network(net_name)
                if exists is not None:
                    self._log.debug("PortGroup '%s' already exists on host '%s'", net_name,
                                    self.host.name)
                else:  # Create the generic network if it does not exist
                    # NOTE: lookup of name is case-sensitive! This can lead to bugs
                    self._log.debug("Creating portgroup '%s' on host '%s'", net_name,
                                    self.host.name)
                    vsw = self.networks["generic-networks"][name].get("vswitch", self.vswitch_name)
                    create_portgroup(name=net_name, host=self.host, promiscuous=False,
                                     vlan=next(get_vlan()), vswitch_name=vsw)
                self.net_table[net_name] = True  # Register the existence of the generic
            return net_name
        else:
            self._log.error("Invalid network type %s for network %s", net_type, name)
            raise TypeError

    def cleanup_masters(self, network_cleanup=False):
        """
        Cleans up any master instances
        :param bool network_cleanup: If networks should be cleaned up [default: False]
        """
        # TODO: look at getorphanedvms in pyvmomi-community-samples for how to do this
        # Get the folder to cleanup in
        master_folder = futils.find_in_folder(self.root_folder, self.master_root_name)
        self._log.info("Found master folder '%s' under folder '%s', proceeding with cleanup...",
                       master_folder.name, self.root_folder.name)

        # Recursively descend from master folder, destroying anything with the prefix
        futils.cleanup(folder=master_folder, vm_prefix=self.master_prefix,
                       recursive=True, destroy_folders=True, destroy_self=True)

        # Cleanup networks (TODO: use network folders to aid in this, during creation phase)
        if network_cleanup:
            pass

    def cleanup_environment(self, network_cleanup=False):
        """
        Cleans up a deployed environment
        :param bool network_cleanup: If networks should be cleaned up [default: False]
        """
        # Get the root environment folder to cleanup in
        enviro_folder = self.root_folder

        # TODO: ensure master folder is skipped

        # Cleanup networks (TODO: use network folders to aid in this, during creation phase)
        if network_cleanup:
            pass

    def __str__(self):
        return str(self.server) + str(self.groups) + str(self.hosts)

    def __eq__(self, other):
        return super(VsphereInterface, self).__eq__(other) and self.server == other.server and \
               self.groups == other.groups and self.hosts == other.hosts
