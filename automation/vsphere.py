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
        # self._log = logging.getLogger(__name__)
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
        Creates a VM folder in a datacenter
        :param folder_name: Name of folder to create
        :param create_in: Name of folder where new folder should be created
        """
        if get_obj(self.content, [vim.Folder], folder_name):
            print("Folder {0} already exists".format(folder_name))
        else:
            print("Creating folder {0} in folder {1}".format(folder_name, create_in))
            parent = get_obj(self.content, [vim.Folder], create_in)
            parent.CreateFolder(folder_name)

    # From: add_nic_to_vm.py in pyvmomi-community-samples
    def add_nic_to_vm(self, vm, port_group, summary='default'):
        """
        Add a NIC in the specified portgroup to the specified VM.
        :param vm: Virtual Machine Object
        :param port_group: Virtual Port Group
        :param summary: Device Info summary string
        """
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


def main():
    """ For testing of vSphere """
    from json import load
    from os import pardir, path

    with open(path.join(pardir, "logins.json"), "r") as login_file:
        logins = load(fp=login_file)["vsphere"]

    # TODO: add capability to wait on tasks and provide status (important for long-running deploys/clones)
    server = vSphere("r620", logins["user"], logins["pass"], logins["host"], logins["port"])

    vm = server.get_vm("dummy")
    print_vm_info(vm)


if __name__ == '__main__':
    main()


