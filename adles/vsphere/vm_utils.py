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

from pyVmomi import vim, vmodl

import adles.utils as utils


@utils.time_execution
def clone_vm(vm, folder, name, clone_spec):
    """
    Creates a clone of the VM or Template
    :param vm: vim.VirtualMachine object
    :param folder: vim.Folder object in which to create the clone
    :param name: String name of the new VM
    :param clone_spec: vim.vm.CloneSpec for the new VM
    """
    if is_template(vm) and not bool(clone_spec.location.pool):
        logging.error("Cannot clone Template '%s' without specifying a resource pool", vm.name)
    else:
        logging.debug("Cloning VM '%s' to folder '%s' as '%s'", vm.name, folder.name, name)
        try:
            vm.CloneVM_Task(folder=folder, name=name, spec=clone_spec).wait()
        except vim.fault.InvalidState:
            logging.error("Could not make clone '%s': invalid state for VM '%s'", name, vm.name)
        except vim.fault.CustomizationFault:
            logging.error("Could not make clone '%s': invalid customization", name)
        except vim.fault.VmConfigFault:
            logging.error("Could not make clone '%s': invalid configuration", name)
vim.VirtualMachine.clone = clone_vm


def destroy_vm(vm):
    """
    Destroys a Virtual Machine
    :param vm: vim.VirtualMachine object
    """
    logging.debug("Destroying VM '%s'", vm.name)
    if powered_on(vm):
        logging.warning("VM '%s' is still on, powering off before destroying...", vm.name)
        change_vm_state(vm, "off", attempt_guest=False)
    vm.Destroy_Task().wait()
vim.VirtualMachine.destroy = destroy_vm


@utils.check(vim.VirtualMachine, "vm")
def edit_vm(vm, config):
    """
    Edits a VM using the given configuration specification
    :param vm: vim.VirtualMachine object
    :param config: vim.vm.ConfigSpec object
    """
    logging.debug("Reconfiguring VM '%s'", vm.name)
    try:
        vm.ReconfigVM_Task(config).wait()
    except vim.fault.TaskInProgress as e:
        logging.error("Cannot edit VM '%s': it is busy with task '%s'", vm.name, e.task)
    except vim.fault.VmConfigFault:
        logging.error("Cannot edit VM '%s': invalid configuration", vm.name)
    except vim.fault.InvalidState:
        logging.error("Cannot edit VM '%s': it is in an invalid state", vm.name)
    except vim.fault.InvalidName as e:
        logging.error("Cannot edit VM '%s': name '%s' is not valid", vm.name, e.name)
    except vim.fault.DuplicateName as e:
        logging.error("Cannot edit VM '%s': there is a duplicate with name '%s'", vm.name, e.name)
    except vim.fault.InvalidPowerState as e:
        logging.error("Cannot edit VM '%s': invalid power state '%s'", vm.name, e.existingState)
    except vim.fault.InvalidDatastore as e:
        logging.error("Cannot edit VM '%s': invalid Datastore '%s'", vm.name, e.datastore)


def change_vm_state(vm, state, attempt_guest=True):
    """
    :param vm: vim.VirtualMachine object to change state of
    :param state: State to change to (on | off | reset | suspend)
    :param attempt_guest: Whether to attempt to use guest operations to change power state
    """
    if is_template(vm):
        logging.error("VM '%s' is a Template, so state cannot be changed to '%s'", vm.name, state)
        return
    try:
        if attempt_guest and has_tools(vm) and state != "on":  # Can't power on using guest ops
            change_guest_state(vm, state)
        else:
            change_power_state(vm, state)
    except vim.fault.InvalidPowerState as e:
        logging.error("Cannot change '%s' in power state '%s' to '%s'",
                      vm.name, e.existingState, state)
    except vmodl.fault.NotSupported:
        logging.error("Cannot change power state of '%s': it is a template", vm.name)
    except vim.fault.TaskInProgress as e:
        logging.error("Cannot change power state of '%s': Task '%s' in progress",
                      vm.name, e.task)
    except vim.fault.InvalidState:
        logging.error("Cannot change power state of '%s': it is in an invalid state ", vm.name)
vim.VirtualMachine.change_state = change_vm_state


def change_power_state(vm, power_state):
    """
    Changes a VM power state to the state specified
    :param vm: vim.VirtualMachine object to change power state of
    :param power_state: on, off, reset, or suspend
    """
    state = power_state.lower()
    if state == "on":
        task = vm.PowerOnVM_Task()
    elif state == "off":
        task = vm.PowerOffVM_Task()
    elif state == "reset":
        task = vm.ResetVM_Task()
    elif state == "suspend":
        task = vm.SuspendVM_Task()
    else:
        logging.error("Invalid power_state %s for VM %s", power_state, vm.name)
        return
    logging.debug("Changing power state of VM %s to: '%s'", vm.name, power_state)
    task.wait()


def change_guest_state(vm, guest_state):
    """
    Changes a VMs guest power state. VMware Tools must be installed on the VM for this to work.
    :param vm:  vim.VirtualMachine object to change guest state of
    :param guest_state: shutdown, reboot, or standby [Alternatives: off, reset, suspend]
    """
    state = guest_state.lower()
    if vm.summary.guest.toolsStatus == "toolsNotInstalled":
        logging.error("Cannot change a VM's guest power state without VMware Tools!")
        return
    elif state == "shutdown" or state == "off":
        task = vm.ShutdownGuest()
    elif state == "reboot" or state == "reset":
        task = vm.RebootGuest()
    elif state == "standby" or state == "suspend":
        task = vm.StandbyGuest()
    else:
        logging.error("Invalid guest_state argument: %s", state)
        return
    logging.debug("Changing guest power state of VM %s to: '%s'", vm.name, guest_state)
    try:
        task.wait()
    except vim.fault.ToolsUnavailable:
        logging.error("Cannot change guest state of '%s': Tools are not running", vm.name)


def snapshot_disk_usage(vm):
    """
    Determines the total disk usage of a VM's snapshots
    :param vm: vim.VirtualMachine
    :return: Human-readable disk usage of the snapshots
    """
    from re import search
    disk_list = vm.layoutEx.file
    size = 0
    for disk in disk_list:
        if disk.type == 'snapshotData':
            size += disk.size
        ss_disk = search('0000\d\d', disk.name)
        if ss_disk:
            size += disk.size
    return utils.sizeof_fmt(size)


# From: getallvms in pyvmomi-community-samples
def get_vm_info(vm, detailed=False, uuids=False, snapshot=False, vnics=False):
    """
    Get human-readable information for a VM
    :param vm: vim.VirtualMachine object
    :param detailed: Add more detailed information, such as maximum memory used [default: False]
    :param uuids: Whether to get UUID information [default: False]
    :param snapshot: Shows the current snapshot, if any [default: False]
    :param vnics: Add information about the virtual network interfaces on the VM
    :return: String with the VM information
    """
    info_string = "\n"
    summary = vm.summary
    info_string += "Name          : %s\n" % summary.config.name
    info_string += "Status        : %s\n" % str(summary.overallStatus)
    info_string += "Power State   : %s\n" % summary.runtime.powerState
    if vm.guest:
        info_string += "Guest State   : %s\n" % vm.guest.guestState
    info_string += "Last modified : %s\n" % str(vm.config.modified)  # datetime object
    if detailed:
        info_string += "Num consoles  : %d\n" % summary.runtime.numMksConnections
    info_string += "Host          : %s\n" % summary.runtime.host.name
    info_string += "Guest OS      : %s\n" % summary.config.guestFullName
    info_string += "Num CPUs      : %s\n" % summary.config.numCpu
    info_string += "Memory (MB)   : %s\n" % summary.config.memorySizeMB
    if detailed:
        info_string += "Num vNICs     : %s\n" % summary.config.numEthernetCards
        info_string += "Num Disks     : %s\n" % summary.config.numVirtualDisks
    info_string += "IsTemplate    : %s\n" % summary.config.template  # bool
    if detailed:
        info_string += "Path          : %s\n" % summary.config.vmPathName
    info_string += "Folder:       : %s\n" % vm.parent.name
    if vm.guest:
        info_string += "IP            : %s\n" % vm.guest.ipAddress
        info_string += "Hostname:     : %s\n" % vm.guest.hostName
        info_string += "Tools status  : %s\n" % vm.guest.toolsRunningStatus
        info_string += "Tools version : %s\n" % vm.guest.toolsVersionStatus2
    if vnics:
        vm_nics = get_nics(vm)
        for num, vnic in zip(range(1, len(vm_nics) + 1), vm_nics):
            info_string += "vNIC %d label   : %s\n" % (num, vnic.deviceInfo.label)
            info_string += "vNIC %d summary : %s\n" % (num, vnic.deviceInfo.summary)
            info_string += "vNIC %d network : %s\n" % (num, vnic.backing.network.name)
    if uuids:
        info_string += "Instance UUID : %s\n" % summary.config.instanceUuid
        info_string += "Bios UUID     : %s\n" % summary.config.uuid
    if summary.runtime.question:
        info_string += "Question      : %s\n" % summary.runtime.question.text
    if summary.config.annotation:
        info_string += "Annotation    : %s\n" % summary.config.annotation
    if snapshot and vm.snapshot and hasattr(vm.snapshot, 'currentSnapshot'):
        info_string += "Current Snapshot: %s\n" % vm.snapshot.currentSnapshot.config.name
        info_string += "Disk usage of all snapshots: %s\n" % snapshot_disk_usage(vm=vm)
    if detailed and summary.runtime:
        info_string += "Last Poweron  : %s\n" % str(summary.runtime.bootTime)  # datetime object
        info_string += "Max CPU usage : %s\n" % summary.runtime.maxCpuUsage
        info_string += "Max Mem usage : %s\n" % summary.runtime.maxMemoryUsage
        info_string += "Last suspended: %s\n" % summary.runtime.suspendTime
    return info_string
vim.VirtualMachine.get_info = get_vm_info


def get_nics(vm):
    """
    Returns a list of all Virtual Network Interface Cards (vNICs) on a VM
    :param vm: vim.VirtualMachine
    :return: list of vim.vm.device.VirtualEthernetCard
    """
    from adles.vsphere.vsphere_utils import is_vnic
    return [dev for dev in vm.config.hardware.device if is_vnic(dev)]
vim.VirtualMachine.get_nics = get_nics


def has_tools(vm):
    """
    Checks if VMware Tools is installed and working
    :param vm: vim.VirtualMachine
    :return: If tools are installed and working
    """
    tools = vm.summary.guest.toolsStatus
    return True if tools == "toolsOK" or tools == "toolsOld" else False
vim.VirtualMachine.has_tools = has_tools


def powered_on(vm):
    """
    Determines if a VM is powered on
    :param vm: vim.VirtualMachine object
    :return: If VM is powered on
    """
    return vm.runtime.powerState == vim.VirtualMachine.PowerState.poweredOn
vim.VirtualMachine.powered_on = powered_on


def is_template(vm):
    """
    Checks if VM is a template
    :param vm: vim.VirtualMachine
    :return: If the VM is a template
    """
    return bool(vm.summary.config.template)
vim.VirtualMachine.is_template = is_template
