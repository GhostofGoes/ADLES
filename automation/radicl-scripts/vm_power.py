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
    vm_power.py
    vm_power.py -f FILE
    vm_power.py --version
    vm_power.py (-h | --help)

Options:
    -h, --help          Prints this page
    --version           Prints current version
    -f, --file FILE     Name of JSON file with server connection and login information

"""

from docopt import docopt

from ..automation.vsphere.vm_utils import change_power_state, change_guest_state, tools_status
from ..automation.utils import prompt_y_n_question
from .radicl_utils import make_vsphere, warning, user_input

__version__ = "0.1.4"

args = docopt(__doc__, version=__version__, help=True)
server = make_vsphere(args["--file"])
warning()

operation = input("Enter the power operation you wish to perform [on | off | reset | suspend]: ")
guest_check = prompt_y_n_question("Do you wish to use guest power operations if VMware Tools is installed? ")
guest_op = None
if guest_check:
    guest_op = input("What guest operation do you wish to be performed [shutdown | reboot | standby]: ")

if prompt_y_n_question("Do you wish to do power operations on multiple VMs? "):
    folder, folder_name = user_input("Name of folder which contains the VMs (NOT the path): ",
                                     "folder", server.get_folder)
    if prompt_y_n_question("Found {} VMs in folder {}. Do you wish to continue? "
                           .format(len(list(folder.childEntity)), folder_name)):
        for vm in folder.childEntity:
            if guest_check and tools_status(vm):
                change_guest_state(vm, guest_op)
            else:
                change_power_state(vm, operation)

else:
    vm, vm_name = user_input("Name of the VM to do power operation on: ", "VM", server.get_vm)
    print("Changing power state of VM {} to {}".format(vm_name, operation))
    change_power_state(vm, operation)
