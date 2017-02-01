#!/usr/bin/env python3
# -*- coding: utf-8 -*-


def change_power_state(vm, power_state, datacenter=None):
    """
    Changes a VM power state to the state specified.
    :param vm: vim.VirtualMachine object to change power state of
    :param power_state: on, off, reset, or suspend
    :param datacenter: vim.Datacenter object, required for power on operation
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
    Converts a VM to a template
    :param vm: vim.VirtualMachine object to be converted
    """
    try:
        vm.MarkAsTemplate()
    except vim.fault.InvalidPowerState:
        print("(ERROR) VM {0} must be powered off before being converted to a template!".format(vm.name))


def set_note(vm, note):
    """
    Sets the note on the VM to note
    :param vm: vim.VirtualMachine object
    :param note: String to set the note to
    """
    spec = vim.vm.ConfigSpec()
    spec.annotation = note
    vm.ReconfigVM_Task(spec)
