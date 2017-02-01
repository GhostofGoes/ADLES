#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from atexit import register

from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim

from automation.vsphere_utils import *


class vSphere:
    """ Maintains connection, logging, and constants for a vSphere instance """
    def __init__(self, user, password, host, port=443):
        from urllib.error import URLError
        # self._log = logging.getLogger(__name__)
        # TODO: colored logs (https://pypi.python.org/pypi/coloredlogs/)
        if not password:
            from getpass import getpass
            password = getpass(prompt='Enter password for host %s and user %s: ' % (host, user))
        try:
            self.server = SmartConnect(host=host, user=user, pwd=password, port=int(port))  # Connect to server
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

    # From: create_folder_in_datacenter.py in pyvmomi-community-samples
    def create_folder(self, folder_name, create_in):
        """
        Creates a VM folder in a datacenter
        :param folder_name: Name of folder to create
        :param create_in: Name of folder where new folder should be created
        :return:
        """
        if get_obj(self.content, [vim.Folder], folder_name):
            print("Folder '%s' already exists" % folder_name)
        else:
            parent = get_obj(self.content, [vim.Folder], create_in)
            parent.CreateFolder(folder_name)

    @staticmethod
    def convert_to_template(vm):
        """
        Converts a VM to a template
        :param vm:
        :param template_name:
        :return:
        """
        try:
            vm.MarkAsTemplate()
        except vim.fault.InvalidPowerState:
            print("(ERROR) VM {0} must be powered off before being converted to a template!".format(vm.name))

    def change_vm_power_state(self, vm, power_state):
        """
        Changes a VM power state to the state specified.
        Options for power_state: on, off, reset, suspend
        :param vm: vim.VirtualMachine
        :param power_state: str
        :return:
        """
        print("Changing power state of VM {0} to: '{1}'".format(vm.name, power_state))
        if power_state.lower() == "on": # TODO: (power on using Datacenter.PowerOnMultiVM, as PowerOnVM is deprecated)
            pass
        elif power_state.lower() == "off":
            vm.PowerOffVM_Task()
        elif power_state.lower() == "reset":
            vm.ResetVM_Task()
        elif power_state.lower() == "suspend":
            vm.SuspendVM_Task()

    def change_vm_guest_state(self, vm, guest_state):
        """
        Changes a VMs guest power state. VMware Tools must be installed on the VM for this to work.
        Options for guest_state: shutdown, reboot, standby
        :param vm:  vim.VirtualMachine
        :param guest_state:  str
        :return:
        """
        print("Changing guest power state of VM {0} to: '{1}'".format(vm.name, guest_state))
        if vm.summary.guest.toolsStatus == "toolsNotInstalled":
            print("(ERROR) Cannot change a VM's guest power state without VMware Tools!")
            return

        if guest_state.lower() == "shutdown":
            vm.ShutdownGuest()
        elif guest_state.lower() == "reboot":
            vm.RebootGuest()
        elif guest_state.lower() == "standby":
            vm.StandbyGuest()
        else:
            print("(ERROR) Invalid guest_state argument!")

    @staticmethod
    def set_vm_note(vm, note):
        """
        Sets the note on the VM to note
        :param vm: vim.VirtualMachine
        :param note: str
        :return:
        """
        spec = vim.vm.ConfigSpec()
        spec.annotation = note
        vm.ReconfigVM_Task(spec)

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

    def get_folder(self, folder_name):
        """
        Finds and returns the named folder
        :param folder_name:
        :return:
        """
        return get_obj(self.content, [vim.Folder], folder_name)

    def get_vm(self, vm_name):
        """
        Finds and returns the named VM
        :param vm_name:
        :return:
        """
        return get_obj(self.content, [vim.VirtualMachine], vm_name)


def main():
    """ For testing of vSphere """
    from json import load
    from os import pardir, path

    with open(path.join(pardir, "logins.json"), "r") as login_file:
        logins = load(fp=login_file)["vsphere"]

    # TODO: task waiting
    server = vSphere(logins["user"], logins["pass"], logins["host"], logins["port"])

    vm = server.get_vm("dummy2")
    print_vm_info(vm)


if __name__ == '__main__':
    main()


