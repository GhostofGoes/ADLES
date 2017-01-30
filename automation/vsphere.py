#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from atexit import register

from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim


class vSphere:
    """ Maintains connection, logging, and constants for a vSphere instance """
    def __init__(self, user, password, host, port=443):
        self._log = logging.getLogger(__name__)
        if not password:
            from getpass import getpass
            password = getpass(prompt='Enter password for host %s and user %s: ' % (host, user))
        self.server = SmartConnect(host=host, user=user, pwd=password, port=int(port))
        if not self.server:
            print("Could not connect to the specified host using specified username and password")
            raise Exception()
        register(Disconnect, self.server)

    # From: create_folder_in_datacenter.py in pyvmomi-community-samples
    def create_folder(self, folder_name, datacenter, create_in):
        """
        Creates a VM folder in a datacenter
        :param folder_name: Name of folder to create
        :param datacenter: Name of datacenter where folder should be created
        :param create_in: Name of folder where new folder should be created
        :return:
        """
        content = self.server.RetrieveContent()
        if get_obj(content, [vim.Folder], folder_name): # TODO: this checks at vCenter level and not DC level?
            self._log.warning("Folder '%s' already exists" % folder_name)
        else:
            dc = get_obj(content, [vim.Datacenter], datacenter)
            # dc.vmFolder.CreateFolder(folder)
            parent = get_obj(dc.vmFolder.childEntity, [vim.Folder], create_in)
            parent.CreateFolder(folder_name)

    def convert_vm_to_template(self, vm, template_name):
        pass

    def change_vm_power_state(self, vm, power_state):
        """
        Power on, Power off, ACPI shutdown, Reset
        :param vm:
        :param power_state:
        :return:
        """
        pass

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
        content = self.server.RetrieveContent()
        nic_spec.device.backing.network = get_obj(content, [vim.Network], port_group)
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


# Helper functions
def get_obj(content, vimtype, name):
    """
    Finds and returns named object of specified type
    :param content:
    :param vimtype:
    :param name:
    :return:
    """
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
    return obj


def main():
    """ For testing of vSphere """
    from json import load
    from os import pardir, path
    # from pyVim.connect import SmartConnect, Disconnect
    # from atexit import register

    logging.basicConfig(filename='vsphere_testing.log', filemode='w', level=logging.DEBUG)

    with open(path.join(pardir, "logins.json"), "r") as login_file:
        logins = load(fp=login_file)["vsphere"]

    server = vSphere(logins["user"], logins["pass"], logins["host"], logins["port"])
    server.create_folder("testing", "r620", "script_testing")


if __name__ == '__main__':
    main()


