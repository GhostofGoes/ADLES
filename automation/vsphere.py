#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from atexit import register

from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim

from automation.vsphere_utils import *
from automation.vm_utils import *


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

    # From: add_nic_to_vm.py in pyvmomi-community-samples
    def add_nic_to_vm(self, vm, port_group, summary="default"):
        """
        Add a NIC in the portgroup to the VM
        :param vm: vim.VirtualMachine
        :param port_group: Name of the port group to use
        :param summary: (Optional) Human-readable device info
        """
        print("Adding NIC to VM {0}. Port group: {1} Summary: {2}".format(vm.name, port_group, summary))
        nic_spec = vim.vm.device.VirtualDeviceSpec()
        nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add

        nic_spec.device = vim.vm.device.VirtualE1000()
        nic_spec.device.addressType = 'assigned'

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

        edit_vm(vm, vim.vm.ConfigSpec(deviceChange=[nic_spec]))

    def add_iso_to_vm(self, vm, filename, datastore=None):
        """
        Attaches an ISO image to a VM
        :param vm: vim.VirtualMachine
        :param filename: Name of the ISO image to attach
        :param datastore: (Optional) vim.Datastore where the ISO resides. Default: class-defined datastore
        """
        print("Adding ISO '{0}' to VM '{1}'".format(filename, vm.name))
        drive_spec = vim.vm.device.VirtualDeviceSpec()
        drive_spec.device = vim.vm.device.VirtualCdrom()
        drive_spec.device.controllerKey = find_free_ide_controller(vm).key
        drive_spec.device.key = -1
        drive_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        drive_spec.device.backing = vim.vm.device.VirtualCdrom.IsoBackingInfo()
        if datastore:
            drive_spec.device.backing.datastore = datastore
        else:
            drive_spec.device.backing.datastore = self.datastore
        drive_spec.device.backing.fileName = "[{0}] {1}".format(drive_spec.device.backing.datastore.name, filename)
        drive_spec.device.unitNumber = 0

        drive_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
        drive_spec.device.connectable.allowGuestControl = True
        drive_spec.device.connectable.startConnected = True
        drive_spec.device.connectable.connected = True

        # cdrom = vim.vm.device.VirtualCdrom()
        # cdrom.controllerKey = find_free_ide_controller(vm).key
        # cdrom.key = -1
        # cdrom.connectable = connectable
        # cdrom.backing = backing
        edit_vm(vm, vim.vm.ConfigSpec(deviceChange=[drive_spec]))

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
    server = vSphere(datacenter="r620", username=logins["user"], password=logins["pass"], hostname=logins["host"],
                     port=logins["port"], datastore="Datastore")

    # folder = server.get_folder("script_testing")
    # pool = get_objs(server.content, [vim.ResourcePool])[0]
    # file_info = vim.vm.FileInfo()
    # file_info.vmPathName = "[Datastore]"
    # vm_spec = vim.vm.ConfigSpec(name="test_vm", guestId="ubuntuGuest", numCPUs=1, numCoresPerSocket=1,
    #                             memoryMB=1024, annotation="it worked!", files=file_info)
    # create_vm(folder, vm_spec, pool)

    vm = server.get_vm("dummy")
    # server.add_iso_to_vm(vm, "ISO-Images/vyos-1.1.7-amd64.iso")
    # server.add_nic_to_vm(vm, "test_network", "test_summary")
    delete_nic(vm, 1)

if __name__ == '__main__':
    main()
