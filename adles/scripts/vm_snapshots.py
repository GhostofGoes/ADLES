#!/usr/bin/env python3
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

"""Perform Snapshot operations on Virtual Machines in a vSphere environment.

Usage:
    vm-snapshots [options]

Options:
    -h, --help          Prints this page
    --version           Prints current version
    -n, --no-color      Do not color terminal output
    -v, --verbose       Emit debugging logs to terminal
    -f, --file FILE     Name of JSON file with server connection information

Examples:
    vm-snapshots -vf logins.json

"""

import logging

import tqdm

from adles.utils import script_setup, get_args, \
    ask_question, resolve_path, is_vm
from adles.vsphere.folder_utils import format_structure
from adles.vsphere.vm import VM

__version__ = "0.3.0"


# noinspection PyUnboundLocalVariable
def main():
    args = get_args(__doc__, __version__, 'vm_snapshots.log')
    server = script_setup(args=args, script_info=(__file__, __version__))

    op = str(input("Enter Snapshot operation [create | revert | revert-current "
                   "| remove | remove-all | get | "
                   "get-current | get-all | disk-usage]: "))
    if op == "create" or op == "revert" or op == "remove" or op == "get":
        name = str(input("Name of snapshot to %s: " % op))
        if op == "create":
            desc = str(input("Description of snapshot to create: "))
            memory = ask_question("Include memory?")
            quiesce = ask_question("Quiesce disks? (Requires VMware Tools "
                                   "to be running on the VM)")
        elif op == "remove":
            children = ask_question("Remove any children of the snapshot?",
                                    default="yes")

    if ask_question("Multiple VMs? ", default="yes"):
        f, f_name = resolve_path(server, "folder", "with VMs")
        vms = [VM(vm=x) for x in f.childEntity if is_vm(x)]
        logging.info("Found %d VMs in folder '%s'", len(vms), f_name)
        if ask_question("Show the status of the VMs in the folder? "):
            logging.info("Folder structure: \n%s", format_structure(
                f.enumerate(recursive=True, power_status=True)))
        if not ask_question("Continue? ", default="yes"):
            logging.info("User cancelled operation, exiting...")
            exit(0)
    else:
        vms = [resolve_path(server, "vm",
                            "to perform snapshot operations on")[0]]

    # Perform the operations
    pbar = tqdm.tqdm(vms, total=len(vms), desc="Taking snapshots", unit="VMs")
    for vm in pbar:
        logging.info("Performing operation '%s' on VM '%s'", op, vm.name)
        pbar.set_postfix_str(vm.name)
        if op == "create":
            vm.create_snapshot(name=name, description=desc,
                               memory=memory, quiesce=quiesce)
        elif op == "revert":
            vm.revert_to_snapshot(snapshot=name)
        elif op == "revert-current":
            vm.revert_to_current_snapshot()
        elif op == "remove":
            vm.remove_snapshot(snapshot=name, remove_children=children)
        elif op == "remove-all":
            vm.remove_all_snapshots()
        elif op == "get":
            logging.info(vm.get_snapshot_info(name))
        elif op == "get-current":
            logging.info(vm.get_snapshot_info())
        elif op == "get-all":
            logging.info(vm.get_all_snapshots_info())
        elif op == "disk-usage":
            logging.info(vm.snapshot_disk_usage())
        else:
            logging.error("Unknown operation: %s", op)
        pbar.update()
    pbar.close()


if __name__ == '__main__':
    main()
