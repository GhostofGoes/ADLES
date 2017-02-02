#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pyVmomi import vim


def clone_vm(vm, folder, name, clone_spec):
    """
    Creates a clone of the VM or Template
    :param vm: vim.VirtualMachine object
    :param folder: vim.Folder object in which to create the clone
    :param name: String name of the new VM
    :param clone_spec: vim.vm.CloneSpec for the new VM
    """
    print("Cloning VM {0} to folder {1} with name {2}".format(vm.name, folder.name, name))
    vm.CloneVM_Task(folder=folder, name=name, spec=clone_spec)  # CloneSpec docs: pyvmomi/docs/vim/vm/CloneSpec.rst


def destroy_vm(vm):
    """
    Unregisters and deletes the VM
    :param vm: vim.VirtualMachine object
    """
    print("DESTROYING VM {0}".format(vm.name))
    if powered_on(vm):
        print("VM is still on, powering off before destroying...")
        change_power_state(vm, "off")
    vm.Destroy_Task()


def change_power_state(vm, power_state):
    """
    Changes a VM power state to the state specified.
    :param vm: vim.VirtualMachine object to change power state of
    :param power_state: on, off, reset, or suspend
    """
    print("Changing power state of VM {0} to: '{1}'".format(vm.name, power_state))
    if power_state.lower() == "on":
        vm.PowerOnVM_Task()
    elif power_state.lower() == "off":
        vm.PowerOffVM_Task()
    elif power_state.lower() == "reset":
        vm.ResetVM_Task()
    elif power_state.lower() == "suspend":
        vm.SuspendVM_Task()


def change_guest_state(vm, guest_state):
    """
    Changes a VMs guest power state. VMware Tools must be installed on the VM for this to work.
    :param vm:  vim.VirtualMachine object to change guest state of
    :param guest_state: shutdown, reboot, or standby
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


def convert_to_template(vm):
    """
    Converts a Virtual Machine to a template
    :param vm: vim.VirtualMachine object to convert
    """
    try:
        print("Converting VM {0} to Template".format(vm.name))
        vm.MarkAsTemplate()
    except vim.fault.InvalidPowerState:
        print("(ERROR) VM {0} must be powered off before being converted to a template!".format(vm.name))


def convert_to_vm(vm, resource_pool, host=None):
    """
    Converts a Template to a Virtual Machine
    :param vm: vim.VirtualMachine object to convert
    :param resource_pool: vim.ResourcePool to associate with the VM
    :param host: (optional) vim.HostSystem on which the VM should run
    """
    print("Converting Template {0} to VM and assigning to resource pool {1}".format(vm.name, resource_pool.name))
    vm.MarkAsVirtualMachine(resource_pool, host)


def set_note(vm, note):
    """
    Sets the note on the VM to note
    :param vm: vim.VirtualMachine object
    :param note: String to set the note to
    """
    print("Setting note of VM {0} to {1}".format(vm.name, note))
    spec = vim.vm.ConfigSpec()
    spec.annotation = note
    vm.ReconfigVM_Task(spec)


def create_snapshot(vm, name, description="default", memory=False):
    """
    Create a snapshot of the VM
    :param vm: vim.VirtualMachine object
    :param name: Title of the snapshot
    :param memory: Memory dump of the VM is included in the snapshot
    :param description: Text description of the snapshot
    """
    print("Creating snapshot of VM {0} with a name of {1}".format(vm.name, name))
    vm.CreateSnapshot_Task(name=name, description=description, memory=memory, quiesce=True)


def revert_to_snapshot(vm, snapshot_name):
    """
    Reverts VM to the named snapshot
    :param vm: vim.VirtualMachine object
    :param snapshot_name: Name of the snapshot to revert to
    """
    print("Reverting VM {0} to the snapshot {1}".format(vm.name, snapshot_name))
    snap = get_snapshot(vm, snapshot_name)
    snap.RevertToSnapshot_Task()


def revert_to_current_snapshot(vm):
    """
    Reverts the VM to the most recent snapshot
    :param vm: vim.VirtualMachine object
    """
    print("Reverting VM {0} to the current snapshot".format(vm.name))
    vm.RevertToCurrentSnapshot_Task()


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
    Retireves the current snapshot from the VM
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
    print("Removing snapshot {0} from VM {1}".format(snapshot_name, vm.name))
    snapshot = get_snapshot(vm, snapshot_name)
    snapshot.RemoveSnapshot_Task(remove_children, consolidate_disks)


def remove_all_snapshots(vm, consolidate_disks=True):
    """
    Removes all snapshots associated with the VM
    :param vm: vim.VirtualMachine object
    :param consolidate_disks: (Optional) Virtual disks of the deleted snapshot will be merged with
    other disks if possible [default: True]
    """
    print("Removing ALL snapshots for the VM {0}".format(vm.name))
    vm.RemoveAllSnapshots_Task(consolidate_disks)


# From: getallvms.py in pyvmomi-community-samples
def print_vm_info(virtual_machine):
    """
    Print human-readable information for a virtual machine object
    :param virtual_machine:
    """
    summary = virtual_machine.summary
    print("Name          : ", summary.config.name)
    print("Template      : ", summary.config.template)
    print("Path          : ", summary.config.vmPathName)
    print("Guest         : ", summary.config.guestFullName)
    print("Instance UUID : ", summary.config.instanceUuid)
    print("Bios UUID     : ", summary.config.uuid)
    print("State         : ", summary.runtime.powerState)
    if summary.guest:
        print("VMware-tools  : ", summary.guest.toolsStatus)
        print("IP            : ", summary.guest.ipAddress)
    if summary.runtime.question:
        print("Question  : ", summary.runtime.question.text)
    if summary.config.annotation:
        print("Annotation    : ", summary.config.annotation)


def powered_on(vm):
    """
    Determines if a VM is powered on
    :param vm: vim.VirtualMachine object
    :return: Boolean. Do I really need to write a description for this?
    """
    return vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn
