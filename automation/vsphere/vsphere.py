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

"""vSphere wrapper class. This entrypoint is used to test the class.

Usage:
    vsphere.py [-v] [-f FILE]
    vsphere.py --version
    vsphere.py (-h | --help)

Options:
    -h, --help          Shows this help
    --version           Prints current version
    -f, --file FILE     JSON file with server connection information
    -v, --verbose       Emits debugging logs to terminal in addition to a file

"""

from atexit import register
import logging

from pyVim.connect import SmartConnect, SmartConnectNoSSL, Disconnect
from pyVmomi import vim

# Must always use absolute imports when running as script (aka as '__main__')
from automation.vsphere.vsphere_utils import get_obj, get_objs, get_item, find_in_folder, get_in_dc

__version__ = "0.6.2"


class Vsphere:
    """ Maintains connection, logging, and constants for a vSphere instance """

    def __init__(self, username, password, hostname, datacenter=None, datastore=None, port=443, use_ssl=False):
        """
        Connects to the vCenter server instance and initializes class data members
        :param username: Username of account to login with
        :param password: Password of account to login with
        :param hostname: DNS hostname or IPv4 address of vCenter instance
        :param datastore: Name of datastore to use as default for operations [default: first datastore found on server]
        :param datacenter: Name of datacenter that will be used [default: First datacenter found on server]
        :param port: Port used to connect to vCenter instance [default: 443]
        """
        logging.debug("Initializing vSphere - Host: %s:%d\tUsername: %s\tDatacenter: %s\tDatastore: %s",
                      hostname, int(port), username, datacenter, datastore)
        if not password:
            from getpass import getpass
            password = getpass('Enter password for host %s and user %s: ' % (hostname, username))
        try:
            if use_ssl:  # Connect to server using SSL certificate verification
                self.server = SmartConnect(host=hostname, user=username, pwd=password, port=int(port))
            else:
                self.server = SmartConnectNoSSL(host=hostname, user=username, pwd=password, port=int(port))
        except Exception as e:
            logging.error("Error occurred while trying to connect to vCenter: %s", str(e))

        if not self.server:
            logging.error("Could not connect to host %s using specified username and password", hostname)
            raise Exception()

        register(Disconnect, self.server)  # Ensures connection to server is closed upon script termination

        self.user = username
        self.hostname = hostname
        self.port = port
        self.content = self.server.RetrieveContent()
        self.children = self.content.rootFolder.childEntity
        self.datacenter = get_item(self.content, vim.Datacenter, datacenter)
        self.datastore = self.get_datastore(datastore)

        logging.debug("Finished initializing vSphere")

    # From: create_folder_in_datacenter.py in pyvmomi-community-samples
    def create_folder(self, folder_name, create_in=None):
        """
        Creates a VM folder in the specified folder
        :param folder_name: Name of folder to create
        :param create_in: Name of folder or vim.Folder object to create folder in [default: root folder of datacenter]
        :return: The created vim.Folder object
        """
        if create_in:
            if type(create_in) is str:  # create_in is a string, so we look it up on the server
                logging.debug("Retrieving parent folder %s from server", create_in)
                parent = get_obj(self.content, [vim.Folder], create_in)
            else:
                parent = create_in  # create_in is a vim.Folder object, so we just assign it
            exists = find_in_folder(parent, folder_name)
            if exists:
                logging.warning("Folder %s already exists", folder_name)
                return exists
            else:
                logging.info("Creating folder %s in folder %s", folder_name, parent.name)
                return parent.CreateFolder(folder_name)
        else:
            logging.info("Creating folder %s in server root folder", folder_name)
            return self.content.rootFolder.CreateFolder(folder_name)

    # TODO: generate_vm_spec

    def generate_clone_spec(self, datastore_name=None, pool_name=None):
        """
        Generates a clone specification used to clone a VM
        :param datastore_name: (Optional) Name of the datastore in which to create the clone's disk
                                [default: first datastore found]
        :param pool_name: (Optional) Name of resource pool to use for the clone [default: first pool found]
        :return: vim.vm.CloneSpec object
        """
        if datastore_name:
            datastore = get_obj(self.content, [vim.Datastore], datastore_name)
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
        logging.info("Setting vCenter MOTD to %s", message)
        self.content.sessionManager.UpdateServiceMessage(message=message)

    def get_folder(self, folder_name=None):
        """
        Finds and returns the named folder
        :param folder_name: (Optional) Name of the folder [default: rootFolder of vCenter instance]
        :return: vim.Folder object
        """
        if folder_name:
            # TODO: specify which root to start (type of folder)
            return get_obj(self.content, [vim.Folder], folder_name)
        else:
            return self.datacenter.vmFolder  # S.f.r: pyvmomi/docs/vim/Datacenter.rst

    def get_vm(self, vm_name):
        """
        Finds and returns the named VM
        :param vm_name: Name of the VM
        :return: vim.VirtualMachine object
        """
        return get_obj(self.content, [vim.VirtualMachine], vm_name)

    def get_network(self, network_name=None, distributed=False):
        """
        Finds and returns the named PortGroup
        :param network_name: (Optional) Name of the portgroup [default: first portgroup in datacenter]
        :param distributed: (Optional) If the portgroup is a Distributed PortGroup [default: False]
        :return: vim.Network or vim.dvs.DistributedVirtualPortgroup object
        """
        if not distributed:
            return get_item(self.content, [vim.Network], network_name)
        else:
            return get_item(self.content, [vim.dvs.DistributedVirtualPortgroup], network_name)

    def get_host(self, host_name=None):
        """
        Finds and returns the named host
        :param host_name: (Optional) Name of the host [default: the first host found in the datacenter]
        :return: vim.HostSystem object
        """
        # return get_item(content=self.content, vimtype=vim.HostSystem, name=host_name)
        return get_in_dc(self.datacenter.hostFolder, host_name)

    def get_datastore(self, datastore_name=None):
        """
        Finds and returns the named datastore
        :param datastore_name: (Optional) Name of the datastore [default: first datastore found in the datacenter]
        :return: vim.Datastore object
        """
        # return get_item(content=self.content, vimtype=vim.Datastore, name=datastore_name)
        return get_in_dc(self.datacenter.datastoreFolder, datastore_name)

    def get_pool(self, pool_name=None):
        """
        Finds and returns the named resource pool
        :param pool_name: (Optional) Name of the resource pool [default: first resource pool found in the datacenter]
        :return: vim.ResourcePool object
        """
        return get_item(content=self.content, vimtype=vim.ResourcePool, name=pool_name)

    def get_all_vms(self):
        """
        Finds and returns ALL VMs registered in the datacenter
        :return: List of vim.VirtualMachine objects
        """
        return get_objs(self.content, [vim.VirtualMachine])

    def get_obj(self, vimtype, name, recursive=True):
        """
        Finds and returns named vSphere object of specified type
        :param vimtype: List of vimtype objects to look for
        :param name: string name of the object
        :param recursive: (Optional) Whether to recursively descend or only look in the current level
        :return: The vimtype object found with the specified name, or None if no object was found
        """
        get_obj(self.content, vimtype, name, recursive)

    def get_objs(self, vimtype, recursive=True):
        """
        Get all the vSphere objects associated with a given type
        :param vimtype: List of vimtype objects to look for
        :param recursive: (Optional) Whether to recursively descend or only look in the current level
        :return: List of all vimtype objects found, or None if none were found
        """
        get_objs(self.content, vimtype, recursive)

    def __repr__(self):
        return "vSphere({}, {}, {}:{})".format(self.datacenter.name, self.datastore.name, self.hostname, self.port)

    def __str__(self):
        return "Datacenter: {} \tDatastore: {} \tServer: {}:{}".format(self.datacenter.name, self.datastore.name,
                                                                       self.hostname, self.port)


def main():
    """ For testing of vSphere. Has examples of usage as well. """
    from docopt import docopt
    from automation.utils import setup_logging
    from automation.utils import make_vsphere
    import automation.vsphere.vm_utils as vm_utils  # Must always use absolute imports when running as script (__main__)

    args = docopt(__doc__, version=__version__, help=True)
    setup_logging(filename='vsphere-testing.log', console_level=logging.DEBUG if args["--verbose"] else logging.INFO)
    server = make_vsphere(args["--file"])

    vm = server.get_vm("dummy")
    vm_utils.print_vm_info(vm)

    # print(str(server))
    # print(repr(server))

    # folder = server.get_folder("script_testing")
    # vm = traverse_path(folder, "/Templates/Routers/VyOS 1.1.7 (64-bit)")
    # print_vm_info(vm)
    # folder = traverse_path(folder, "/Templates/Servers/Windows")
    # print(folder.name)

    # folder = server.get_folder("script_testing")
    # pool = get_objs(server.content, [vim.ResourcePool])[0]
    # file_info = vim.vm.FileInfo()
    # file_info.vmPathName = "[Datastore]"
    # vm_spec = vim.vm.ConfigSpec(name="test_vm", guestId="ubuntuGuest", numCPUs=1, numCoresPerSocket=1,
    #                             memoryMB=1024, annotation="it worked!", files=file_info)
    # create_vm(folder, vm_spec, pool)
    # attach_iso(vm, "ISO-Images/vyos-1.1.7-amd64.iso", server.get_datastore("Datastore"))

    # portgroup = get_obj(server.content, [vim.Network], "test_network")
    # add_nic(vm, portgroup, "test_summary")
    # edit_nic(vm, 2, summary="lol")
    # delete_nic(vm, 1)

    # create_portgroup("test_portgroup", server.get_host(), "test_vswitch")
    # delete_portgroup("test_portgroup", server.get_host())

if __name__ == '__main__':
    main()
