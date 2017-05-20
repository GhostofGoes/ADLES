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

"""Power operations for Virtual Machines in vSphere.

Usage:
    vm-power [options]

Options:
    -h, --help          Prints this page
    --version           Prints current version
    -n, --no-color      Do not color terminal output
    -v, --verbose       Emit debugging logs to terminal
    -f, --file FILE     Name of JSON file with server connection information

Examples:
    vm-power -vf logins.json

"""

import logging

from docopt import docopt

from adles.utils import ask_question, script_setup, resolve_path, is_vm
from adles.vsphere.folder_utils import format_structure
from adles.vsphere.vm import VM

__version__ = "0.3.10"


def main():
    args = docopt(__doc__, version=__version__, help=True)
    server = script_setup('vm_power.log', args, (__file__, __version__))

    operation = str(input("Enter the power operation you wish to perform"
                          " [on | off | reset | suspend]: "))
    attempt_guest = ask_question("Attempt to use guest OS operations, "
                                 "if available? ")

    if ask_question("Multiple VMs? ", default="yes"):
        folder, folder_name = resolve_path(server, "folder", "with VMs")
        vms = [VM(vm=x) for x in folder.childEntity if is_vm(x)]
        logging.info("Found %d VMs in folder '%s'", len(vms), folder_name)
        if ask_question("Show the status of the VMs in the folder? "):
            logging.info("Folder structure: \n%s", format_structure(
                folder.enumerate(recursive=True, power_status=True)))
        if ask_question("Continue? ", default="yes"):
            for vm in vms:
                vm.change_state(operation, attempt_guest)

    else:
        vm = resolve_path(server, "VM")[0]
        logging.info("Changing power state of '%s' to '%s'", vm.name, operation)
        vm.change_state(operation, attempt_guest)


if __name__ == '__main__':
    main()
