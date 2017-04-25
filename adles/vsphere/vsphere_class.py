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

from pyVim.connect import SmartConnect, SmartConnectNoSSL, Disconnect
from pyVmomi import vim, vmodl

from adles.vsphere.folder_utils import create_folder, get_in_folder, find_in_folder


class Vsphere:
    """ Maintains connection, logging, and constants for a vSphere instance """

    __version__ = "0.9.9"

    def __init__(self, username=None, password=None, hostname=None,
                 datacenter=None, datastore=None,
                 port=443, use_ssl=False):
        """
        Connects to a vCenter server and initializes a class instance.
        :param username: Username of account to login with [default: prompt user]
        :param password: Password of account to login with [default: prompt user]
        :param hostname: DNS hostname or IP address of vCenter instance [default: prompt user]
        :param datastore: Name of datastore to use [default: first datastore found on server]
        :param datacenter: Name of datacenter to use [default: First datacenter found on server]
        :param port: Port used to connect to vCenter instance [default: 443]
        :param use_ssl: If SSL should be used to connect [default: False]
        """
        self._log = logging.getLogger('Vsphere')
        self._log.debug("Initializing Vsphere %s\nDatacenter: %s\nDatastore: %s\nSSL: %s",
                        Vsphere.__version__, datacenter, datastore, str(use_ssl))
        if username is None:
            username = str(input("Enter username for vSphere: "))
        if password is None:
            from getpass import getpass
            password = str(getpass("Enter password for %s: " % username))
        if hostname is None:
            hostname = str(input("Enter hostname for vSphere: "))
        try:
            self._log.info("Connecting to vSphere: %s@%s:%d", username, hostname, port)
            if use_ssl:  # Connect to server using SSL certificate verification
                self.server = SmartConnect(host=hostname, user=username, pwd=password, port=port)
            else:
                self.server = SmartConnectNoSSL(host=hostname, user=username, pwd=password,
                                                port=port)
        except vim.fault.InvalidLogin:
            self._log.error("Invalid vSphere login credentials for user %s", username)
            exit(1)
        except Exception as e:
            self._log.error("An exception occurred while trying to connect to vSphere: %s", str(e))
            exit(1)

        from atexit import register
        register(Disconnect, self.server)  # Ensures connection to server is closed on program exit

        self._log.info("Connected to vSphere host %s:%d", hostname, port)
        self._log.debug("Current server time: %s", str(self.server.CurrentTime()))

        self.username = username
        self.hostname = hostname
        self.port = port

        self.content = self.server.RetrieveContent()
        self.auth = self.content.authorizationManager
        self.user_dir = self.content.userDirectory

        self.datacenter = self.get_item(vim.Datacenter, name=datacenter)
        if not self.datacenter:
            self._log.error("Could not find a datacenter to initialize with!")
            exit(1)

        self.datastore = self.get_datastore(datastore)
        if not self.datastore:
            self._log.error("Could not find a datastore to initialize with!")
            exit(1)

        self._log.debug("Finished initializing vSphere")

    # From: create_folder_in_datacenter.py in pyvmomi-community-samples
    def create_folder(self, folder_name, create_in=None):
        """
        Creates a VM folder in the specified folder
        :param folder_name: Name of folder to create
        :param create_in: Name of folder or vim.Folder object to create folder in
        [default: root folder of datacenter]
        :return: The created vim.Folder object
        """
        if create_in:
            if type(create_in) is str:  # create_in is a string, so we look it up on the server
                self._log.debug("Retrieving parent folder '%s' from server", create_in)
                parent = self.get_folder(folder_name=create_in)
            else:
                parent = create_in  # create_in is a vim.Folder object, so we just assign it
        else:
            parent = self.content.rootFolder  # Default to using the server root folder
        return create_folder(folder=parent, folder_name=folder_name)

    def gen_clone_spec(self, datastore_name=None, pool_name=None):
        """
        Generates a clone specification used to clone a VM
        :param datastore_name: Name of datastore to put clone on [default: class-defined datastore]
        :param pool_name: Name of resource pool to use for the clone [default: first pool found]
        :return: vim.vm.CloneSpec object
        """
        if datastore_name:
            datastore = self.get_datastore(datastore_name)
        else:
            datastore = self.datastore
        relospec = vim.vm.RelocateSpec()
        relospec.pool = self.get_pool(pool_name)
        relospec.datastore = datastore

        clonespec = vim.vm.CloneSpec()
        clonespec.location = relospec
        return clonespec

    def set_motd(self, message):
        """
        Sets vCenter server Message of the Day (MOTD)
        :param message: Message to set
        """
        self._log.info("Setting vCenter MOTD to %s", message)
        self.content.sessionManager.UpdateServiceMessage(message=str(message))

    def set_entity_permissions(self, entity, permission):
        """
        Defines or updates rule(s) for the given user or group on the entity
        :param entity: vim.ManagedEntity, The entity on which to set permissions
        :param permission: vim.AuthorizationManager.Permission
        """
        try:
            self.auth.SetEntityPermissions(entity=entity, permission=permission)
        except vim.fault.UserNotFound as e:
            self._log.error("Could not find user '%s' to set permission '%s' on entity '%s'",
                            e.principal, str(permission), entity.name)
        except vim.fault.NotFound:
            self._log.error("Invalid role ID for permission '%s'", str(permission))
        except vmodl.fault.ManagedObjectNotFound as e:
            self._log.error("Entity '%s' does not exist to set permission on", str(e.obj))
        except vim.fault.NoPermission as e:
            self._log.error("Could not set permissions for entity '%s': the current session "
                            "does not have privilege '%s' to set permissions for the entity '%s'",
                            entity.name, e.privilegeId, e.object)
        except vmodl.fault.InvalidArgument as e:
            self._log.error("Invalid argument to set permission '%s' on entity '%s': %s",
                            entity.name, str(permission), str(e))
        except Exception as e:
            self._log.error("Unknown error while setting permissions for entity '%s': %s",
                            entity.name, str(e))

    def get_entity_permissions(self, entity, inherited=True):
        """
        Gets permissions defined on or effective on a managed entity
        :param entity: vim.ManagedEntity
        :param inherited: Include propagating permissions defined by parent entities [default: True]
        :return: vim.AuthorizationManager.Permission
        """
        try:
            return self.auth.RetrieveEntityPermissions(entity=entity, inherited=inherited)
        except vmodl.fault.ManagedObjectNotFound as e:
            self._log.error("Could not find entity '%s' to get permissions from", str(e.obj))
            return None

    def get_role_permissions(self, role_id):
        """
        Gets all permissions that use a particular role
        :param role_id: ID of the role
        :return: vim.AuthorizationManager.Permission
        """
        try:
            return self.auth.RetrieveRolePermissions(roleId=int(role_id))
        except vim.fault.NotFound:
            self._log.error("Role ID %s does not exist", str(role_id))
            return None

    def get_users(self, search='', domain='', exact=False,
                  belong_to_group=None, have_user=None,
                  find_users=True, find_groups=False):
        """
        Returns a list of the users and groups defined for the server.
        NOTE: You must hold the Authorization.ModifyPermissions privilege to invoke this method!
        :param search: Case insensitive substring used to filter results [default: all users]
        :param domain: Domain to be searched [default: local machine]
        :param exact: Search should match user/group name exactly [default: False]
        :param belong_to_group: Only find users/groups that directly belong
        to this group [default: None]
        :param have_user: Only find groups that directly contain this user [default: None]
        :param find_users: If users should be included in the results [default: True]
        :param find_groups: If groups should be included in the results [default: False]
        :return: List of vim.UserSearchResult
        """
        # See for reference: pyvmomi/docs/vim/UserDirectory.rst
        kwargs = {"searchStr": search, "exactMatch": exact,
                  "findUsers": find_users, "findGroups": find_groups}
        if domain != '':
            kwargs["domain"] = domain
        if belong_to_group is not None:
            kwargs["belongsToGroup"] = belong_to_group
        if have_user is not None:
            kwargs["belongsToUser"] = have_user

        try:
            return self.user_dir.RetrieveUserGroups(**kwargs)
        except vim.fault.NotFound:
            self._log.debug("Could not find domain, group or user in call to get_users"
                            "\nkwargs: %s", str(kwargs))
            return None
        except vmodl.fault.NotSupported:
            self._log.error("System doesn't support domains or by-membership queries for get_users")
            return None

    def get_info(self):
        """
        Retrieves and formats basic information about the vSphere instance
        :return: string with formatted server information
        """
        about = self.content.about
        info_string = "\n"
        info_string += "Host address: %s:%d\n" % (self.hostname, self.port)
        info_string += "Datacenter  : %s\n" % self.datacenter.name
        info_string += "Datastore   : %s\n" % self.datastore.name
        info_string += "Full name   : %s\n" % about.fullName
        info_string += "Vendor      : %s\n" % about.vendor
        info_string += "Version     : %s\n" % about.version
        info_string += "API type    : %s\n" % about.apiType
        info_string += "API version : %s\n" % about.apiVersion
        info_string += "OS type     : %s" % about.osType
        return info_string

    def get_folder(self, folder_name=None):
        """
        Finds and returns the named Folder
        :param folder_name: Name of the folder [default: Datacenter vmFolder]
        :return: vim.Folder object
        """
        if folder_name:  # Try to find the named folder in the datacenter
            return self.get_obj(self.datacenter, [vim.Folder], folder_name)
        else:  # Default to the VM folder in the datacenter
            self._log.debug("Could not find folder '%s' in Datacenter '%s', defaulting to vmFolder",
                            folder_name, self.datacenter.name)
            return self.datacenter.vmFolder  # Reference: pyvmomi/docs/vim/Datacenter.rst

    def get_vm(self, vm_name):
        """
        Finds and returns the named VM
        :param vm_name: Name of the VM
        :return: vim.VirtualMachine object
        """
        return self.get_item(vim.VirtualMachine, vm_name)

    def get_network(self, network_name, distributed=False):
        """
        Finds and returns the named Network
        :param network_name: Name of the Network
        :param distributed: If the Network is a Distributed PortGroup [default: False]
        :return: vim.Network or vim.dvs.DistributedVirtualPortgroup object
        """
        if not distributed:
            return find_in_folder(folder=self.datacenter.networkFolder, name=network_name,
                                  recursive=True, vimtype=vim.Network)
        else:
            return self.get_item(vim.dvs.DistributedVirtualPortgroup,  network_name)

    def get_host(self, host_name=None):
        """
        Finds and returns the named Host System
        :param host_name: Name of the host [default: first host found in datacenter]
        :return: vim.HostSystem object
        """
        return self.get_item(vim.HostSystem, host_name)

    def get_cluster(self, cluster_name=None):
        """
        Finds and returns the named Cluster
        :param cluster_name: Name of the cluster [default: first cluster found in datacenter]
        :return: vim.ClusterComputeResource object
        """
        return self.get_item(cluster_name, vim.ClusterComputeResource)

    def get_clusters(self):
        """
        Get all the clusters associated with the vCenter server
        :return: List of vim.ClusterComputeResource objects
        """
        return self.get_objs(self.content.rootFolder, [vim.ClusterComputeResource])

    def get_datastore(self, datastore_name=None):
        """
        Finds and returns the named Datastore
        :param datastore_name: Name of the datastore [default: first datastore found in datacenter]
        :return: vim.Datastore object
        """
        return get_in_folder(self.datacenter.datastoreFolder, datastore_name)

    def get_pool(self, pool_name=None):
        """
        Finds and returns the named Resource Pool
        :param pool_name: Name of the resource pool [default: first pool found in datacenter]
        :return: vim.ResourcePool object
        """
        return self.get_item(vim.ResourcePool, pool_name)

    def get_all_vms(self):
        """
        Finds and returns all VMs registered in the Datacenter
        :return: List of vim.VirtualMachine objects
        """
        return self.get_objs(self.datacenter.vmFolder, [vim.VirtualMachine])

    def get_obj(self, container, vimtypes, name, recursive=True):
        """
        Finds and returns named vSphere object of specified type
        :param vimtypes: List of vimtype objects to look for
        :param name: Name of the object
        :param container: Container to search in
        :param recursive: Recursively descend or only look in the current level [default: True]
        :return: The vimtype object found with the specified name, or None if no object was found
        """
        con_view = self.content.viewManager.CreateContainerView(container, vimtypes, recursive)
        obj = None
        for c in con_view.view:
            if c.name.lower() == name.lower():
                obj = c
                break
        con_view.Destroy()
        return obj

    # From: https://github.com/sijis/pyvmomi-examples/vmutils.py
    def get_objs(self, container, vimtypes, recursive=True):
        """
        Get all the vSphere objects associated with a given type
        :param vimtypes: Object to search for
        :param container: Container to search in
        :param recursive: Recursively descend or only look in the current level [default: True]
        :return: List of all vimtype objects found, or None if none were found
        """
        objs = []
        con_view = self.content.viewManager.CreateContainerView(container, vimtypes, recursive)
        for c in con_view.view:
            objs.append(c)
        con_view.Destroy()
        return objs

    def get_item(self, vimtype, name=None, container=None, recursive=True):
        """
        Get a item of specified name and type. Intended to be simple version of get_obj()
        :param vimtype: Type of item
        :param name: Name of item [default: None]
        :param container: Container to search in [default: vCenter server content root folder]
        :param recursive: Recursively descend or only look in the current level [default: True]
        :return: The item found
        """
        contain = (self.content.rootFolder if not container else container)
        if not name:
            return self.get_objs(contain, [vimtype], recursive)[0]
        else:
            return self.get_obj(contain, [vimtype], name, recursive)

    def map_items(self, vimtypes, func, name=None, container=None, recursive=True):
        """
        Apply a function to item(s)
        :param vimtypes: List of vimtype objects to look for
        :param func: Function to apply
        :param name: Name of item to apply to [default: None]
        :param container: Container to search in [default: content.rootFolder]
        :param recursive: Recursively descend or only look in the current level [default: True]
        :return: List of values returned from the function call(s)
        """
        contain = (self.content.rootFolder if not container else container)
        con_view = self.content.viewManager.CreateContainerView(contain, vimtypes, recursive)
        returns = []
        for item in con_view.view:
            if name:
                if hasattr(item, 'name') and item.name.lower() == name.lower():
                    returns.append(func(item))
            else:
                returns.append(func(item))
        con_view.Destroy()
        return returns

    def find_by_uuid(self, uuid, instance_uuid=True):
        """
        Find a VM in the datacenter with the given Instance or BIOS UUID
        :param uuid: UUID to search for (Instance or BIOS for VMs)
        :param instance_uuid: Search for VM Instance UUIDs, otherwise BIOS UUIDs [default: True]
        :return: vim.ManagedEntity
        """
        return self.content.searchIndex.FindByUuid(datacenter=self.datacenter,
                                                   uuid=str(uuid), vmSearch=True,
                                                   instanceUuid=instance_uuid)

    def find_by_ds_path(self, path):
        """
        Finds a VM by it's location on a Datastore
        :param path: Path to the VM's .vmx file on the Datastore
        :return: vim.VirtualMachine
        """
        try:
            return self.content.searchIndex.FindByDatastorePath(datacenter=self.datacenter,
                                                                path=str(path))
        except vim.fault.InvalidDatastore:
            self._log.error("Invalid datastore in path: %s", str(path))
            return None

    def find_by_ip(self, ip, vm_search=True):
        """
        Find a VM or Host using a IP address
        :param ip: IP address string as returned by VMware Tools ipAddress
        :param vm_search: Search for VMs if True, Hosts if False [default: True]
        :return: vim.ManagedEntity
        """
        return self.content.searchIndex.FindByIp(datacenter=self.datacenter,
                                                 ip=str(ip), vmSearch=vm_search)

    def find_by_hostname(self, hostname, vm_search=True):
        """
        Find a VM or Host using a fully-qualified domain name
        :param hostname: Fully-qualified domain name
        :param vm_search: Search for VMs if True, Hosts if False [default: True]
        :return: vim.ManagedEntity
        """
        return self.content.searchIndex.FindByDnsName(datacenter=self.datacenter,
                                                      dnsName=hostname, vmSearch=vm_search)

    def find_by_inv_path(self, path):
        """
        Finds a vim.ManagedEntity (VM, host, resource pool, folder, etc) in a inventory
        :param path: Path to the entity
        :return: vim.ManagedEntity
        """
        return self.content.searchIndex.FindByInventoryPath(inventoryPath=str(path))

    def __repr__(self):
        return "vSphere(%s, %s, %s:%s)" % (self.datacenter.name, self.datastore.name,
                                           self.hostname, self.port)

    def __str__(self):
        return str(self.get_info())

    def __hash__(self):
        return hash((self.hostname, self.port, self.username))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.hostname == other.hostname \
               and self.port == other.port and self.username == other.username

    def __ne__(self, other):
        return not self.__eq__(other)
