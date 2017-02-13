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

from atexit import register
import logging

from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim

from automation.vsphere.vsphere_utils import *
from automation.vsphere.vm_utils import *
from automation.vsphere.network_utils import *


class vSphere:
    """ Maintains connection, logging, and constants for a vSphere instance """

    def __init__(self, datacenter, username, password, hostname, port=443, datastore=None):
        """
        Connects to the vCenter server instance and initializes class data members
        :param datacenter: Name of datacenter that will be used (multiple datacenter support is TODO)
        :param username: Username of account to login with
        :param password: Password of account to login with
        :param hostname: DNS hostname or IPv4 address of vCenter instance
        :param datastore: Name of datastore to use as default for operations. Default: first datastore found
        :param port: Port used to connect to vCenter instance
        """
        logging.debug("Initializing vSphere...")
        from urllib.error import URLError
        if not password:
            from getpass import getpass
            password = getpass(prompt='Enter password for host %s and user %s: ' % (hostname, username))
        try:
            self.server = SmartConnect(host=hostname, user=username, pwd=password, port=int(port))  # Connect to server
        except URLError as e:
            logging.error("Your system does not trust the server's certificate. Follow instructions in the README to "
                          "install the certificate, or contact a lab administrator. "
                          "Here is the full error for your enjoyment: %s", str(e))
        if not self.server:
            logging.error("Could not connect to host %s using specified username and password", str(hostname))
            raise Exception()
        register(Disconnect, self.server)  # Ensures connection to server is closed upon script termination

        self.hostname = hostname
        self.port = port
        self.content = self.server.RetrieveContent()
        self.children = self.content.rootFolder.childEntity
        self.datacenter = get_obj(self.content, [vim.Datacenter], datacenter)
        if datastore:
            self.datastore = self.get_datastore(datastore_name=datastore)
        else:
            self.datastore = get_objs(self.content, [vim.Datastore])[0]

    # From: create_folder_in_datacenter.py in pyvmomi-community-samples
    def create_folder(self, folder_name, create_in=None):
        """
        Creates a VM folder in the specified folder
        :param folder_name: Name of folder to create
        :param create_in: Name of folder or vim.Folder object to create folder in [default: root folder of datacenter]
        """
        # if get_obj(self.content, [vim.Folder], folder_name):
        #    logging.warning("Folder {0} already exists".format(folder_name))
        if create_in:
            if type(create_in) is str:
                logging.debug("Retrieving parent folder %s from server", create_in)
                parent = get_obj(self.content, [vim.Folder], create_in)
            else:
                parent = create_in
            if find_in_folder(parent, folder_name):
                logging.warning("Folder {0} already exists".format(folder_name))
            else:
                logging.info("Creating folder {0} in folder {1}".format(folder_name, parent.name))
                parent.CreateFolder(folder_name)
        else:
            logging.info("Creating folder {0} in root folder".format(folder_name))
            self.content.rootFolder.CreateFolder(folder_name)

    # TODO: generate_vm_spec

    def generate_clone_spec(self, datastore_name=None, pool_name=None):
        """
        Generates a clone specification used to clone a VM
        :param datastore_name: (Optional) Name of the datastore in which to create the clone's disk
                                [default: first datastore found]
        :param pool_name: (Optional) Name of resource pool to use for the clone
        :return: vim.vm.CloneSpec object
        """
        if datastore_name:
            datastore = get_obj(self.content, [vim.Datastore], datastore_name)
        else:
            datastore = self.datastore
        relospec = vim.vm.RelocateSpec()
        clonespec = vim.vm.CloneSpec()
        if pool_name:
            pool = get_obj(self.content, [vim.ResourcePool], pool_name)
            relospec.pool = pool
        relospec.datastore = datastore
        clonespec.location = relospec
        return clonespec

    def set_motd(self, message):
        """
        Sets vCenter server Message of the Day (MOTD)
        :param message:
        """
        logging.info("Setting vCenter MOTD to {}".format(message))
        self.content.sessionManager.UpdateServiceMessage(message=message)

    def get_folder(self, folder_name=None):
        """
        Finds and returns the named folder
        :param folder_name: Name of the folder [default: rootFolder of vCenter instance]
        :return: vim.Folder object
        """
        if folder_name:
            return get_obj(self.content, [vim.Folder], folder_name)
        else:
            return self.content.rootFolder

    def get_vm(self, vm_name):
        """
        Finds and returns the named VM
        :param vm_name: Name of the VM
        :return: vim.VirtualMachine object
        """
        return get_obj(self.content, [vim.VirtualMachine], vm_name)

    def get_host(self, host_name=None):
        """
        Finds and returns the named host
        :param host_name: (Optional) Name of the host [default: the first host found in the datacenter]
        :return: vim.HostSystem object
        """
        if not host_name:
            return get_objs(self.content, [vim.HostSystem])[0]
        else:
            return get_obj(self.content, [vim.HostSystem], host_name)

    def get_datastore(self, datastore_name=None):
        """
        Finds and returns the named datastore
        :param datastore_name: (Optional) Name of the datastore [default: first datastore found in the datacenter]
        :return: vim.Datastore object
        """
        if not datastore_name:
            return get_objs(self.content, [vim.Datastore])[0]
        else:
            return get_obj(self.content, [vim.Datastore], datastore_name)

    def get_pool(self, pool_name=None):
        """
        Finds and returns the named resource pool
        :param pool_name: (Optional) Name of the resource pool [default: first resource pool found in the datacenter]
        :return: vim.ResourcePool object
        """
        if not pool_name:
            return get_objs(self.content, [vim.ResourcePool])[0]
        else:
            return get_obj(self.content, [vim.ResourcePool], pool_name)

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
    """ For testing of vSphere. Also has examples of wrapper API useage. """
    from json import load
    from os import pardir, path

    with open(path.join(pardir, "logins.json"), "r") as login_file:
        logins = load(fp=login_file)

    server = vSphere(datacenter="r620", username=logins["user"], password=logins["pass"], hostname=logins["host"],
                     port=logins["port"], datastore="Datastore")

    logging.basicConfig(level=logging.DEBUG,
                        format="[%(asctime)s] %(name)-12s %(levelname)-8s %(message)s",
                        datefmt="%y-%m-%d %H:%M:%S",
                        filename="vsphere-testing.log",
                        filemode='w')
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(levelname)-12s %(message)s")
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    # create_vswitch("cs439_vswitch", server.get_host())

    # vm = server.get_vm("dummy")
    # print_vm_info(vm)

    # print(str(server))
    # print(repr(server))

    # folder = server.get_folder("script_testing")
    # vm = traverse_path(folder, "/Templates/Clients/Linux/", "Kali 2016.2 (64-bit)")
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
