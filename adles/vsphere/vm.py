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
import os

from pyVmomi import vim

import adles.utils as utils
from adles.vsphere.vsphere_utils import wait_for_task, is_vnic
from adles.vsphere.folder_utils import find_in_folder


class VM:
    """ Represents a VMware vSphere Virtual Machine instance. """
    __version__ = "0.3.0"

    def __init__(self, vm=None, name=None, folder=None, resource_pool=None,
                 datastore=None, host=None):
        """
        NOTE: VM.create() must be called post-init
        :param name: Name of the VM
        :param folder: Name of the folder VM is located
        :param resource_pool: Resource pool to use for the VM
        :param datastore: Datastore the VM is stored on
        :param host: Host the VM runs on
        :param vm: vim.VirtualMachine object to use instead of calling create()
        """
        self._log = logging.getLogger('VM')
        if vm is not None:
            self._vm = vm
            self.vm_folder = os.path.split(self._vm.summary.config.vmPathName)[0]
            self.name = vm.name
            self.folder = vm.parent
            self.resource_pool = vm.resourcePool
            self.datastore = vm.datastore[0]
            self.host = vm.summary.runtime.host
            self.network = vm.network
        else:
            self._vm = None
            self.vm_folder = None  # Note: this is the path to the VM's files on the Datastore
            self.name = name
            self.folder = folder  # vim.Folder, but may be Folder class eventually
            self.resource_pool = resource_pool  # vim.Pool or something object
            self.datastore = datastore  # vim.Datastore object
            self.host = host  # vim.HostSystem, but may be Host class soon

    def create(self, template=None, cpus=1, cores=1, memory=512, max_consoles=None,
               version=None, firmware='efi', datastore_path=None):
        """
        Creates a Virtual Machine
        :param template: Template VM to clone
        :param cpus: Number of processors [default: 1]
        :param cores: Number of processor cores [default: 1]
        :param memory: Amount of RAM in MB [default: 512]
        :param max_consoles: Maximum number of active console connections [default: default]
        :param version: Hardware version of the VM [default: highest host supports]
        :param firmware: Firmware to emulate for the VM (efi | bios) [default: efi]
        :param datastore_path: Path to existing VM files on datastore [default: None]
        """
        if template is not None:  # Use a template to create the VM
            self._log.debug("Creating VM '%s' by cloning %s", self.name, template.name)
            clonespec = vim.vm.CloneSpec()
            clonespec.location = vim.vm.RelocateSpec(pool=self.resource_pool,
                                                     datastore=self.datastore)
            wait_for_task(template.CloneVM_Task(folder=self.folder, name=self.name, spec=clonespec))
        else:  # Generate the specification for and create the new VM
            self._log.debug("Creating VM '%s' from scratch", self.name)
            spec = vim.vm.ConfigSpec()
            spec.name = self.name
            spec.numCPUs = int(cpus)
            spec.numCoresPerSocket = int(cores)
            spec.memoryMB = int(memory)
            spec.memoryHotAddEnabled = True
            spec.firmware = str(firmware).lower()
            if version is not None:
                spec.version = str(version)
            if max_consoles is not None:
                spec.maxMksConnections = int(max_consoles)
            vm_path = '[' + self.datastore.name + '] '
            if datastore_path:
                vm_path += str(datastore_path)
            vm_path += self.name + '/' + self.name + '.vmx'
            spec.files = vim.vm.FileInfo(vmPathName=vm_path)
            self._log.debug("Creating VM '%s' in folder '%s'", self.name, self.folder.name)
            wait_for_task(self.folder.CreateVM_Task(spec, self.resource_pool, self.host))

        self._vm = find_in_folder(self.folder, self.name, vimtype=vim.VirtualMachine)
        if not self._vm:
            self._log.error("Failed to create VM %s", self.name)
            return False
        else:
            self._log.debug("Created VM %s", self.name)
            # TODO: if cloned, reconfigure to match anything given as parameters, e.g memory
        self.vm_folder = os.path.split(self._vm.summary.config.vmPathName)[0]
        self.network = self._vm.network
        return True

    def destroy(self):
        """ Destroy the VM """
        self._log.debug("Destroying VM %s", self.name)
        if self.powered_on():
            self.change_state("off")
        wait_for_task(self._vm.Destroy_Task())

    def change_state(self, state, attempt_guest=True):
        """
        Generic power state change function that uses guest operations if available
        :param state: State to change to (on | off | reset | suspend)
        :param attempt_guest: Whether to attempt to use guest operations to change power state
        :return: 
        """
        state = state.lower()
        if self.is_template():
            self._log.error("VM '%s' is a Template, so state cannot be changed to '%s'",
                            self.name, state)
        elif attempt_guest and self.has_tools() and state != "on":  # Can't power on using guest ops
            if self._vm.summary.guest.toolsStatus == "toolsNotInstalled":
                self._log.error("Cannot change a VM's guest power state without VMware Tools!")
                return
            elif state == "shutdown" or state == "off":
                task = self._vm.ShutdownGuest()
            elif state == "reboot" or state == "reset":
                task = self._vm.RebootGuest()
            elif state == "standby" or state == "suspend":
                task = self._vm.StandbyGuest()
            else:
                self._log.error("Invalid guest_state argument: %s", state)
                return
            self._log.debug("Changing guest power state of VM %s to: '%s'", self.name, state)
            try:
                wait_for_task(task)
            except vim.fault.ToolsUnavailable:
                self._log.error("Cannot change guest state of '%s': Tools are not running", self.name)
        else:
            if state == "on":
                task = self._vm.PowerOnVM_Task()
            elif state == "off":
                task = self._vm.PowerOffVM_Task()
            elif state == "reset":
                task = self._vm.ResetVM_Task()
            elif state == "suspend":
                task = self._vm.SuspendVM_Task()
            else:
                self._log.error("Invalid state arg %s for VM %s", state, self.name)
                return
            self._log.debug("Changing power state of VM %s to: '%s'", self.name, state)
            wait_for_task(task)

    def edit_resources(self, cpus=None, cores=None, memory=None, max_consoles=None):
        """
        Edit resource limits for the VM
        :param cpus: Number of CPUs
        :param cores: Number of CPU cores
        :param memory: Amount of RAM in MB
        :param max_consoles: Maximum number of simultaneous MKS console connections
        """
        spec = vim.vm.ConfigSpec()
        if cpus is not None:
            spec.numCPUs = int(cpus)
        if cores is not None:
            spec.numCoresPerSocket = int(cores)
        if memory is not None:
            spec.memoryMB = int(memory)
        if max_consoles is not None:
            spec.maxMksConnections = int(max_consoles)
        self._edit(spec)

    def rename(self, name):
        """
        Rename the VM
        :param name: New name for the VM
        """
        spec = vim.vm.ConfigSpec(name=str(name))
        self._edit(spec)
        self.name = str(name)

    def upgrade_vm(self, version):
        """
        Upgrades the hardware version of the VM
        :param version: Version of hardware to upgrade VM to [default: latest VM's host supports]
        """
        full_version = "vmx-" + str(version)
        try:
            wait_for_task(self._vm.UpgradeVM_Task(full_version))
        except vim.fault.AlreadyUpgraded:
            self._log.warning("Hardware version is already up-to-date for %s", self.name)

    def convert_template(self):
        """ Converts a Virtual Machine to a Template """
        if self.is_template():
            self._log.warning("%s is already a Template", self.name)
        else:
            self._log.debug("Converting '%s' to Template", self.name)
            self._vm.MarkAsTemplate()

    def convert_vm(self):
        """ Converts a Template to a Virtual Machine """
        self._log.debug("Converting '%s' to VM", self.name)
        self._vm.MarkAsVirtualMachine(self.resource_pool, self.host)

    def set_note(self, note):
        """
        Sets the note on the VM
        :param note: String to set the note to
        """
        self._edit(vim.vm.ConfigSpec(annotation=str(note)))

    def get_vm_info(self, detailed=False, uuids=False, snapshot=False, vnics=False):
        """
        Get human-readable information for a VM
        :param detailed: Add more detailed information, such as maximum memory used [default: False]
        :param uuids: Whether to get UUID information [default: False]
        :param snapshot: Shows the current snapshot, if any [default: False]
        :param vnics: Add information about the virtual network interfaces on the VM
        :return: String with the VM information
        """
        info_string = "\n"
        # http://pubs.vmware.com/vsphere-60/topic/com.vmware.wssdk.apiref.doc/vim.vm.Summary.html
        summary = self._vm.summary
        # http://pubs.vmware.com/vsphere-60/topic/com.vmware.wssdk.apiref.doc/vim.vm.ConfigInfo.html
        config = self._vm.config
        info_string += "Name          : %s\n" % self.name
        info_string += "Status        : %s\n" % str(summary.overallStatus)
        info_string += "Power State   : %s\n" % summary.runtime.powerState
        if self._vm.guest:
            info_string += "Guest State   : %s\n" % self._vm.guest.guestState
        info_string += "Last modified : %s\n" % str(self._vm.config.modified)  # datetime object
        if hasattr(summary.runtime, 'cleanPowerOff'):
            info_string += "Clean poweroff: %s\n" % summary.runtime.cleanPowerOff
        if detailed:
            info_string += "Num consoles  : %d\n" % summary.runtime.numMksConnections
        info_string += "Host          : %s\n" % self.host.name
        info_string += "Datastore     : %s\n" % self.datastore
        info_string += "HW Version    : %s\n" % config.version
        info_string += "Guest OS      : %s\n" % summary.config.guestFullName
        info_string += "Num CPUs      : %s\n" % summary.config.numCpu
        info_string += "Memory (MB)   : %s\n" % summary.config.memorySizeMB
        if detailed:
            info_string += "Num vNICs     : %s\n" % summary.config.numEthernetCards
            info_string += "Num Disks     : %s\n" % summary.config.numVirtualDisks
        info_string += "IsTemplate    : %s\n" % summary.config.template  # bool
        if detailed:
            info_string += "Config Path   : %s\n" % summary.config.vmPathName
        info_string += "Folder:       : %s\n" % self._vm.parent.name
        if self._vm.guest:
            info_string += "IP            : %s\n" % self._vm.guest.ipAddress
            info_string += "Hostname:     : %s\n" % self._vm.guest.hostName
            info_string += "Tools status  : %s\n" % self._vm.guest.toolsRunningStatus
            info_string += "Tools version : %s\n" % self._vm.guest.toolsVersionStatus2
        if vnics:
            vm_nics = self.get_nics()
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
        if snapshot and self._vm.snapshot and hasattr(self._vm.snapshot, 'currentSnapshot'):
            info_string += "Current Snapshot: %s\n" % self._vm.snapshot.currentSnapshot.config.name
            info_string += "Disk usage of all snapshots: %s\n" % self.snapshot_disk_usage()
        if detailed and summary.runtime:
            info_string += "Last Poweron  : %s\n" % str(summary.runtime.bootTime)  # datetime object
            info_string += "Max CPU usage : %s\n" % summary.runtime.maxCpuUsage
            info_string += "Max Mem usage : %s\n" % summary.runtime.maxMemoryUsage
            info_string += "Last suspended: %s\n" % summary.runtime.suspendTime
        return info_string

    def get_vim_vm(self):
        """
        Get the vim.VirtualMachine instance of the VM
        :return: vim.VirtualMachine
        """
        return self._vm

    def screenshot(self):
        """
        Takes a screenshot of a VM
        :return: Path to datastore location of the screenshot
        """
        return wait_for_task(self._vm.CreateScreenshot_Task())

    def snapshot_disk_usage(self):
        """
        Determines the total disk usage of a VM's snapshots
        :return: Human-readable disk usage of the snapshots
        """
        from re import search
        disk_list = self._vm.layoutEx.file
        size = 0
        for disk in disk_list:
            if disk.type == 'snapshotData':
                size += disk.size
            ss_disk = search('0000\d\d', disk.name)
            if ss_disk:
                size += disk.size
        return utils.sizeof_fmt(size)

    def get_snapshot(self, snapshot=None):
        """
        Retrieves the named snapshot from the VM
        :param snapshot: Name of the snapshot to get [default: current snapshot]
        :return: vim.Snapshot object
        """
        if snapshot is None:
            return self._vm.snapshot.currentSnapshot
        else:
            for snap in self.get_all_snapshots():
                if snap.name == snapshot:
                    return snap.snapshot
            return None

    def get_all_snapshots(self):
        """
        Retrieves a list of all snapshots of the VM
        :return: Nested List of vim.Snapshot objects
        """
        return self._get_snapshots_recursive(self._vm.snapshot.rootSnapshotList)

    # From: https://github.com/imsweb/ezmomi
    def _get_snapshots_recursive(self, snap_tree):
        """
        Recursively finds all snapshots in the tree
        :param snap_tree: Tree of snapshots
        :return: Nested List of vim.Snapshot objects
        """
        local_snap = []
        for snap in snap_tree:
            local_snap.append(snap)
        for snap in snap_tree:
            recurse_snap = self._get_snapshots_recursive(snap.childSnapshotList)
            if recurse_snap:
                local_snap.extend(recurse_snap)
        return local_snap

    def create_snapshot(self, name, description='', memory=False):
        """
        Create a snapshot of the VM
        :param name: Title of the snapshot
        :param memory: Memory dump of the VM is included in the snapshot
        :param description: Text description of the snapshot
        """
        self._log.info("Creating snapshot '%s' of VM '%s'", name, self.name)
        wait_for_task(self._vm.CreateSnapshot_Task(name=name, description=description,
                                                   memory=bool(memory), quiesce=True))

    def revert_to_snapshot(self, snapshot):
        """
        Reverts VM to the named snapshot
        :param snapshot: Name of the snapshot to revert to
        """
        self._log.info("Reverting '%s' to the snapshot '%s'", self.name, snapshot)
        wait_for_task(self.get_snapshot(snapshot).RevertToSnapshot_Task())

    def revert_to_current_snapshot(self):
        """ Reverts the VM to the most recent snapshot. """
        self._log.info("Reverting '%s' to the current snapshot", self.name)
        wait_for_task(self._vm.RevertToCurrentSnapshot_Task())

    def remove_snapshot(self, snapshot_name, remove_children=True, consolidate_disks=True):
        """
        Removes the named snapshot from the VM
        :param snapshot_name: Name of the snapshot to remove
        :param remove_children: Removal of the entire snapshot subtree [default: True]
        :param consolidate_disks: Virtual disks of deleted snapshot will be merged with
        other disks if possible [default: True]
        """
        self._log.info("Removing snapshot '%s' from '%s'", snapshot_name, self.name)
        snapshot = self.get_snapshot(snapshot_name)
        wait_for_task(snapshot.RemoveSnapshot_Task(remove_children, consolidate_disks))

    def remove_all_snapshots(self, consolidate_disks=True):
        """
        Removes all snapshots associated with the VM
        :param consolidate_disks: Virtual disks of the deleted snapshot will be merged with
        other disks if possible [default: True]
        """
        self._log.info("Removing ALL snapshots for the '%s'", self.name)
        wait_for_task(self._vm.RemoveAllSnapshots_Task(consolidate_disks))

    def remove_device(self, device):
        """
        Removes the device from the VM
        :param device: vim.vm.device.VirtualDeviceSpec
        """
        self._log.debug("Removing device '%s' from '%s'", device.name, self.name)
        device.operation = vim.vm.device.VirtualDeviceSpec.Operation.remove
        self._edit(vim.vm.ConfigSpec(deviceChange=[device]))

    def get_nics(self):
        """
        Returns a list of all Virtual Network Interface Cards (vNICs) on a VM
        :return: list of vim.vm.device.VirtualEthernetCard
        """
        return [dev for dev in self._vm.config.hardware.device if is_vnic(dev)]

    def get_nic_by_name(self, name):
        """
        Gets a Virtual Network Interface Card from a VM
        :param name: Name of the vNIC
        :return: vim.vm.device.VirtualEthernetCard
        """
        for dev in self._vm.config.hardware.device:
            if is_vnic(dev) and dev.deviceInfo.label.lower() == name.lower():
                return dev
        self._log.debug("Could not find vNIC '%s' on '%s'", name, self.name)
        return None

    def get_nic_by_id(self, nic_id):
        """
        Get a vNIC by integer ID
        :param nic_id: ID of the vNIC
        :return: vim.vm.device.VirtualEthernetCard
        """
        return self.get_nic_by_name("Network Adapter " + str(nic_id))

    def get_nic_by_network(self, network):
        """
        Finds a vNIC by it's network backing
        :param network: vim.Network
        :return: Name of the vNIC
        """
        for dev in self._vm.config.hardware.device:
            if is_vnic(dev) and dev.backing.network == network:
                return dev
        self._log.debug("Could not find vNIC with network '%s' on '%s'", network.name, self.name)
        return None

    def add_nic(self, network, summary="default-summary", model="e1000"):
        """
        Add a NIC in the portgroup to the VM
        :param network: vim.Network to attach NIC to
        :param summary: Human-readable device info [default: default-summary]
        :param model: Model of virtual network adapter. [default: e1000]
        Options: (e1000 | e1000e | vmxnet | vmxnet2 | vmxnet3 | pcnet32 | sriov)
        e1000 will work on Windows Server 2003+, and e1000e is supported on Windows Server 2012+.
        VMXNET adapters require VMware Tools to be installed, and provide enhanced performance.
        Read this for more details: http://rickardnobel.se/vmxnet3-vs-e1000e-and-e1000-part-1/
        """
        if not isinstance(network, vim.Network):
            self._log.error("Invalid network type when adding vNIC to VM '%s': %s",
                            self.name, type(network).__name__)
        self._log.debug("Adding NIC to VM '%s'\nNetwork: '%s'\tSummary: '%s'\tNIC Model: '%s'",
                        self.name, network.name, summary, model)
        nic_spec = vim.vm.device.VirtualDeviceSpec()  # Create base object to add configurations to
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
        elif model == "pcnet32":
            nic_spec.device = vim.vm.device.VirtualPCNet32()
        elif model == "sriov":
            nic_spec.device = vim.vm.device.VirtualSriovEthernetCard()
        else:
            self._log.error("Invalid NIC model: '%s'\nDefaulting to e1000...", model)
            nic_spec.device = vim.vm.device.VirtualE1000()
        nic_spec.device.addressType = 'generated'  # Sets how MAC address is assigned
        nic_spec.device.wakeOnLanEnabled = False  # Disables Wake-on-lan capabilities

        nic_spec.device.deviceInfo = vim.Description()
        nic_spec.device.deviceInfo.summary = summary

        nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
        nic_spec.device.backing.useAutoDetect = False
        nic_spec.device.backing.network = network  # Sets port group to assign adapter to
        nic_spec.device.backing.deviceName = network.name  # Sets name of device on host system

        nic_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
        nic_spec.device.connectable.startConnected = True  # Ensures adapter is connected at boot
        nic_spec.device.connectable.allowGuestControl = True  # Allows guest OS to control device
        nic_spec.device.connectable.connected = True
        nic_spec.device.connectable.status = 'untried'
        # TODO: configure guest IP address if statically assigned
        self._edit(vim.vm.ConfigSpec(deviceChange=[nic_spec]))  # Apply change to VM

    def edit_nic(self, nic_id, port_group=None, summary=None):
        """
        Edits a VM NIC based on it's number
        :param nic_id: Number of network adapter on VM
        :param port_group: vim.Network object to assign NIC to [default: None]
        :param summary: Human-readable device description [default: None]
        """
        nic_label = 'Network adapter ' + str(nic_id)
        self._log.debug("Changing '%s' on VM '%s'", nic_label, self.name)
        virtual_nic_device = self.get_nic_by_name(nic_label)
        if not virtual_nic_device:
            self._log.error('Virtual %s could not be found!', nic_label)
            return
        nic_spec = vim.vm.device.VirtualDeviceSpec()
        nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
        nic_spec.device = virtual_nic_device
        if summary:
            nic_spec.device.deviceInfo.summary = str(summary)
        if port_group:
            self._log.debug("Changing PortGroup to: '%s'", port_group.name)
            nic_spec.device.backing.network = port_group
            nic_spec.device.backing.deviceName = port_group.name
        self._edit(vim.vm.ConfigSpec(deviceChange=[nic_spec]))  # Apply change to VM

    def delete_nic(self, nic_number):
        """
        Deletes VM vNIC based on it's number
        :param nic_number: Integer unit of the vNIC to delete
        """
        nic_label = 'Network adapter ' + str(nic_number)
        self._log.debug("Removing Virtual %s from '%s'", nic_label, self.name)
        virtual_nic_device = self.get_nic_by_name(nic_label)
        if virtual_nic_device is not None:
            virtual_nic_spec = vim.vm.device.VirtualDeviceSpec()
            virtual_nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.remove
            virtual_nic_spec.device = virtual_nic_device
            self._edit(vim.vm.ConfigSpec(deviceChange=[virtual_nic_spec]))  # Apply change to VM
        else:
            self._log.error("Virtual %s could not be found for '%s'", nic_label, self.name)

    def attach_iso(self, iso_name, datastore=None, boot=True):
        """
        Attaches an ISO image to a VM
        :param iso_name: Name of the ISO image to attach
        :param datastore: vim.Datastore where the ISO resides [default: VM's datastore]
        :param boot: Set VM to boot from the attached ISO [default: True]
        """
        self._log.debug("Adding ISO '%s' to '%s'", iso_name, self.name)
        if datastore is None:
            datastore = self.datastore

        drive_spec = vim.vm.device.VirtualDeviceSpec()
        drive_spec.device = vim.vm.device.VirtualCdrom()
        drive_spec.device.key = -1
        drive_spec.device.unitNumber = 0

        # Find a disk controller to attach to
        controller = self._find_free_ide_controller()
        if controller:
            drive_spec.device.controllerKey = controller.key
        else:
            self._log.error("Could not find a free IDE controller on '%s' to attach ISO '%s'",
                            self.name, iso_name)
            return

        drive_spec.device.backing = vim.vm.device.VirtualCdrom.IsoBackingInfo()
        drive_spec.device.backing.fileName = "[%s] %s" % (datastore.name, iso_name)  # Attach ISO
        drive_spec.device.backing.datastore = datastore  # Set datastore ISO is in

        drive_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
        drive_spec.device.connectable.allowGuestControl = True  # Allows guest OS to control device
        drive_spec.device.connectable.startConnected = True  # Ensures ISO is connected at boot

        drive_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        vm_spec = vim.vm.ConfigSpec(deviceChange=[drive_spec])
        if boot:  # Set the VM to boot from the ISO upon power on
            self._log.debug("Setting '%s' to boot from ISO '%s'", self.name, iso_name)
            order = [vim.vm.BootOptions.BootableCdromDevice()]
            order.extend(list(self._vm.config.bootOptions.bootOrder))
            vm_spec.bootOptions = vim.vm.BootOptions(bootOrder=order)
        self._edit(vm_spec)  # Apply change to VM

    def _find_free_ide_controller(self):
        """
        Finds a free IDE controller to use
        :return: vim.vm.device.VirtualIDEController
        """
        for dev in self._vm.config.hardware.device:
            if isinstance(dev, vim.vm.device.VirtualIDEController) and len(dev.device) < 2:
                return dev  # If there are less than 2 devices attached, we can use it
        return None

    def mount_tools(self):
        """ Mounts the installer for VMware Tools """
        wait_for_task(self._vm.MountToolsInstaller())

    def has_tools(self):
        """
        Checks if VMware Tools is installed and working
        :return: If tools are installed and working
        """
        tools = self._vm.summary.guest.toolsStatus
        return True if tools == "toolsOK" or tools == "toolsOld" else False

    def powered_on(self):
        """
        Determines if a VM is powered on
        :return: If VM is powered on
        """
        return self._vm.runtime.powerState == vim.VirtualMachine.PowerState.poweredOn

    def is_template(self):
        """
        Checks if VM is a template
        :return: If the VM is a template
        """
        return bool(self._vm.summary.config.template)

    # http://pubs.vmware.com/vsphere-60/topic/com.vmware.wssdk.apiref.doc/vim.vm.GuestOsDescriptor.GuestOsIdentifier.html
    def is_windows(self):
        """
        Checks if a VM's guest OS is Windows
        :return: Bool
        """
        return bool(str(self._vm.config.guestId).lower().startswith("win"))

    def _edit(self, config):
        """
        Reconfigures VM using the given configuration specification
        :param config: vim.vm.ConfigSpec
        """
        wait_for_task(self._vm.ReconfigVM_Task(config))

    def __str__(self):
        return str(self.name)

    def __hash__(self):
        return hash(self._vm.summary.config.instanceUuid)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.name == other.name \
               and hash(self) == hash(other)

    def __ne__(self, other):
        return not self.__eq__(other)
