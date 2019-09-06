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
import sys

import tqdm
from humanfriendly.prompts import prompt_for_choice, prompt_for_confirmation

from adles.scripts.script_base import Script
from adles.utils import default_prompt, pad
from adles.vsphere.folder_utils import format_structure
from adles.vsphere.vm import VM
from adles.vsphere.vsphere_utils import is_vm, make_vsphere, resolve_path


class VsphereScript(Script):
    """Base class for all vSphere CLI scripts."""

    def __init__(self, server_filename=None):
        super(VsphereScript, self).__init__()
        self.server = make_vsphere(filename=server_filename)


class CleanupVms(VsphereScript):
    """Cleanup and Destroy Virtual Machines (VMs)
    and VM Folders in a vSphere environment."""

    __version__ = "0.5.12"
    name = "cleanup"

    def run(self):
        if prompt_for_confirmation("Multiple VMs? "):
            folder, folder_name = resolve_path(
                self.server, "folder", "that has the VMs/folders " "you want to destroy"
            )

            # Display folder structure
            if prompt_for_confirmation("Display the folder structure? "):
                self._log.info(
                    "Folder structure: \n%s",
                    format_structure(
                        folder.enumerate(recursive=True, power_status=True)
                    ),
                )

            # Prompt user to configure destruction options
            print("Answer the following questions to configure the cleanup")  # noqa
            if prompt_for_confirmation(
                "Destroy everything in and " "including the folder? "
            ):
                vm_prefix = ""
                folder_prefix = ""
                recursive = True
                destroy_folders = True
                destroy_self = True
            else:
                vm_prefix = default_prompt(
                    "Prefix of VMs you wish to destroy" " (CASE SENSITIVE!)", default=""
                )
                recursive = prompt_for_confirmation(
                    "Recursively descend " "into folders? "
                )
                destroy_folders = prompt_for_confirmation(
                    "Destroy folders in " "addition to VMs? "
                )
                if destroy_folders:
                    folder_prefix = default_prompt(
                        "Prefix of folders " "you wish to destroy" " (CASE SENSITIVE!)",
                        default="",
                    )
                    destroy_self = prompt_for_confirmation(
                        "Destroy the " "folder itself? "
                    )
                else:
                    folder_prefix = ""
                    destroy_self = False

            # Show user what options they selected
            self._log.info(
                "Options selected\nVM Prefix: %s\n"
                "Folder Prefix: %s\nRecursive: %s\n"
                "Folder-destruction: %s\nSelf-destruction: %s",
                str(vm_prefix),
                str(folder_prefix),
                recursive,
                destroy_folders,
                destroy_self,
            )

            # Show how many items matched the options
            v, f = folder.retrieve_items(vm_prefix, folder_prefix, recursive=True)
            num_vms = len(v)
            if destroy_folders:
                num_folders = len(f)
                if destroy_self:
                    num_folders += 1
            else:
                num_folders = 0
            self._log.info(
                "%d VMs and %d folders match the options", num_vms, num_folders
            )

            # Confirm and destroy
            if prompt_for_confirmation("Continue with destruction? "):
                self._log.info("Destroying folder '%s'...", folder_name)
                folder.cleanup(
                    vm_prefix=vm_prefix,
                    folder_prefix=folder_prefix,
                    recursive=recursive,
                    destroy_folders=destroy_folders,
                    destroy_self=destroy_self,
                )
            else:
                self._log.info("Destruction cancelled")
        else:
            vm = resolve_path(self.server, "vm", "to destroy")[0]

            if prompt_for_confirmation("Display VM info? "):
                self._log.info(
                    vm.get_info(detailed=True, uuids=True, snapshot=True, vnics=True)
                )

            if vm.is_template():  # Warn if template
                if not prompt_for_confirmation(
                    "VM '%s' is a Template. " "Continue? " % vm.name
                ):
                    sys.exit(0)

            if prompt_for_confirmation("Continue with destruction? "):
                self._log.info("Destroying VM '%s'", vm.name)
                vm.destroy()
            else:
                self._log.info("Destruction cancelled")


class CloneVms(VsphereScript):
    """Clone multiple Virtual Machines in vSphere."""

    __version__ = "0.5.12"
    name = "clone"

    def run(self):
        vms = []
        vm_names = []

        # Single-vm source
        if prompt_for_confirmation("Do you want to clone from a single VM?"):
            v = resolve_path(self.server, "VM", "or template you wish to clone")[0]
            vms.append(v)
            vm_names.append(input("Base name for instances to be created: "))
        # Multi-VM source
        else:
            folder_from, from_name = resolve_path(
                self.server, "folder", "you want to clone all VMs in"
            )
            # Get VMs in the folder
            v = [VM(vm=x) for x in folder_from.childEntity if is_vm(x)]
            vms.extend(v)
            self._log.info("%d VMs found in source folder %s", len(v), from_name)
            if not prompt_for_confirmation("Keep the same names? "):
                names = []
                for i in range(len(v)):
                    names.append(input("Enter base name for VM %d: " % i))
            else:
                names = list(map(lambda x: x.name, v))  # Same names as sources
            vm_names.extend(names)

        create_in, create_in_name = resolve_path(
            self.server, "folder", "in which to create VMs"
        )
        instance_folder_base = None
        if prompt_for_confirmation(
            "Do you want to create a " "folder for each instance? "
        ):
            instance_folder_base = input("Enter instance folder base name: ")

        num_instances = int(input("Number of instances to be created: "))

        # Determine what will be the default
        pool_name = self.server.get_pool().name
        pool_name = default_prompt(
            prompt="Resource pool to assign VMs to", default=pool_name
        )
        pool = self.server.get_pool(pool_name)

        datastore_name = default_prompt(prompt="Datastore to put clones on")
        datastore = self.server.get_datastore(datastore_name)

        self._log.info(
            "Creating %d instances under folder %s", num_instances, create_in_name
        )
        for instance in tqdm.trange(
            num_instances, desc="Creating instances", unit="instances"
        ):
            with tqdm.tqdm(
                total=len(vm_names), leave=False, desc="Creating VMs", unit="VMs"
            ) as pbar:
                for vm, name in zip(vms, vm_names):
                    pbar.set_postfix_str(name)
                    if instance_folder_base:
                        # Create instance folders for a nested clone
                        f = self.server.create_folder(
                            instance_folder_base + pad(instance), create_in=create_in
                        )
                        vm_name = name
                    else:
                        f = create_in
                        vm_name = name + pad(instance)  # Append instance number

                    new_vm = VM(
                        name=vm_name, folder=f, resource_pool=pool, datastore=datastore
                    )
                    new_vm.create(template=vm.get_vim_vm())
                    pbar.update()


class VmPower(VsphereScript):
    """Power operations for Virtual Machines in vSphere."""

    __version__ = "0.4.0"
    name = "power"

    def run(self):
        print("Enter the power operation you wish to perform")  # noqa: T001
        operation = prompt_for_choice(["on", "off", "reset", "suspend"], padding=False)
        attempt_guest = prompt_for_confirmation(
            "Attempt to use guest OS " "operations, if available? "
        )

        if prompt_for_confirmation("Multiple VMs? ", default=True):
            folder, folder_name = resolve_path(self.server, "folder", "with VMs")
            vms = [VM(vm=x) for x in folder.childEntity if is_vm(x)]
            self._log.info("Found %d VMs in folder '%s'", len(vms), folder_name)
            if prompt_for_confirmation("Show the status of the " "VMs in the folder? "):
                self._log.info(
                    "Folder structure: \n%s",
                    format_structure(
                        folder.enumerate(recursive=True, power_status=True)
                    ),
                )
            if prompt_for_confirmation("Continue? ", default=True):
                pbar = tqdm.tqdm(
                    vms, unit="VMs", desc="Performing power operation " + operation
                )
                for vm in pbar:
                    pbar.set_postfix_str(vm.name)
                    vm.change_state(operation, attempt_guest)
                pbar.close()

        else:
            vm = resolve_path(self.server, "VM")[0]
            self._log.info(
                "Changing power state of '%s' " "to '%s'", vm.name, operation
            )
            vm.change_state(operation, attempt_guest)


class VsphereInfo(VsphereScript):
    """Query information about a vSphere environment and objects within it."""

    __version__ = "0.6.5"
    name = "info"

    def run(self):
        print("What type of thing do you want to get information on?")  # noqa: T001
        thing_type = prompt_for_choice(
            ["vm", "datastore", "vsphere", "folder"], padding=False
        )

        # Single Virtual Machine
        if thing_type == "vm":
            vm = resolve_path(self.server, "vm", "you want to get information on")[0]
            self._log.info(
                vm.get_info(detailed=True, uuids=True, snapshot=True, vnics=True)
            )

        # Datastore
        elif thing_type == "datastore":
            ds = self.server.get_datastore(
                input(
                    "Enter name of the Datastore [leave "
                    "blank for first datastore found]: "
                )
            )
            self._log.info(ds.get_info())

        # vCenter server
        elif thing_type == "vsphere":
            self._log.info(str(self.server))

        # Folder
        elif thing_type == "folder":
            folder, folder_name = resolve_path(self.server, "folder")
            if "VirtualMachine" in folder.childType and prompt_for_confirmation(
                "Want to see power state " "of VMs in the folder?"
            ):
                contents = folder.enumerate(recursive=True, power_status=True)
            else:
                contents = folder.enumerate(recursive=True, power_status=False)
            self._log.info(
                "Information for Folder %s\n"
                "Types of items folder can contain: %s\n%s",
                folder_name,
                str(folder.childType),
                format_structure(contents),
            )

        # That's not a thing!
        else:
            self._log.info("Invalid selection: %s", thing_type)


class VmSnapshot(VsphereScript):
    """Perform Snapshot operations on Virtual
    Machines in a vSphere environment."""

    __version__ = "0.3.0"
    name = "snapshot"

    def run(self):
        print("Enter Snapshot operation to perform")  # noqa: T001
        op = prompt_for_choice(
            [
                "create",
                "revert",
                "revert-current",
                "remove",
                "remove-all",
                "get",
                "get-current",
                "get-all",
                "disk-usage",
            ],
            padding=False,
        )
        if op in ["create", "revert", "remove", "get"]:
            name = input("Name of snapshot to %s: " % op)
            if op == "create":
                desc = input("Description of snapshot to create: ")
                memory = prompt_for_confirmation("Include memory?")
                quiesce = prompt_for_confirmation(
                    "Quiesce disks? (Requires VMware " "Tools to be running on the VM)"
                )
            elif op == "remove":
                children = prompt_for_confirmation(
                    "Remove any children of the " "snapshot?", default=True
                )

        if prompt_for_confirmation("Multiple VMs? ", default=True):
            f, f_name = resolve_path(self.server, "folder", "with VMs")
            vms = [VM(vm=x) for x in f.childEntity if is_vm(x)]
            self._log.info("Found %d VMs in folder '%s'", len(vms), f_name)
            if prompt_for_confirmation("Show the status of the " "VMs in the folder? "):
                self._log.info(
                    "Folder structure: \n%s",
                    format_structure(f.enumerate(recursive=True, power_status=True)),
                )
            if not prompt_for_confirmation("Continue? ", default=True):
                self._log.info("User cancelled operation, exiting...")
                sys.exit(0)
        else:
            vms = [
                resolve_path(self.server, "vm", "to perform snapshot operations on")[0]
            ]

        # Perform the operations
        pbar = tqdm.tqdm(vms, total=len(vms), unit="VMs", desc="Taking snapshots")
        for vm in pbar:
            self._log.info("Performing operation '%s' on VM '%s'", op, vm.name)
            pbar.set_postfix_str(vm.name)
            if op == "create":
                vm.create_snapshot(
                    name=name, description=desc, memory=memory, quiesce=quiesce
                )
            elif op == "revert":
                vm.revert_to_snapshot(snapshot=name)
            elif op == "revert-current":
                vm.revert_to_current_snapshot()
            elif op == "remove":
                vm.remove_snapshot(snapshot=name, remove_children=children)
            elif op == "remove-all":
                vm.remove_all_snapshots()
            elif op == "get":
                self._log.info(vm.get_snapshot_info(name))
            elif op == "get-current":
                self._log.info(vm.get_snapshot_info())
            elif op == "get-all":
                self._log.info(vm.get_all_snapshots_info())
            elif op == "disk-usage":
                self._log.info(vm.snapshot_disk_usage())
            else:
                self._log.error("Unknown operation: %s", op)
            pbar.update()
        pbar.close()


VSPHERE_SCRIPTS = [CleanupVms, CloneVms, VmPower, VsphereInfo, VmSnapshot]
