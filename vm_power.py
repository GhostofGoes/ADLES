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
    vm_power.py [-v] [-f FILE]
    vm_power.py --version
    vm_power.py (-h | --help)

Options:
    -h, --help          Prints this page
    --version           Prints current version
    -f, --file FILE     Name of JSON file with server connection information
    -v, --verbose       Verbose output of whats going on

"""

from docopt import docopt
import logging

from automation.utils import prompt_y_n_question, setup_logging, make_vsphere, warning, user_input
from automation.vsphere.vm_utils import change_vm_state
from automation.vsphere.vsphere_utils import traverse_path

__version__ = "0.3.0"

args = docopt(__doc__, version=__version__, help=True)
setup_logging(filename='vm_power.log', console_level=logging.DEBUG if args["--verbose"] else logging.INFO)

server = make_vsphere(args["--file"])
warning()

operation = input("Enter the power operation you wish to perform [on | off | reset | suspend]: ")
attempt_guest = prompt_y_n_question("Use guest operations if available? ")

if prompt_y_n_question("Multiple VMs? "):
    folder, folder_name = user_input("Name of or path to the folder: ", "folder",
                                     lambda x: traverse_path(server.get_folder(), x)
                                     if '/' in x else server.get_folder(x))
    vms = [vm for vm in folder if hasattr(vm, "summary")]
    if prompt_y_n_question("Found %s VMs in folder %s. Continue? " % (len(vms), folder_name)):
        for vm in vms:
            change_vm_state(vm, operation, attempt_guest)

else:
    vm, vm_name = user_input("Name of or path to the VM: ", "VM",
                             lambda x: traverse_path(server.get_folder(), x) if '/' in x else server.get_vm(x))
    logging.info("Changing power state of VM %s to %s", vm_name, operation)
    change_vm_state(vm, operation, attempt_guest)