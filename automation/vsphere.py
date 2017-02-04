#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from atexit import register

from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim

from automation.vsphere_utils import *
from automation.vm_utils import *
from automation.network_utils import *


class vSphere:
    """ Maintains connection, logging, and constants for a vSphere instance """
    def __init__(self, datacenter, username, password, hostname, port=443, datastore=None):
        """
        Connects to the vCenter server instance and initializes class data members
        :param datacenter: Name of datacenter that will be used (multiple datacenter support is TODO)
        :param username:
        :param password:
        :param hostname: DNS hostname or IPv4 address of vCenter instance
        :param datastore: Name of datastore to use as default for operations. Default: first datastore found
        :param port: Port used to connect to vCenter instance
        """
        from urllib.error import URLError
        # TODO: colored logs (https://pypi.python.org/pypi/coloredlogs/)
        if not password:
            from getpass import getpass
            password = getpass(prompt='Enter password for host %s and user %s: ' % (hostname, username))
        try:
            self.server = SmartConnect(host=hostname, user=username, pwd=password, port=int(port))  # Connect to server
        except URLError as e:
            print("Your system does not trust the server's certificate. Follow instructions in the README to "
                  "install the certificate, or contact a lab administrator.")
            print("Here is the full error for your enjoyment: ", str(e))
        if not self.server:
            print("Could not connect to the specified host using specified username and password")
            raise Exception()
        register(Disconnect, self.server)  # Ensures connection to server is closed upon script termination

        self.content = self.server.RetrieveContent()
        self.children = self.content.rootFolder.childEntity
        self.datacenter = get_obj(self.content, [vim.Datacenter], datacenter)
        if datastore:
            self.datastore = self.get_datastore(datastore_name=datastore)
        else:
            self.datastore = get_objs(self.content, [vim.Datastore])[0]

    # From: create_folder_in_datacenter.py in pyvmomi-community-samples
    def create_folder(self, folder_name, create_in):
        """
        Creates a VM folder in the specified folder
        :param folder_name: Name of folder to create
        :param create_in: Name of folder where new folder should be created
        """
        if get_obj(self.content, [vim.Folder], folder_name):
            print("Folder {0} already exists".format(folder_name))
        else:
            print("Creating folder {0} in folder {1}".format(folder_name, create_in))
            parent = get_obj(self.content, [vim.Folder], create_in)
            parent.CreateFolder(folder_name)

    def generate_clone_spec(self, datastore_name, pool_name=None):
        """
        Generates a clone specification used to clone a VM
        :param datastore_name: Name of the datastore in which to create the clone's disk
        :param pool_name: Name of resource pool to use for the clone
        :return: vim.vm.CloneSpec object
        """
        datastore = get_obj(self.content, [vim.Datastore], datastore_name)
        relospec = vim.vm.RelocateSpec()
        clonespec = vim.vm.CloneSpec()
        if pool_name:
            pool = get_obj(self.content, [vim.ResourcePool], pool_name)
            relospec.pool = pool
        relospec.datastore = datastore
        clonespec.location = relospec
        return clonespec

    def get_folder(self, folder_name):
        """
        Finds and returns the named folder
        :param folder_name: Name of the folder
        :return: vim.Folder object
        """
        return get_obj(self.content, [vim.Folder], folder_name)

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
        :param host_name: (Optiona) Name of the host [default: the first host found in the datacenter]
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

    def get_pool(self, pool_name):
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


# TODO: unit tests
def main():
    """ For testing of vSphere """
    from json import load
    from os import pardir, path

    with open(path.join(pardir, "logins.json"), "r") as login_file:
        logins = load(fp=login_file)["vsphere"]

    # TODO: add capability to wait on tasks and provide status (important for long-running deploys/clones)
    #   Idea: create a task queue, place all the tasks i need done in-order, then run them all using wait_for_tasks
    server = vSphere(datacenter="r620", username=logins["user"], password=logins["pass"], hostname=logins["host"],
                     port=logins["port"], datastore="Datastore")

    # folder = server.get_folder("script_testing")
    # pool = get_objs(server.content, [vim.ResourcePool])[0]
    # file_info = vim.vm.FileInfo()
    # file_info.vmPathName = "[Datastore]"
    # vm_spec = vim.vm.ConfigSpec(name="test_vm", guestId="ubuntuGuest", numCPUs=1, numCoresPerSocket=1,
    #                             memoryMB=1024, annotation="it worked!", files=file_info)
    # create_vm(folder, vm_spec, pool)
    # vm = server.get_vm("test_vm")

    # attach_iso(vm, "ISO-Images/vyos-1.1.7-amd64.iso", server.get_datastore("Datastore"))
    # portgroup = get_obj(server.content, [vim.Network], "test_network")
    # add_nic(vm, portgroup, "test_summary")
    # edit_nic(vm, 2, summary="lol")
    # delete_nic(vm, 1)
    # create_portgroup("test_portgroup", server.get_host(), "test_vswitch")
    # delete_portgroup("test_portgroup", server.get_host())
    # print_datastore_info(server.get_datastore())

if __name__ == '__main__':
    main()
