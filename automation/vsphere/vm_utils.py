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
from pyVmomi import vim

from automation.vsphere.vsphere_utils import wait_for_task
from automation.utils import time_execution


@time_execution
def clone_vm(vm, folder, name, clone_spec):
    """
    Creates a clone of the VM or Template
    :param vm: vim.VirtualMachine object
    :param folder: vim.Folder object in which to create the clone
    :param name: String name of the new VM
    :param clone_spec: vim.vm.CloneSpec for the new VM
    """
    logging.info("Cloning VM %s to folder %s with name %s", vm.name, folder.name, name)
    # CloneSpec docs: pyvmomi/docs/vim/vm/CloneSpec.rst
    if is_template(vm) and not bool(clone_spec.location.pool):
        logging.error("Cannot clone template %s without specifying a pool", vm.name)
    else:
        wait_for_task(task=vm.CloneVM_Task(folder=folder, name=name, spec=clone_spec))


@time_execution
def create_vm(folder, config, pool, host=None):
    """
    Creates a VM with the specified configuration in the given folder
    :param folder: vim.Folder in which to create the VM
    :param config: vim.vm.ConfigSpec defining the new VM
    :param pool: vim.ResourcePool to which the virtual machine will be attached
    :param host: (Optional) vim.HostSystem on which the VM will run
    """
    logging.info("Creating VM %s in folder %s", config.name, folder.name)
    wait_for_task(task=folder.CreateVM_Task(config, pool, host))


@time_execution
def destroy_vm(vm):
    """
    Destroys a Virtual Machine
    :param vm: vim.VirtualMachine object
    """
    name = vm.name
    logging.info("Destroying VM %s", name)
    if powered_on(vm):
        logging.info("VM %s is still on, powering off before destroying...", name)
        wait_for_task(change_power_state(vm, "off"))
    wait_for_task(task=vm.Destroy_Task())


def edit_vm(vm, config):
    """
    Edit a VM using the given configuration
    :param vm: vim.VirtualMachine object
    :param config: vim.vm.ConfigSpec object
    """
    logging.info("Reconfiguring VM %s", vm.name)
    wait_for_task(vm.ReconfigVM_Task(config))


def change_power_state(vm, power_state):
    """
    Changes a VM power state to the state specified
    :param vm: vim.VirtualMachine object to change power state of
    :param power_state: on, off, reset, or suspend
    :return: vim.Task
    """
    logging.debug("Changing power state of VM %s to: '%s'", vm.name, power_state)
    if power_state.lower() == "on":
        return vm.PowerOnVM_Task()
    elif power_state.lower() == "off":
        return vm.PowerOffVM_Task()
    elif power_state.lower() == "reset":
        return vm.ResetVM_Task()
    elif power_state.lower() == "suspend":
        return vm.SuspendVM_Task()
    else:
        logging.error("Invalid power_state %s for VM %s", power_state, vm.name)
    return None


def change_guest_state(vm, guest_state):
    """
    Changes a VMs guest power state. VMware Tools must be installed on the VM for this to work.
    :param vm:  vim.VirtualMachine object to change guest state of
    :param guest_state: shutdown, reboot, or standby
    :return: vim.Task
    """
    logging.debug("Changing guest power state of VM %s to: '%s'", vm.name, guest_state)
    if vm.summary.guest.toolsStatus == "toolsNotInstalled":
        logging.error("Cannot change a VM's guest power state without VMware Tools!")
    elif guest_state.lower() == "shutdown":
        return vm.ShutdownGuest()
    elif guest_state.lower() == "reboot":
        return vm.RebootGuest()
    elif guest_state.lower() == "standby":
        return vm.StandbyGuest()
    else:
        logging.error("Invalid guest_state argument: %s", guest_state.lower())
    return None


def tools_status(vm):
    """
    Checks if VMware Tools is working on the VM
    :param vm: vim.VirtualMachine
    :return: If tools are working or not
    """
    tools = vm.summary.guest.toolsStatus
    return True if tools == "toolsOK" or tools == "toolsOld" else False


def is_template(vm):
    """
    Checks if VM is a template
    :param vm: vim.VirtualMachine
    :return: If the VM is a template
    """
    return bool(vm.summary.config.template)


def convert_to_template(vm):
    """
    Converts a Virtual Machine to a template
    :param vm: vim.VirtualMachine object to convert
    """
    try:
        logging.debug("Converting VM %s to Template", vm.name)
        wait_for_task(vm.MarkAsTemplate())
    except vim.fault.InvalidPowerState:
        logging.error("VM %s must be powered off before being converted to a template!", vm.name)


def convert_to_vm(vm, resource_pool, host=None):
    """
    Converts a Template to a Virtual Machine
    :param vm: vim.VirtualMachine object to convert
    :param resource_pool: vim.ResourcePool to associate with the VM
    :param host: (optional) vim.HostSystem on which the VM should run
    """
    logging.debug("Converting Template %s to VM and assigning to resource pool %s", vm.name, resource_pool.name)
    wait_for_task(vm.MarkAsVirtualMachine(resource_pool, host))


def set_note(vm, note):
    """
    Sets the note on the VM to note
    :param vm: vim.VirtualMachine object
    :param note: String to set the note to
    """
    logging.debug("Setting note of VM %s to %s", vm.name, note)
    spec = vim.vm.ConfigSpec()
    spec.annotation = note
    wait_for_task(vm.ReconfigVM_Task(spec))


@time_execution
def create_snapshot(vm, name, description="default", memory=False):
    """
    Create a snapshot of the VM
    :param vm: vim.VirtualMachine object
    :param name: Title of the snapshot
    :param memory: Memory dump of the VM is included in the snapshot
    :param description: Text description of the snapshot
    """
    logging.info("Creating snapshot of VM %s with a name of %s", vm.name, name)
    wait_for_task(task=vm.CreateSnapshot_Task(name=name, description=description, memory=memory, quiesce=True))


@time_execution
def revert_to_snapshot(vm, snapshot_name):
    """
    Reverts VM to the named snapshot
    :param vm: vim.VirtualMachine object
    :param snapshot_name: Name of the snapshot to revert to
    """
    logging.info("Reverting VM %s to the snapshot %s", vm.name, snapshot_name)
    snap = get_snapshot(vm, snapshot_name)
    wait_for_task(task=snap.RevertToSnapshot_Task())


@time_execution
def revert_to_current_snapshot(vm):
    """
    Reverts the VM to the most recent snapshot
    :param vm: vim.VirtualMachine object
    """
    logging.info("Reverting VM %s to the current snapshot", vm.name)
    wait_for_task(task=vm.RevertToCurrentSnapshot_Task())


def get_snapshot(vm, snapshot_name):
    """
    Retrieves the named snapshot from the VM
    :param vm: vim.VirtualMachine object
    :param snapshot_name: Name of the snapshot to get
    :return: vim.Snapshot object
    """
    for snap in get_all_snapshots(vm):
        if snap.name == snapshot_name:
            return snap.snapshot
    return None


def get_current_snapshot(vm):
    """
    Retrieves the current snapshot from the VM
    :param vm: vim.VirtualMachine object
    :return: Current vim.Snapshot object for the VM, or None if there are no snapshots
    """
    return vm.snapshot.currentSnapshot


def get_all_snapshots(vm):
    """
    Retrieves a list of all snapshots of the VM
    :param vm: vim.VirtualMachine object
    :return: Nested List of vim.Snapshot objects
    """
    return _get_snapshots_recursive(vm.snapshot.rootSnapshotList)


# From: https://github.com/imsweb/ezmomi
def _get_snapshots_recursive(snap_tree):
    """
    Recursively finds all snapshots in the tree
    :param snap_tree:
    :return: Nested List of vim.Snapshot objects
    """
    local_snap = []
    for snap in snap_tree:
        local_snap.append(snap)
    for snap in snap_tree:
        recurse_snap = _get_snapshots_recursive(snap.childSnapshotList)
        if recurse_snap:
            local_snap.extend(recurse_snap)
    return local_snap


def remove_snapshot(vm, snapshot_name, remove_children=True, consolidate_disks=True):
    """
    Removes the named snapshot from the VM
    :param vm: vim.VirtualMachine object
    :param snapshot_name: Name of the snapshot to remove
    :param remove_children: (Optional) Removal of the entire snapshot subtree [default: True]
    :param consolidate_disks: (Optional) Virtual disks of the deleted snapshot will be merged with
    other disks if possible [default: True]
    """
    logging.info("Removing snapshot %s from VM %s", snapshot_name, vm.name)
    snapshot = get_snapshot(vm, snapshot_name)
    wait_for_task(snapshot.RemoveSnapshot_Task(remove_children, consolidate_disks))


def remove_all_snapshots(vm, consolidate_disks=True):
    """
    Removes all snapshots associated with the VM
    :param vm: vim.VirtualMachine object
    :param consolidate_disks: (Optional) Virtual disks of the deleted snapshot will be merged with
    other disks if possible [default: True]
    """
    logging.info("Removing ALL snapshots for the VM %s", vm.name)
    wait_for_task(vm.RemoveAllSnapshots_Task(consolidate_disks))


# From: getallvms.py in pyvmomi-community-samples
def print_vm_info(virtual_machine, print_uuids=False):
    """
    Print human-readable information for a VM
    :param virtual_machine: vim.VirtualMachine object
    :param print_uuids: (Optional) Whether to print UUID information
    """
    summary = virtual_machine.summary
    logging.info("Name          : %s", summary.config.name)
    logging.info("State         : %s", summary.runtime.powerState)
    logging.info("Guest         : %s", summary.config.guestFullName)
    logging.info("CPUs          : %s", summary.config.numCpu)
    logging.info("Memory (MB)   : %s", summary.config.memorySizeMB)
    logging.info("vNICs         : %s", summary.config.numEthernetCards)
    logging.info("Disks         : %s", summary.config.numVirtualDisks)
    logging.info("IsTemplate    : %s", summary.config.template)
    logging.info("Path          : %s", summary.config.vmPathName)
    if summary.guest:
        logging.info("VMware-Tools  : %s", summary.guest.toolsStatus)
        logging.info("IP            : %s", summary.guest.ipAddress)
    if print_uuids:
        logging.info("Instance UUID : %s", summary.config.instanceUuid)
        logging.info("Bios UUID     : %s", summary.config.uuid)
    if summary.runtime.question:
        logging.info("Question  : %s", summary.runtime.question.text)
    if summary.config.annotation:
        logging.info("Annotation    : %s", summary.config.annotation)


def powered_on(vm):
    """
    Determines if a VM is powered on
    :param vm: vim.VirtualMachine object
    :return: If VM is powered on
    """
    return vm.runtime.powerState == vim.VirtualMachine.PowerState.poweredOn


# From: cdrom_vm.py in pyvmomi-community-samples
def find_free_ide_controller(vm):
    """
    Finds a free IDE controller to use
    :param vm: vim.VirtualMachine
    :return: vim.vm.device.VirtualIDEController
    """
    for dev in vm.config.hardware.device:
        if isinstance(dev, vim.vm.device.VirtualIDEController):
            if len(dev.device) < 2:  # If there are less than 2 devices attached, we can use it
                return dev
    return None


def remove_device(vm, device):
    """
    Removes the device from the VM
    :param vm: vim.VirtualMachine
    :param device: vim.vm.device.VirtualDeviceSpec
    """
    logging.debug("Removing device {} from vm {}".format(device.name, vm.name))
    device.operation = vim.vm.device.VirtualDeviceSpec.Operation.remove
    wait_for_task(vm.ReconfigVM_Task(vim.vm.ConfigSpec(deviceChange=[device])))  # Apply the change to the VM


# From: delete_nic_from_vm.py in pyvmomi-community-samples
def delete_nic(vm, nic_number):
    """
    Deletes VM NIC based on it's number
    :param vm: vim.VirtualMachine
    :param nic_number: Unit Number
    """
    nic_label = 'Network adapter ' + str(nic_number)
    logging.debug("Removing Virtual %s from %s", nic_label, vm.name)
    virtual_nic_device = None
    for dev in vm.config.hardware.device:
        if isinstance(dev, vim.vm.device.VirtualEthernetCard) and dev.deviceInfo.label == nic_label:
            virtual_nic_device = dev

    if not virtual_nic_device:
        logging.error('Virtual %s could not be found!', nic_label)
        return

    virtual_nic_spec = vim.vm.device.VirtualDeviceSpec()
    virtual_nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.remove
    virtual_nic_spec.device = virtual_nic_device

    wait_for_task(edit_vm(vm, vim.vm.ConfigSpec(deviceChange=[virtual_nic_spec])))  # Apply the change to the VM


def edit_nic(vm, nic_number, port_group=None, summary=None):
    """
    Edits a VM NIC based on it's number
    :param vm: vim.VirtualMachine
    :param nic_number: Number of network adapter on VM
    :param port_group: (Optional) vim.Network object to assign NIC to
    :param summary: (Optional) Human-readable device info
    """
    nic_label = 'Network adapter ' + str(nic_number)
    logging.debug("Changing %s on %s", nic_label, vm.name)
    virtual_nic_device = None
    for dev in vm.config.hardware.device:
        if isinstance(dev, vim.vm.device.VirtualEthernetCard) and dev.deviceInfo.label == nic_label:
            virtual_nic_device = dev

    if not virtual_nic_device:
        logging.error('Virtual %s could not be found!', nic_label)
        return

    nic_spec = vim.vm.device.VirtualDeviceSpec()
    nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
    nic_spec.device = virtual_nic_device

    if summary:
        logging.debug("Changing summary to %s", summary)

    if port_group:
        logging.debug("Changing PortGroup to %s", port_group.name)
        nic_spec.device.backing.network = port_group
        nic_spec.device.backing.deviceName = port_group.name

    wait_for_task(edit_vm(vm, vim.vm.ConfigSpec(deviceChange=[nic_spec])))  # Apply the change to the VM


# From: add_nic_to_vm.py in pyvmomi-community-samples
def add_nic(vm, port_group, summary="default-summary", model="e1000"):
    """
    Add a NIC in the portgroup to the VM
    :param vm: vim.VirtualMachine
    :param port_group: vim.Network port group to attach NIC to
    :param summary: (Optional) Human-readable device info
    :param model: (Optional) Model of virtual network adapter. [default: e1000]
    Options: e1000, e1000e, vmxnet, vmxnet2, vmxnet3.
    e1000 will work on Windows Server 2003+, and e1000e is supported on Windows Server 2012 and newer.
    VMXNET adapters require VMware Tools to be installed, and will provide significantly enhanced performance,
    since they remove emulation overhead.
    Read this for more details: http://rickardnobel.se/vmxnet3-vs-e1000e-and-e1000-part-1/
    """
    logging.debug("Adding NIC to VM %s\nPort group: %s Summary: %s", vm.name, port_group.name, summary)
    nic_spec = vim.vm.device.VirtualDeviceSpec()  # Create a base object to add configurations to
    nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add

    # Set the type of network adapter
    if model == "e1000":
        nic_spec.device = vim.vm.device.VirtualE1000()
    elif model == "e1000e":
        nic_spec.device = vim.vm.device.VirtualE1000e()
    elif model == "vmxnet":
        nic_spec.device = vim.vm.device.VirtualVmxnet()
    elif model == "vmxnet2":
        nic_spec.device = vim.vm.device.VirtualVmxnet2()
    elif model == "vmxnet3":
        nic_spec.device = vim.vm.device.VirtualVmxnet3()
    else:
        logging.error("Invalid NIC model: %s\nDefaulting to e1000...", model)
        nic_spec.device = vim.vm.device.VirtualE1000()

    nic_spec.device.addressType = 'generated'               # Sets how MAC address is assigned
    nic_spec.device.wakeOnLanEnabled = False                # Disables Wake-on-lan capabilities

    nic_spec.device.deviceInfo = vim.Description()
    nic_spec.device.deviceInfo.summary = summary

    nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
    nic_spec.device.backing.useAutoDetect = False
    nic_spec.device.backing.network = port_group            # Sets port group to assign adapter to
    nic_spec.device.backing.deviceName = port_group.name    # Sets name of device on host system

    nic_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
    nic_spec.device.connectable.startConnected = True       # Ensures adapter is connected at boot
    nic_spec.device.connectable.allowGuestControl = True    # Allows VM guest OS to control device state
    nic_spec.device.connectable.connected = True
    nic_spec.device.connectable.status = 'untried'

    # TODO: configure guest IP address if statically assigned

    wait_for_task(edit_vm(vm, vim.vm.ConfigSpec(deviceChange=[nic_spec])))  # Apply the change to the VM


def attach_iso(vm, filename, datastore, boot=True):
    """
    Attaches an ISO image to a VM
    :param vm: vim.VirtualMachine
    :param filename: Name of the ISO image to attach
    :param datastore: vim.Datastore where the ISO resides
    :param boot: Set VM to boot from the attached ISO
    """
    logging.debug("Adding ISO '%s' to VM '%s'", filename, vm.name)
    drive_spec = vim.vm.device.VirtualDeviceSpec()
    drive_spec.device = vim.vm.device.VirtualCdrom()
    drive_spec.device.controllerKey = find_free_ide_controller(vm).key
    drive_spec.device.key = -1
    drive_spec.device.unitNumber = 0

    drive_spec.device.backing = vim.vm.device.VirtualCdrom.IsoBackingInfo()
    drive_spec.device.backing.fileName = "[{0}] {1}".format(datastore.name, filename)  # Attach ISO
    drive_spec.device.backing.datastore = datastore  # Set datastore ISO is in

    drive_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
    drive_spec.device.connectable.allowGuestControl = True  # Allows VM guest OS to control device state
    drive_spec.device.connectable.startConnected = True  # Ensures ISO is connected at boot

    drive_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
    vm_spec = vim.vm.ConfigSpec(deviceChange=[drive_spec])

    if boot:
        order = [vim.vm.BootOptions.BootableCdromDevice()]
        order.extend(list(vm.config.bootOptions.bootOrder))
        vm_spec.bootOptions = vim.vm.BootOptions(bootOrder=order)

    wait_for_task(edit_vm(vm, vm_spec))  # Apply the change to the VM


def get_nics(vm):
    """
    Returns a list of all Virtual Network Interface Cards (vNICs) on a VM
    :param vm: vim.VirtualMachine
    :return: list of vim.vm.device.VirtualDevice
    """
    return [dev for dev in vm.config.hardware.device if isinstance(dev, vim.vm.device.VirtualEthernetCard)]
