#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from atexit import register

from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim

from automation.vsphere_utils import *
from automation.vm_utils import *


class vSphere:
    """ Maintains connection, logging, and constants for a vSphere instance """
    def __init__(self, datacenter, username, password, hostname, port=443):
        """
        Connects to the vCenter server instance and initializes class data members
        :param datacenter: Name of datacenter that will be used (multiple datacenter support is TODO)
        :param username:
        :param password:
        :param hostname: DNS hostname or IPv4 address of vCenter instance
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

    # From: add_nic_to_vm.py in pyvmomi-community-samples
    def add_nic_to_vm(self, vm, port_group, summary='default'):
        """
        Add a NIC in the specified portgroup to the specified VM.
        :param vm: Virtual Machine Object
        :param port_group: Virtual Port Group
        :param summary: Device Info summary string
        """
        print("Adding NIC to VM {0}. Port group: {1} Summary: {2}".format(vm.name, port_group.name, summary))
        nic_spec = vim.vm.device.VirtualDeviceSpec()
        nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add

        nic_spec.device = vim.vm.device.VirtualE1000()

        nic_spec.device.deviceInfo = vim.Description()
        nic_spec.device.deviceInfo.summary = summary

        nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
        nic_spec.device.backing.useAutoDetect = False
        nic_spec.device.backing.network = get_obj(self.content, [vim.Network], port_group)
        nic_spec.device.backing.deviceName = port_group

        nic_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
        nic_spec.device.connectable.startConnected = True
        nic_spec.device.connectable.allowGuestControl = True
        nic_spec.device.connectable.connected = False
        nic_spec.device.connectable.status = 'untried'
        nic_spec.device.addressType = 'assigned'

        spec = vim.vm.ConfigSpec()
        spec.deviceChange = [nic_spec]
        vm.ReconfigVM_Task(spec=spec)

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

    def get_host(self, host_name):
        """
        Finds and returns the named host
        :param host_name: Name of the host
        :return: vim.HostSystem object
        """
        return get_obj(self.content, [vim.HostSystem], host_name)

    def get_datastore(self, datastore_name):
        """
        Finds and returns the named datastore
        :param datastore_name: Name of the datastore
        :return: vim.Datastore object
        """
        return get_obj(self.content, [vim.Datastore], datastore_name)

    def get_pool(self, pool_name):
        """
        Finds and returns the named resource pool
        :param pool_name: Name of the resource pool
        :return: vim.ResourcePool object
        """
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
    server = vSphere("r620", logins["user"], logins["pass"], logins["host"], logins["port"])


if __name__ == '__main__':
    main()


