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


class Vsphere:
    """ Maintains connection, logging, and constants for a vSphere instance """
    __version__ = "1.0.2"

    def __init__(self, username=None, password=None, hostname=None,
                 datacenter=None, datastore=None,
                 port=443, use_ssl=False):
        """
        Connects to a vCenter server and initializes a class instance.

        :param str username: Username of account to login with
        [default: prompt user]
        :param str password: Password of account to login with
        [default: prompt user]
        :param str hostname: DNS hostname or IP address of vCenter instance
        [default: prompt user]
        :param str datastore: Name of datastore to use
        [default: first datastore found on server]
        :param str datacenter: Name of datacenter to use
        [default: First datacenter found on server]
        :param int port: Port used to connect to vCenter instance
        :param bool use_ssl: If SSL should be used to connect
        :raises LookupError: if a datacenter or datastore cannot be found
        """
        self._log = logging.getLogger('Vsphere')
        self._log.debug("Initializing Vsphere %s\nDatacenter: %s"
                        "\tDatastore: %s\tSSL: %s",
                        Vsphere.__version__, datacenter, datastore, use_ssl)

        if username is None:
            username = str(input("Enter username for vSphere: "))
        if password is None:
            from getpass import getpass
            password = str(getpass("Enter password for %s: " % username))
        if hostname is None:
            hostname = str(input("Enter hostname for vSphere: "))
        try:
            self._log.info("Connecting to vSphere: %s@%s:%d",
                           username, hostname, port)
            if use_ssl:  # Connect to server using SSL certificate verification
                self._server = SmartConnect(host=hostname, user=username,
                                            pwd=password, port=port)
            else:
                self._server = SmartConnectNoSSL(host=hostname, user=username,
                                                 pwd=password, port=port)
        except vim.fault.InvalidLogin:
            self._log.error("Invalid vSphere login credentials for user %s",
                            username)
            exit(1)
        except Exception as e:
            self._log.exception("Error connecting to vSphere: %s", str(e))
            exit(1)

        # Ensure connection to server is closed on program exit
        from atexit import register
        register(Disconnect, self._server)

        self._log.info("Connected to vSphere host %s:%d", hostname, port)
        self._log.debug("Current server time: %s",
                        str(self._server.CurrentTime()))

        self.username = username
        self.hostname = hostname
        self.port = port
        self.content = self._server.RetrieveContent()
        self.auth = self.content.authorizationManager
        self.user_dir = self.content.userDirectory
        self.search_index = self.content.searchIndex

        self.datacenter = self.get_item(vim.Datacenter, name=datacenter)
        if not self.datacenter:
            raise LookupError("Could not find a Datacenter to initialize with!")
        self.datastore = self.get_datastore(datastore)
        if not self.datastore:
            raise LookupError("Could not find a Datastore to initialize with!")
        self._log.debug("Finished initializing vSphere")

    # From: create_folder_in_datacenter.py in pyvmomi-community-samples
    def create_folder(self, folder_name, create_in=None):
        """
        Creates a VM folder in the specified folder.

        :param str folder_name: Name of folder to create
        :param create_in: Folder to create the new folder in
        [default: root folder of datacenter]
        :type create_in: str or vim.Folder
        :return: The created folder
        :rtype: vim.Folder
        """
        if create_in:
            if isinstance(create_in, str):  # Lookup creat_in on the server
                self._log.debug("Retrieving parent folder '%s' from server",
                                create_in)
                parent = self.get_folder(folder_name=create_in)
            else:
                parent = create_in  # Already vim.Folder, so we just assign it
        else:
            parent = self.content.rootFolder  # Default to server root folder
        return parent.create(folder_name)

    def set_motd(self, message):
        """
        Sets vCenter server Message of the Day (MOTD).

        :param str message: Message to set
        """
        self._log.info("Setting vCenter MOTD to %s", message)
        self.content.sessionManager.UpdateServiceMessage(message=str(message))

    def map_items(self, vimtypes, func, name=None,
                  container=None, recursive=True):
        """
        Apply a function to item(s) in a container.

        :param list vimtypes: List of vimtype objects to look for
        :param func: Function to apply
        :param str name: Name of item to apply to
        :param container: Container to search in [default: content.rootFolder]
        :param bool recursive: Whether to recursively descend
        :return: List of values returned from the function call(s)
        :rtype: list
        """
        contain = (self.content.rootFolder if not container else container)
        con_view = self.content.viewManager.CreateContainerView(contain,
                                                                vimtypes,
                                                                recursive)
        returns = []
        for item in con_view.view:
            if name:
                if hasattr(item, 'name') and item.name.lower() == name.lower():
                    returns.append(func(item))
            else:
                returns.append(func(item))
        con_view.Destroy()
        return returns

    def set_entity_permissions(self, entity, permission):
        """
        Defines or updates rule(s) for the given user or group on the entity.

        :param entity: The entity on which to set permissions
        :type entity: vim.ManagedEntity
        :param permission: The permission to set
        :type permission: vim.AuthorizationManager.Permission
        """
        try:
            self.auth.SetEntityPermissions(entity=entity, permission=permission)
        except vim.fault.UserNotFound as e:
            self._log.error("Could not find user '%s' to set permission "
                            "'%s' on entity '%s'",
                            e.principal, str(permission), entity.name)
        except vim.fault.NotFound:
            self._log.error("Invalid role ID for permission '%s'",
                            str(permission))
        except vmodl.fault.ManagedObjectNotFound as e:
            self._log.error("Entity '%s' does not exist to set permission on",
                            str(e.obj))
        except vim.fault.NoPermission as e:
            self._log.error("Could not set permissions for entity '%s': "
                            "the current session does not have privilege '%s' "
                            "to set permissions for the entity '%s'",
                            entity.name, e.privilegeId, e.object)
        except vmodl.fault.InvalidArgument as e:
            self._log.error("Invalid argument to set permission '%s' "
                            "on entity '%s': %s",
                            entity.name, str(permission), str(e))
        except Exception as e:
            self._log.exception("Unknown error while setting permissions "
                                "for entity '%s': %s",
                                entity.name, str(e))

    def get_entity_permissions(self, entity, inherited=True):
        """
        Gets permissions defined on or effective on a managed entity.

        :param entity: The entity to get permissions for
        :type entity: vim.ManagedEntity
        :param bool inherited: Include propagating permissions
        defined in parent
        :return: The permissions for the entity
        :rtype: vim.AuthorizationManager.Permission or None
        """
        try:
            return self.auth.RetrieveEntityPermissions(entity=entity,
                                                       inherited=inherited)
        except vmodl.fault.ManagedObjectNotFound as e:
            self._log.error("Couldn't find entity '%s' to get permissions from",
                            str(e.obj))
            return None

    def get_role_permissions(self, role_id):
        """
        Gets all permissions that use a particular role.

        :param int role_id: ID of the role
        :return: The role permissions
        :rtype: vim.AuthorizationManager.Permission or None
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
        Returns a list of the users and groups defined for the server

        .. note:: You must hold the Authorization.ModifyPermissions 
        privilege to invoke this method.

        :param str search: Case insensitive substring used to filter results
        [default: all users]
        :param str domain: Domain to be searched [default: local machine]
        :param bool exact: Search should match user/group name exactly
        :param str belong_to_group: Only find users/groups that directly belong
        to this group
        :param str have_user: Only find groups that directly contain this user
        :param bool find_users: Include users in results
        :param bool find_groups: Include groups in results
        :return: The users and groups defined for the server
        :rtype: list(vim.UserSearchResult) or None
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
            self._log.warning("Could not find domain, group or user "
                              "in call to get_users"
                              "\nkwargs: %s", str(kwargs))
            return None
        except vmodl.fault.NotSupported:
            self._log.error("System doesn't support domains or "
                            "by-membership queries for get_users")
            return None

    def get_info(self):
        """
        Retrieves and formats basic information about the vSphere instance.

        :return: formatted server information
        :rtype: str
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
        Finds and returns the named Folder.

        :param str folder_name: Name of folder [default: Datacenter vmFolder]
        :return: The folder found
        :rtype: vim.Folder
        """
        if folder_name:  # Try to find the named folder in the datacenter
            return self.get_obj(self.datacenter, [vim.Folder], folder_name)
        else:  # Default to the VM folder in the datacenter
            # Reference: pyvmomi/docs/vim/Datacenter.rst
            self._log.warning("Could not find folder '%s' in Datacenter '%s', "
                              "defaulting to vmFolder",
                              folder_name, self.datacenter.name)
            return self.datacenter.vmFolder

    def get_vm(self, vm_name):
        """
        Finds and returns the named VM.

        :param str vm_name: Name of the VM
        :return: The VM found
        :rtype: vim.VirtualMachine or None
        """
        return self.get_item(vim.VirtualMachine, vm_name)

    def get_network(self, network_name, distributed=False):
        """
        Finds and returns the named Network.

        :param str network_name: Name or path of the Network
        :param bool distributed: If the Network is a Distributed PortGroup
        :return: The network found
        :rtype: vim.Network or vim.dvs.DistributedVirtualPortgroup or None
        """
        if not distributed:
            return self.get_obj(container=self.datacenter.networkFolder,
                                vimtypes=[vim.Network],
                                name=str(network_name), recursive=True)
        else:
            return self.get_item(vim.dvs.DistributedVirtualPortgroup,
                                 network_name)

    def get_host(self, host_name=None):
        """
        Finds and returns the named Host System.

        :param str host_name: Name of the host
        [default: first host found in datacenter]
        :return: The host found
        :rtype: vim.HostSystem or None
        """
        return self.get_item(vim.HostSystem, host_name)

    def get_cluster(self, cluster_name=None):
        """
        Finds and returns the named Cluster.

        :param str cluster_name: Name of the cluster
        [default: first cluster found in datacenter]
        :return: The cluster found
        :rtype: vim.ClusterComputeResource or None
        """
        return self.get_item(cluster_name, vim.ClusterComputeResource)

    def get_clusters(self):
        """
        Get all the clusters associated with the vCenter server.

        :return: All clusters associated with the vCenter server
        :rtype: list(vim.ClusterComputeResource)
        """
        return self.get_objs(self.content.rootFolder,
                             [vim.ClusterComputeResource])

    def get_datastore(self, datastore_name=None):
        """
        Finds and returns the named Datastore.

        :param str datastore_name: Name of the datastore
        [default: first datastore in datacenter]
        :return: The datastore found
        :rtype: vim.Datastore or None
        """
        return self.datacenter.datastoreFolder.get(datastore_name)

    def get_pool(self, pool_name=None):
        """
        Finds and returns the named vim.ResourcePool.

        :param str pool_name: Name of the resource pool
        [default: first pool found in datacenter]
        :return: The resource pool found
        :rtype: vim.ResourcePool or None
        """
        return self.get_item(vim.ResourcePool, pool_name)

    def get_all_vms(self):
        """
        Finds and returns all VMs registered in the Datacenter.

        :return: All VMs in the Datacenter defined for the class
        :rtype: list(vim.VirtualMachine)
        """
        return self.get_objs(self.datacenter.vmFolder, [vim.VirtualMachine])

    def get_obj(self, container, vimtypes, name, recursive=True):
        """
        Finds and returns named vim object of specified type.

        :param container: Container to search in
        :param list vimtypes: vimtype objects to look for
        :param str name: Name of the object
        :param bool recursive: Recursively search for the item
        :return: Object found with the specified name
        :rtype: vimtype or None
        """
        con_view = self.content.viewManager.CreateContainerView(container,
                                                                vimtypes,
                                                                recursive)
        obj = None
        for item in con_view.view:
            if item.name.lower() == name.lower():
                obj = item
                break
        con_view.Destroy()
        return obj

    # From: https://github.com/sijis/pyvmomi-examples/vmutils.py
    def get_objs(self, container, vimtypes, recursive=True):
        """
        Get all the vim objects associated with a given type.

        :param container: Container to search in
        :param list vimtypes: Objects to search for
        :param bool recursive: Recursively search for the item
        :return: All vimtype objects found
        :rtype: list(vimtype) or None
        """
        objs = []
        con_view = self.content.viewManager.CreateContainerView(container,
                                                                vimtypes,
                                                                recursive)
        for item in con_view.view:
            objs.append(item)
        con_view.Destroy()
        return objs

    def get_item(self, vimtype, name=None, container=None, recursive=True):
        """
        Get a item of specified name and type.
        Intended to be simple version of :meth: get_obj

        :param vimtype: Type of item
        :type vimtype: vimtype
        :param str name: Name of item
        :param container: Container to search in
        [default: vCenter server content root folder]
        :param bool recursive: Recursively search for the item
        :return: The item found
        :rtype: vimtype or None
        """
        contain = (self.content.rootFolder if not container else container)
        if not name:
            return self.get_objs(contain, [vimtype], recursive)[0]
        else:
            return self.get_obj(contain, [vimtype], name, recursive)

    def find_by_uuid(self, uuid, instance_uuid=True):
        """
        Find a VM in the datacenter with the given Instance or BIOS UUID.

        :param str uuid: UUID to search for (Instance or BIOS for VMs)
        :param bool instance_uuid: If True, search by VM Instance UUID, 
        otherwise search by BIOS UUID
        :return: The VM found
        :rtype: vim.VirtualMachine or None
        """
        return self.search_index.FindByUuid(datacenter=self.datacenter,
                                            uuid=str(uuid), vmSearch=True,
                                            instanceUuid=instance_uuid)

    def find_by_ds_path(self, path):
        """
        Finds a VM by it's location on a Datastore.

        :param str path: Path to the VM's .vmx file on the Datastore
        :return: The VM found
        :rtype: vim.VirtualMachine or None
        """
        try:
            return self.search_index.FindByDatastorePath(
                datacenter=self.datacenter, path=str(path))
        except vim.fault.InvalidDatastore:
            self._log.error("Invalid datastore in path: %s", str(path))
            return None

    def find_by_ip(self, ip, vm_search=True):
        """
        Find a VM or Host using a IP address.

        :param str ip: IP address string as returned by VMware Tools ipAddress
        :param vm_search: Search for VMs if True, Hosts if False
        :return: The VM or host found
        :rtype: vim.VirtualMachine or vim.HostSystem or None
        """
        return self.search_index.FindByIp(datacenter=self.datacenter,
                                          ip=str(ip), vmSearch=vm_search)

    def find_by_hostname(self, hostname, vm_search=True):
        """
        Find a VM or Host using a Fully-Qualified Domain Name (FQDN).

        :param str hostname: FQDN of the VM to find
        :param vm_search: Search for VMs if True, Hosts if False
        :return: The VM or host found
        :rtype: vim.VirtualMachine or vim.HostSystem or None
        """
        return self.search_index.FindByDnsName(datacenter=self.datacenter,
                                               dnsName=hostname,
                                               vmSearch=vm_search)

    def find_by_inv_path(self, path, datacenter=None):
        """
        Finds a vim.ManagedEntity (VM, host, folder, etc) in a inventory.

        :param str path: Path to the entity. This must include the hidden 
        Vsphere folder for the type: vm | network | datastore | host
        Example: "vm/some-things/more-things/vm-name"
        :param str datacenter: Name of datacenter to search in
        [default: instance's datacenter]
        :return: The entity found
        :rtype: vim.ManagedEntity or None
        """
        if datacenter is None:
            datacenter = self.datacenter.name
        full_path = datacenter + "/" + str(path)
        return self.search_index.FindByInventoryPath(inventoryPath=full_path)

    def __repr__(self):
        return "vSphere(%s, %s, %s:%s)" % (self.datacenter.name,
                                           self.datastore.name,
                                           self.hostname, self.port)

    def __str__(self):
        return str(self.get_info())

    def __hash__(self):
        return hash((self.hostname, self.port, self.username))

    def __eq__(self, other):
        return isinstance(other, self.__class__) \
               and self.hostname == other.hostname \
               and self.port == other.port \
               and self.username == other.username

    def __ne__(self, other):
        return not self.__eq__(other)
