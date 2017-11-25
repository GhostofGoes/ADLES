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
from adles.vsphere.folder_utils import find_in_folder


# Docs: https://goo.gl/CRhYEX
class VM:
    """ Represents a VMware vSphere Virtual Machine instance.

    .. warning::    You must call :meth:`create` if a vim.VirtualMachine object
                    is not used to initialize the instance.
    """
    __version__ = "0.10.0"

    def __init__(self, vm=None, name=None, folder=None, resource_pool=None,
                 datastore=None, host=None):
        """
        :param vm: VM instance to use instead of calling :meth:`create`
        :type vm: vim.VirtualMachine
        :param str name: Name of the VM
        :param folder: Folder in inventory to create the VM in
        :type folder: vim.Folder
        :param resource_pool: Resource pool to use for the VM
        :type resource_pool: vim.ResourcePool
        :param datastore: Datastore the VM is stored on
        :type datastore: vim.Datastore
        :param host: Host the VM runs on
        :type host: vim.HostSystem
        """
        self._log = logging.getLogger('VM')
        if vm is not None:
            self._vm = vm
            self.name = vm.name
            self.folder = vm.parent
            self.resource_pool = vm.resourcePool
            self.datastore = vm.datastore[0]
            self.host = vm.summary.runtime.host
            self.network = vm.network
            self.runtime = vm.runtime
            self.summary = vm.summary
        else:
            self._vm = None
            self.name = name
            self.folder = folder  # vim.Folder that will contain the VM
            self.resource_pool = resource_pool  # vim.ResourcePool to use VM
            self.datastore = datastore  # vim.Datastore object to store VM on
            self.host = host  # vim.HostSystem

    def create(self, template=None, cpus=None, cores=None, memory=None,
               max_consoles=None, version=None, firmware='efi',
               datastore_path=None):
        """Creates a Virtual Machine.
        :param vim.VirtualMachine template: Template VM to clone
        :param int cpus: Number of processors
        :param int cores: Number of processor cores
        :param int memory: Amount of RAM in MB
        :param int max_consoles: Maximum number of active console connections
        :param int version: Hardware version of the VM
        [default: highest host supports]
        :param str firmware: Firmware to emulate for the VM (efi | bios)
        :param str datastore_path: Path to existing VM files on datastore
        :return: If the creation was successful
        :rtype: bool
        """
        if template is not None:  # Use a template to create the VM
            self._log.debug("Creating VM '%s' by cloning %s",
                            self.name, template.name)
            clonespec = vim.vm.CloneSpec()
            clonespec.location = vim.vm.RelocateSpec(pool=self.resource_pool,
                                                     datastore=self.datastore)
            if not template.CloneVM_Task(folder=self.folder, name=self.name,
                                         spec=clonespec).wait(120):
                self._log.error("Error cloning VM %s", self.name)
                return False
        else:  # Generate the specification for and create the new VM
            self._log.debug("Creating VM '%s' from scratch", self.name)
            spec = vim.vm.ConfigSpec()
            spec.name = self.name
            spec.numCPUs = int(cpus) if cpus is not None else 1
            spec.numCoresPerSocket = int(cores) if cores is not None else 1
            spec.cpuHotAddEnabled = True
            spec.memoryMB = int(memory) if memory is not None else 512
            spec.memoryHotAddEnabled = True
            spec.firmware = str(firmware).lower()
            if version is not None:
                spec.version = "vmx-" + str(version)
            if max_consoles is not None:
                spec.maxMksConnections = int(max_consoles)
            vm_path = '[' + self.datastore.name + '] '
            if datastore_path:
                vm_path += str(datastore_path)
            vm_path += self.name + '/' + self.name + '.vmx'
            spec.files = vim.vm.FileInfo(vmPathName=vm_path)
            self._log.debug("Creating VM '%s' in folder '%s'",
                            self.name, self.folder.name)
            if not self.folder.CreateVM_Task(spec, self.resource_pool,
                                             self.host).wait():
                self._log.error("Error creating VM %s", self.name)
                return False

        self._vm = find_in_folder(self.folder, self.name,
                                  vimtype=vim.VirtualMachine)
        if not self._vm:
            self._log.error("Failed to make VM %s", self.name)
            return False
        self.network = self._vm.network
        self.runtime = self._vm.runtime
        self.summary = self._vm.summary
        if template is not None:  # Edit resources for a clone if specified
            self.edit_resources(cpus=cpus, cores=cores, memory=memory,
                                max_consoles=max_consoles)

        self._log.debug("Created VM %s", self.name)
        return True

    def destroy(self):
        """Destroys the VM."""
        self._log.debug("Destroying VM %s", self.name)
        if self.powered_on():
            self.change_state("off")
        self._vm.Destroy_Task().wait()

    def change_state(self, state, attempt_guest=True):
        """Generic power state change that uses guest OS operations if available.
        :param str state: State to change to (on | off | reset | suspend)
        :param bool attempt_guest: Attempt to use guest operations
        :return: If state change succeeded
        :rtype: bool
        """
        state = state.lower()  # Convert to lowercase for comparisons
        if self.is_template():
            self._log.error("VM '%s' is a Template, so state "
                            "cannot be changed to '%s'",
                            self.name, state)
        # Can't power on using guest ops
        elif attempt_guest and self.has_tools() and state != "on":
            if self._vm.summary.guest.toolsStatus == "toolsNotInstalled":
                self._log.error("Cannot change a VM's guest power state "
                                "without VMware Tools!")
                return False
            elif state == "shutdown" or state == "off":
                task = self._vm.ShutdownGuest()
            elif state == "reboot" or state == "reset":
                task = self._vm.RebootGuest()
            elif state == "standby" or state == "suspend":
                task = self._vm.StandbyGuest()
            else:
                self._log.error("Invalid guest_state argument: %s", state)
                return False
            self._log.debug("Changing guest power state of VM %s to: '%s'",
                            self.name, state)
            try:
                task.wait()
            except vim.fault.ToolsUnavailable:
                self._log.error("Can't change guest state of '%s': "
                                "Tools aren't running", self.name)
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
                self._log.error("Invalid state arg %s for VM %s",
                                state, self.name)
                return False
            self._log.debug("Changing power state of VM %s to: '%s'",
                            self.name, state)
            return bool(task.wait())

    def edit_resources(self, cpus=None, cores=None,
                       memory=None, max_consoles=None):
        """Edits the resource limits for the VM.
        :param int cpus: Number of CPUs
        :param int cores: Number of CPU cores
        :param int memory: Amount of RAM in MB
        :param int max_consoles: Maximum number of simultaneous 
        Mouse-Keyboard-Screen (MKS) console connections
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
        """Renames the VM.
        :param str name: New name for the VM
        """
        self._log.debug("Renaming VM %s to %s", self.name, name)
        if not self._vm.Rename_Task(newName=str(name)).wait():
            self._log.error("Failed to rename VM %s to %s", self.name, name)
        else:
            self.name = str(name)

    def upgrade(self, version):
        """Upgrades the hardware version of the VM.
        :param int version: Version of hardware to upgrade VM to
        [defaults to the latest version the VM's host supports]
        """
        try:
            self._vm.UpgradeVM_Task("vmx-" + str(version)).wait()
        except vim.fault.AlreadyUpgraded:
            self._log.warning("Hardware version is already up-to-date for %s",
                              self.name)

    def convert_template(self):
        """Converts a Virtual Machine to a Template."""
        if self.is_template():
            self._log.warning("%s is already a Template", self.name)
        else:
            self._log.debug("Converting '%s' to Template", self.name)
            self._vm.MarkAsTemplate()

    def convert_vm(self):
        """Converts a Template to a Virtual Machine."""
        self._log.debug("Converting '%s' to VM", self.name)
        self._vm.MarkAsVirtualMachine(self.resource_pool, self.host)

    def set_note(self, note):
        """Sets the note on the VM.
        :param str note: String to set the note to
        """
        self._edit(vim.vm.ConfigSpec(annotation=str(note)))

    # From: execute_program_in_vm.py in pyvmomi_community_samples
    def execute_program(self, process_manager, program_path,
                        username=None, password=None, program_args=""):
        """Executes a commandline program in the VM.
        This requires VMware Tools to be installed on the VM.
        :param vim.vm.guest.ProcessManager process_manager: vSphere process manager object
        :param str program_path: Path to the program inside the VM
        :param str username: User on VM to execute program using
        [default: current ADLES user]
        :param str password: Plaintext password for the User
        [default: prompt user]
        :param str program_args: Commandline arguments for the program
        :return: Program Process ID (PID) if it was executed successfully, 
        -1 if not
        :rtype: int
        """
        from os.path import basename
        prog_name = basename(program_path)
        if not self.has_tools():
            self._log.error("Cannot execute program %s in VM %s: "
                            "VMware Tools is not running",
                            prog_name, self.name)
            return -1
        if username is None:
            from getpass import getuser
            username = getuser()
        if password is None:
            from getpass import getpass
            password = getpass("Enter password of user %s to "
                               "execute program %s on VM %s"
                               % (username, prog_name, self.name))
        creds = vim.vm.guest.NamePasswordAuthentication(username=username,
                                                        password=password)
        try:
            prog_spec = vim.vm.guest.ProcessManager.ProgramSpec(
                programPath=program_path, arguments=program_args)
            pid = process_manager.StartProgramInGuest(self._vm,
                                                      creds, prog_spec)
            self._log.debug("Successfully started program %s in VM %s. PID: %s",
                            prog_name, self.name, pid)
            return pid
        except IOError as e:
            self._log.error("Could not execute program %s in VM %s: %s",
                            prog_name, self.name, str(e))
            return -1

    def snapshot_disk_usage(self):
        """Determines the total disk usage of a VM's snapshots.
        :return: Human-readable disk usage of the snapshots
        :rtype: str
        """
        from re import search
        disk_list = self._vm.layoutEx.file
        size = 0
        for disk in disk_list:
            if disk.type == 'snapshotData':
                size += disk.size
            ss_disk = search(r'0000\d\d', disk.name)
            if ss_disk:
                size += disk.size
        return utils.sizeof_fmt(size)

    def create_snapshot(self, name, description='', memory=False, quiesce=True):
        """Creates a snapshot of the VM.
        :param str name: Name of the snapshot
        :param str description: Text description of the snapshot
        :param bool memory: Memory dump of the VM is included in the snapshot
        :param bool quiesce: Quiesce VM disks (Requires VMware Tools)
        """
        self._log.info("Creating snapshot '%s' of VM '%s'", name, self.name)
        if not self._vm.CreateSnapshot_Task(name=name, description=description,
                                            memory=bool(memory),
                                            quiesce=quiesce).wait():
            self._log.error("Failed to take snapshot of VM %s", self.name)

    def revert_to_snapshot(self, snapshot):
        """Reverts VM to the named snapshot.
        :param str snapshot: Name of the snapshot to revert to
        """
        self._log.info("Reverting '%s' to the snapshot '%s'",
                       self.name, snapshot)
        self.get_snapshot(snapshot).RevertToSnapshot_Task().wait()

    def revert_to_current_snapshot(self):
        """Reverts the VM to the most recent snapshot."""
        self._log.info("Reverting '%s' to the current snapshot", self.name)
        self._vm.RevertToCurrentSnapshot_Task().wait()

    def remove_snapshot(self, snapshot, remove_children=True,
                        consolidate_disks=True):
        """Removes the named snapshot from the VM.
        :param str snapshot: Name of the snapshot to remove
        :param bool remove_children: Removal of the entire snapshot subtree
        :param bool consolidate_disks: Virtual disks of deleted snapshot 
        will be merged with other disks if possible
        """
        self._log.info("Removing snapshot '%s' from '%s'", snapshot, self.name)
        self.get_snapshot(snapshot).RemoveSnapshot_Task(
            remove_children, consolidate_disks).wait()

    def remove_all_snapshots(self, consolidate_disks=True):
        """Removes all snapshots associated with the VM.
        :param bool consolidate_disks: Virtual disks of the deleted snapshot 
        will be merged with other disks if possible
        """
        self._log.info("Removing ALL snapshots for %s", self.name)
        self._vm.RemoveAllSnapshots_Task(consolidate_disks).wait()

    # Based on: add_nic_to_vm in pyvmomi-community-samples
    def add_nic(self, network, summary="default-summary", model="e1000"):
        """Add a NIC in the portgroup to the VM.
        :param vim.Network network: Network to attach NIC to
        :param str summary: Human-readable device info
        [default: default-summary]
        :param str model: Model of virtual network adapter.
        Options: (e1000 | e1000e | vmxnet | vmxnet2 
        | vmxnet3 | pcnet32 | sriov)
        e1000 will work on Windows Server 2003+, 
        and e1000e is supported on Windows Server 2012+.
        VMXNET adapters require VMware Tools to be installed, 
        and provide enhanced performance.
        `Read this for more details: 
        <http://rickardnobel.se/vmxnet3-vs-e1000e-and-e1000-part-1/>`_
        """
        if not isinstance(network, vim.Network):
            self._log.error("Invalid network type when adding vNIC "
                            "to VM '%s': %s", self.name, type(network).__name__)
        self._log.debug("Adding NIC to VM '%s'\nNetwork: '%s'"
                        "\tSummary: '%s'\tNIC Model: '%s'",
                        self.name, network.name, summary, model)

        # Create base object to add configurations to
        spec = vim.vm.device.VirtualDeviceSpec()
        spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add

        # Set the type of network adapter
        if model == "e1000":
            spec.device = vim.vm.device.VirtualE1000()
        elif model == "e1000e":
            spec.device = vim.vm.device.VirtualE1000e()
        elif model == "vmxnet":
            spec.device = vim.vm.device.VirtualVmxnet()
        elif model == "vmxnet2":
            spec.device = vim.vm.device.VirtualVmxnet2()
        elif model == "vmxnet3":
            spec.device = vim.vm.device.VirtualVmxnet3()
        elif model == "pcnet32":
            spec.device = vim.vm.device.VirtualPCNet32()
        elif model == "sriov":
            spec.device = vim.vm.device.VirtualSriovEthernetCard()
        else:
            self._log.error("Invalid NIC model: '%s'\n"
                            "Defaulting to e1000...", model)
            spec.device = vim.vm.device.VirtualE1000()

        # Sets how MAC address is assigned
        spec.device.addressType = 'generated'
        # Disables Wake-on-lan capabilities
        spec.device.wakeOnLanEnabled = False

        spec.device.deviceInfo = vim.Description()
        spec.device.deviceInfo.summary = summary

        spec.device.backing = \
            vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
        spec.device.backing.useAutoDetect = False
        # Sets port group to assign adapter to
        spec.device.backing.network = network
        # Sets name of device on host system
        spec.device.backing.deviceName = network.name

        spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
        # Ensures adapter is connected at boot
        spec.device.connectable.startConnected = True
        # Allows guest OS to control device
        spec.device.connectable.allowGuestControl = True
        spec.device.connectable.connected = True
        spec.device.connectable.status = 'untried'
        self._edit(vim.vm.ConfigSpec(deviceChange=[spec]))  # Apply change to VM

    def edit_nic(self, nic_id, network=None, summary=None):
        """Edits a vNIC based on it's number.
        :param int nic_id: Number of network adapter on VM
        :param network: Network to assign the vNIC to
        :type network: vim.Network
        :param str summary: Human-readable device description
        :return: If the edit operation was successful
        :rtype: bool
        """
        nic_label = 'Network adapter ' + str(nic_id)
        self._log.debug("Changing '%s' on VM '%s'", nic_label, self.name)
        virtual_nic_device = self.get_nic_by_name(nic_label)
        if not virtual_nic_device:
            self._log.error('Virtual %s could not be found!', nic_label)
            return False
        nic_spec = vim.vm.device.VirtualDeviceSpec()
        nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
        nic_spec.device = virtual_nic_device
        if summary:
            nic_spec.device.deviceInfo.summary = str(summary)
        if network:
            self._log.debug("Changing PortGroup to: '%s'", network.name)
            nic_spec.device.backing.network = network
            nic_spec.device.backing.deviceName = network.name

        # Apply change to VM
        self._edit(vim.vm.ConfigSpec(deviceChange=[nic_spec]))
        return True

    # Based on: delete_nic_from_vm in pyvmomi-community-samples
    def remove_nic(self, nic_number):
        """Deletes a vNIC based on it's number.
        :param int nic_number: Number of the vNIC to delete
        :return: If removal succeeded
        :rtype: bool
        """
        nic_label = "Network adapter " + str(nic_number)
        self._log.debug("Removing Virtual %s from '%s'", nic_label, self.name)
        virtual_nic_device = self.get_nic_by_name(nic_label)
        if virtual_nic_device is not None:
            virtual_nic_spec = vim.vm.device.VirtualDeviceSpec()
            virtual_nic_spec.operation = \
                vim.vm.device.VirtualDeviceSpec.Operation.remove
            virtual_nic_spec.device = virtual_nic_device

            # Apply change to VM
            self._edit(vim.vm.ConfigSpec(deviceChange=[virtual_nic_spec]))
            return True
        else:
            self._log.error("Virtual %s could not be found for '%s'",
                            nic_label, self.name)
            return False

    def remove_device(self, device_spec):
        """Removes a device from the VM.
        :param device_spec: The specification of the device to remove
        :type device_spec: vim.vm.device.VirtualDeviceSpec
        """
        self._log.debug("Removing device '%s' from '%s'",
                        device_spec.name, self.name)
        device_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.remove
        self._edit(vim.vm.ConfigSpec(deviceChange=[device_spec]))

    # Based on: delete_disk_from_vm.py in pyvmomi_community_samples
    def remove_hdd(self, disk_number):
        """Removes a numbered Virtual Hard Disk from the VM.
        :param int disk_number: Number of the HDD to remove
        :return: If the HDD was successfully removed
        :rtype: bool
        """
        hdd_label = "Hard disk " + str(disk_number)
        self._log.debug("Removing Virtual HDD %s from %s", hdd_label, self.name)
        dev = self.get_hdd_by_name(hdd_label)
        if not dev:
            self._log.error("Could not find Virtual %s to remove", hdd_label)
            return False
        else:
            spec = vim.vm.device.VirtualDeviceSpec(device=dev)
            self.remove_device(device_spec=spec)
            return True

    # Based on: resize_disk.py from pyvmomi-community-samples
    def resize_hdd(self, size, disk_number=1, disk_prefix="Hard disk "):
        """Resize a virtual HDD on the VM.
        :param int size: New disk size in KB
        :param int disk_number: Disk number
        :param disk_prefix: Disk label prefix
        :return: If the resize was successful
        :rtype: bool
        """
        # TODO: !!UNTESTED!!
        self._log.warning("Usage of untested method resize_hdd")
        hdd_label = disk_prefix + str(disk_number)
        self._log.debug("Resizing %s on VM %s to %d",
                        hdd_label, self.name, size)

        # Find the disk device
        dev = self.get_hdd_by_name(hdd_label)
        if not dev:
            self._log.error("Could not find Virtual %s to resize", hdd_label)
            return False
        else:
            virtual_disk_spec = vim.vm.device.VirtualDeviceSpec()
            virtual_disk_spec.operation = \
                vim.vm.device.VirtualDeviceSpec.operation.edit
            virtual_disk_spec.device = dev
            virtual_disk_spec.device.capacityInKB = int(size)
            self._edit(vim.vm.ConfigSpec(deviceChange=[virtual_disk_spec]))
            return True

    # Based on: change_disk_mode.py in pyvmomi-community-samples
    def change_hdd_mode(self, mode, disk_number=1, disk_prefix="Hard disk "):
        """Change the mode on a virtual HDD.
        :param str mode: New disk mode
        :param int disk_number: Disk number
        :param str disk_prefix: Disk label prefix
        :return: If the disk mode change operation was successful
        :rtype: bool
        """
        # TODO: !!UNTESTED!!
        self._log.warning("Usage of untested method change_hdd_mode")
        hdd_label = disk_prefix + str(disk_number)
        self._log.debug("Changing mode of %s on VM %s to %s",
                        hdd_label, self.name, mode)

        # Find the disk device
        dev = self.get_hdd_by_name(hdd_label)
        if not dev:
            self._log.error("Could not find Virtual %s to resize", hdd_label)
            return False
        else:
            virtual_disk_spec = vim.vm.device.VirtualDeviceSpec()
            virtual_disk_spec.operation = \
                vim.vm.device.VirtualDeviceSpec.operation.edit
            virtual_disk_spec.device = dev
            virtual_disk_spec.device.backing.diskMode = str(mode)
            self._edit(vim.vm.ConfigSpec(deviceChange=[virtual_disk_spec]))
            return True

    def attach_iso(self, iso_path, datastore=None, boot=True):
        """
        Attaches an ISO image to a VM.
        :param str iso_path: Path in the Datastore of the ISO image to attach
        :param vim.Datastore datastore: Datastore where the ISO resides
        [defaults to the VM's datastore]
        :param bool boot: Set VM to boot from the attached ISO
        """
        self._log.debug("Adding ISO '%s' to '%s'", iso_path, self.name)
        if datastore is None:
            datastore = self.datastore

        spec = vim.vm.device.VirtualDeviceSpec()
        spec.device = vim.vm.device.VirtualCdrom()
        spec.device.key = -1
        spec.device.unitNumber = 0

        # Find a disk controller to attach to
        controller = self._find_free_ide_controller()
        if controller:
            spec.device.controllerKey = controller.key
        else:
            self._log.error("Could not find a free IDE controller "
                            "on '%s' to attach ISO '%s'",
                            self.name, iso_path)
            return

        spec.device.backing = vim.vm.device.VirtualCdrom.IsoBackingInfo()
        # Attach ISO
        spec.device.backing.fileName = "[%s] %s" % (datastore.name, iso_path)
        # Set datastore containing the ISO file
        spec.device.backing.datastore = datastore

        spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
        # Allows guest OS to control device
        spec.device.connectable.allowGuestControl = True
        # Ensures ISO is connected at boot
        spec.device.connectable.startConnected = True

        spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        vm_spec = vim.vm.ConfigSpec(deviceChange=[spec])
        if boot:  # Set the VM to boot from the ISO upon power on
            self._log.debug("Setting '%s' to boot from ISO '%s'",
                            self.name, iso_path)
            order = [vim.vm.BootOptions.BootableCdromDevice()]
            order.extend(list(self._vm.config.bootOptions.bootOrder))
            vm_spec.bootOptions = vim.vm.BootOptions(bootOrder=order)
        self._edit(vm_spec)  # Apply change to VM

    def _find_free_ide_controller(self):
        """
        Finds a free IDE controller to use.

        :return: The free IDE controller
        :rtype: vim.vm.device.VirtualIDEController or None
        """
        for dev in self._vm.config.hardware.device:
            if isinstance(dev, vim.vm.device.VirtualIDEController) \
                    and len(dev.device) < 2:
                # If there are less than 2 devices attached, we can use it
                return dev
        return None

    def relocate(self, host=None, datastore=None):
        """Relocates the VM to a new host and/or datastore
        :param vim.Host host:
        :param vim.Datastore datastore:
        """
        # TODO: !!UNTESTED!!
        self._log.warning("Usage of untested method relocate")
        if host is None:
            host = self.host
        if datastore is None:
            datastore = self.datastore
        self._log.debug("Relocating VM %s to host %s and datastore %s",
                        self.name, host.name, datastore.name)
        self._vm.Relocate(
            spec=vim.vm.RelocateSpec(host=host, datastore=datastore)).wait()

    def mount_tools(self):
        """Mount the installer for VMware Tools."""
        self._log.debug("Mounting tools installer on %s", self.name)
        self._vm.MountToolsInstaller().wait()

    def get_datastore_folder(self):
        """Gets the name of the VM's folder on the datastore.
        :return: The name of the datastore folder with the VM's files
        :rtype: str
        """
        return os.path.split(self._vm.summary.config.vmPathName)[0]

    def get_hdd_by_name(self, name):
        """Gets a Virtual HDD from the VM.
        :param name: Name of the virtual HDD
        :return: The HDD device
        :rtype: vim.vm.device.VirtualDisk or None
        """
        for dev in self._vm.config.hardware.device:
            if isinstance(dev, vim.vm.device.VirtualDisk) and \
                            dev.deviceInfo.label.lower() == name.lower():
                return dev
        return None

    def get_vim_vm(self):
        """Get the vim.VirtualMachine instance of the VM.
        :return: The vim instance of the VM
        :rtype: vim.VirtualMachine
        """
        return self._vm

    def get_nics(self):
        """Returns a list of all Virtual Network Interface Cards (vNICs) on the VM.
        :return: All vNICs on the VM
        :rtype: list(vim.vm.device.VirtualEthernetCard) or list
        """
        return [dev for dev in self._vm.config.hardware.device if is_vnic(dev)]

    def get_nic_by_name(self, name):
        """Gets a Virtual Network Interface Card (vNIC) from a VM.
        :param str  name: Name of the vNIC
        :return: The vNIC found
        :rtype: vim.vm.device.VirtualEthernetCard or None
        """
        for dev in self._vm.config.hardware.device:
            if is_vnic(dev) and dev.deviceInfo.label.lower() == name.lower():
                return dev
        self._log.debug("Could not find vNIC '%s' on '%s'", name, self.name)
        return None

    def get_nic_by_id(self, nic_id):
        """Get a vNIC by integer ID.
        :param int nic_id: ID of the vNIC
        :return: The vNIC found
        :rtype: vim.vm.device.VirtualEthernetCard or None
        """
        return self.get_nic_by_name("Network Adapter " + str(nic_id))

    def get_nic_by_network(self, network):
        """Finds a vNIC by it's network backing.
        :param vim.Network network: Network of the vNIC to match
        :return: Name of the vNIC
        :rtype: str or None
        """
        for dev in self._vm.config.hardware.device:
            if is_vnic(dev) and dev.backing.network == network:
                return dev
        self._log.debug("Could not find vNIC with network '%s' on '%s'",
                        network.name, self.name)
        return None

    def get_snapshot(self, snapshot=None):
        """Retrieves the named snapshot from the VM.
        :param str snapshot: Name of the snapshot [default: current snapshot]
        :return: The snapshot found
        :rtype: vim.Snapshot or None
        """
        if snapshot is None:
            return self._vm.snapshot.currentSnapshot
        else:
            for snap in self.get_all_snapshots():
                if snap.name == snapshot:
                    return snap.snapshot
            return None

    def get_all_snapshots(self):
        """Retrieves a list of all snapshots of the VM.
        :return: Nested List of vim.Snapshot objects
        :rtype: list(vim.Snapshot) or None
        """
        return self._get_snapshots_recursive(self._vm.snapshot.rootSnapshotList)

    # From: https://github.com/imsweb/ezmomi
    def _get_snapshots_recursive(self, snap_tree):
        """Recursively finds all snapshots in the tree.
        :param snap_tree: Tree of snapshots
        :return: Nested List of vim.Snapshot objects
        :rtype: list(vim.Snapshot) or None
        """
        local_snap = []
        for snap in snap_tree:
            local_snap.append(snap)
        for snap in snap_tree:
            recurse_snap = self._get_snapshots_recursive(snap.childSnapshotList)
            if recurse_snap:
                local_snap.extend(recurse_snap)
        return local_snap

    def get_snapshot_info(self, name=None):
        """Human-readable info on a snapshot.
        :param str name: Name of the snapshot to get
        [defaults to the current snapshot]
        :return: Info on the snapshot found
        :rtype: str
        """
        snap = self.get_snapshot(name)
        return "\nName: %s; Description: %s; CreateTime: %s; State: %s" % \
               (snap.name, snap.description, snap.createTime, snap.state)

    def get_all_snapshots_info(self):
        """Enumerates the full snapshot tree of the VM and makes it human-readable.
        :return: The human-readable snapshot tree info
        :rtype: str
        """
        # Check for ideas: snapshot_operations.py in pyvmomi_community_samples
        raise NotImplementedError  # TODO: implement

    def get_info(self, detailed=False, uuids=False,
                 snapshot=False, vnics=False):
        """Get human-readable information for a VM.
        :param bool detailed: Add detailed information, e.g maximum memory used
        :param bool uuids: Whether to get UUID information
        :param bool snapshot: Shows the current snapshot, if any
        :param bool vnics: Add information about vNICs on the VM
        :return: The VM's information
        :rtype: str
        """
        info_string = "\n"
        summary = self._vm.summary  # https://goo.gl/KJRrqS
        config = self._vm.config    # https://goo.gl/xFdCby
        info_string += "Name          : %s\n" % self.name
        info_string += "Status        : %s\n" % str(summary.overallStatus)
        info_string += "Power State   : %s\n" % summary.runtime.powerState
        if self._vm.guest:
            info_string += "Guest State   : %s\n" % self._vm.guest.guestState
        info_string += "Last modified : %s\n" \
                       % str(self._vm.config.modified)  # datetime object
        if hasattr(summary.runtime, 'cleanPowerOff'):
            info_string += "Clean poweroff: %s\n" % \
                           summary.runtime.cleanPowerOff
        if detailed:
            info_string += "Num consoles  : %d\n" % \
                           summary.runtime.numMksConnections
        info_string += "Host          : %s\n" % self.host.name
        info_string += "Datastore     : %s\n" % self.datastore
        info_string += "HW Version    : %s\n" % config.version
        info_string += "Guest OS      : %s\n" % summary.config.guestFullName
        info_string += "Num CPUs      : %s\n" % summary.config.numCpu
        info_string += "Memory (MB)   : %s\n" % summary.config.memorySizeMB
        if detailed:
            info_string += "Num vNICs     : %s\n" % \
                           summary.config.numEthernetCards
            info_string += "Num Disks     : %s\n" % \
                           summary.config.numVirtualDisks
        info_string += "IsTemplate    : %s\n" % summary.config.template  # bool
        if detailed:
            info_string += "Config Path   : %s\n" % summary.config.vmPathName
        info_string += "Folder:       : %s\n" % self._vm.parent.name
        if self._vm.guest:
            info_string += "IP            : %s\n" % self._vm.guest.ipAddress
            info_string += "Hostname:     : %s\n" % self._vm.guest.hostName
            info_string += "Tools status  : %s\n" % \
                           self._vm.guest.toolsRunningStatus
            info_string += "Tools version : %s\n" % \
                           self._vm.guest.toolsVersionStatus2
        if vnics:
            vm_nics = self.get_nics()
            for num, vnic in zip(range(1, len(vm_nics) + 1), vm_nics):
                info_string += "vNIC %d label   : %s\n" % \
                               (num, vnic.deviceInfo.label)
                info_string += "vNIC %d summary : %s\n" % \
                               (num, vnic.deviceInfo.summary)
                info_string += "vNIC %d network : %s\n" % \
                               (num, vnic.backing.network.name)
        if uuids:
            info_string += "Instance UUID : %s\n" % summary.config.instanceUuid
            info_string += "Bios UUID     : %s\n" % summary.config.uuid
        if summary.runtime.question:
            info_string += "Question      : %s\n" % \
                           summary.runtime.question.text
        if summary.config.annotation:
            info_string += "Annotation    : %s\n" % summary.config.annotation
        if snapshot and self._vm.snapshot and hasattr(self._vm.snapshot,
                                                      'currentSnapshot'):
            info_string += "Current Snapshot: %s\n" % \
                           self._vm.snapshot.currentSnapshot.config.name
            info_string += "Disk usage of all snapshots: %s\n" % \
                           self.snapshot_disk_usage()
        if detailed and summary.runtime:
            info_string += "Last Poweron  : %s\n" % \
                           str(summary.runtime.bootTime)  # datetime object
            info_string += "Max CPU usage : %s\n" % summary.runtime.maxCpuUsage
            info_string += "Max Mem usage : %s\n" % \
                           summary.runtime.maxMemoryUsage
            info_string += "Last suspended: %s\n" % summary.runtime.suspendTime
        return info_string

    def screenshot(self):
        """Takes a screenshot of a VM.
        :return: Path to datastore location of the screenshot
        :rtype: str
        """
        self._log.debug("Taking screenshot of %s", self.name)
        return self._vm.CreateScreenshot_Task().wait()

    def has_tools(self):
        """Checks if VMware Tools is installed and working.
        :return: If tools are installed and working
        :rtype: bool
        """
        tools = self._vm.summary.guest.toolsStatus
        return True if tools == "toolsOK" or tools == "toolsOld" else False

    def powered_on(self):
        """Determines if a VM is powered on.
        :return: If VM is powered on
        :rtype: bool
        """
        return self._vm.runtime.powerState == \
            vim.VirtualMachine.PowerState.poweredOn

    def is_template(self):
        """Checks if VM is a template.
        :return: If the VM is a template
        :rtype: bool
        """
        return bool(self._vm.summary.config.template)

    def is_windows(self):
        """Checks if a VM's guest OS is Windows.
        :return: If guest OS is Windows
        :rtype: bool
        """
        return bool(str(self._vm.config.guestId).lower().startswith("win"))

    def _edit(self, config):
        """Reconfigures VM with the given configuration specification.
        :param vim.vm.ConfigSpec config: The configuration specification to apply
        :return: If the edit was successful
        """
        if not self._vm.ReconfigVM_Task(config).wait():
            self._log.error("Failed to edit VM %s", self.name)
            return False
        else:
            return True

    def _customize(self, customization):
        """Customizes the VM using the given customization specification.
        :param vim.vm.customization.Specification customization: The customization specification to apply
        :return: If the customization was successful
        :rtype: bool
        """
        if not self._vm.CheckCustomizationSpec(spec=customization).wait():
            self._log.error("Customization check failed for VM %s", self.name)
            return False
        elif not self._vm.CustomizeVM_Task(spec=customization).wait():
            self._log.error("Failed to customize VM %s", self.name)
            return False
        else:
            return True

    def __str__(self):
        return str(self.name)

    def __hash__(self):
        return hash(self._vm.summary.config.instanceUuid)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.name == other.name \
               and hash(self) == hash(other)

    def __ne__(self, other):
        return not self.__eq__(other)


def is_vnic(device):
    """Checks if the device is a VirtualEthernetCard.
    :param device: The device to check
    :return: If the device is a vNIC
    :rtype: bool
    """
    return isinstance(device, vim.vm.device.VirtualEthernetCard)
