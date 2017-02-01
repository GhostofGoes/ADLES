#!/usr/bin/env python3
# -*- coding: utf-8 -*-


def clone_vm(vm, folder, name, clone_spec):
    """
    Creates a clone of the VM or Template
    :param vm: vim.VirtualMachine object
    :param folder: vim.Folder object in which to create the clone
    :param name: String name of the new VM
    :param clone_spec: vim.vm.CloneSpec for the new VM
    :return:
    """
    print("Cloning VM {0} to folder {1} with name {2}".format(vm.name, folder.name, name))
    vm.CloneVM_Task(folder=folder, name=name, spec=clone_spec)  # CloneSpec docs: pyvmomi/docs/vim/vm/CloneSpec.rst


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


def convert_to_vm(vm):
    """
    Converts a Template to a Virtual Machine
    :param vm: vim.VirtualMachine object to convert
    """
    print("Converting Template {0} to VM".format(vm.name))
    vm.MarkAsVirtualMachine()


def set_note(vm, note):
    """
    Sets the note on the VM to note
    :param vm: vim.VirtualMachine object
    :param note: String to set the note to
    """
    spec = vim.vm.ConfigSpec()
    spec.annotation = note
    vm.ReconfigVM_Task(spec)


# *** SNAPSHOTTING ***
def create_snapshot(vm, name, memory=False, description="default"):
    """
    Create a snapshot of the VM
    :param vm: vim.VirtualMachine object
    :param name: Title of the snapshot
    :param memory: Memory dump of the VM is included in the snapshot
    :param description: Text description of the snapshot
    """
    print("Creating snapshot of VM {0} with a name of {1}".format(vm.name, name))
    vm.CreateSnapshot_Task(name=name, description=description, memory=memory, quiesce=True)

# TODO: remove snapshot


def revert_to_current_snapshot(vm, suppress_power_on=False):
    """
    Reverts the VM to the most recent snapshot
    :param vm: vim.VirtualMachine object
    :param suppress_power_on: Prevents the VM from powering on regardless of the snapshot's power state
    """
    print("Reverting VM {0} to the current snapshot".format(vm.name))
    vm.RevertToCurrentSnapshot_Task(suppress_power_on=suppress_power_on)


def remove_all_snapshots(vm, consolidate_disks=True):
    """
    Removes all snapshots associated with the VM
    :param vm: vim.VirtualMachine object
    :param consolidate_disks: If true, virtual disks of the deleted snapshot will be merged with other disks if possible
    """
    print("Removing ALL snapshots for the VM {0}".format(vm.name))
    vm.RemoveAllSnapshots_Task(consolidate_disks)
