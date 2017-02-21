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

"""Destroy VMs and Folders in a vSphere environment.

Usage:
    destroy_vms.py [-v] [-f FILE]
    destroy_vms.py --version
    destroy_vms.py (-h | --help)

Options:
    -h, --help          Prints this page
    --version           Prints current version
    -f, --file FILE     Name of JSON file with server connection information
    -v, --verbose       Verbose output of whats going on

"""

from docopt import docopt
import logging

from automation.utils import prompt_y_n_question, setup_logging, make_vsphere, warning, user_input
from automation.vsphere.vm_utils import destroy_vm
from automation.vsphere.vsphere_utils import cleanup

__version__ = "0.2.0"

args = docopt(__doc__, version=__version__, help=True)
setup_logging(filename='destroy_vms.log', console_level=logging.DEBUG if args["--verbose"] else logging.INFO)

server = make_vsphere(args["--file"])
warning()

if prompt_y_n_question("Do you wish to destroy a single VM? "):
    vm, vm_name = user_input("Name of VM to destroy: ", "VM", server.get_vm)
    logging.info("Destroying VM with name %s", vm_name)
    destroy_vm(vm)
else:
    folder, folder_name = user_input("Name of folder to destroy: ", "folder", server.get_folder)
    if prompt_y_n_question("Do you wish to destroy VMs with a specific prefix? "):
        prefix = input("Enter the prefix: ")
    else:
        prefix = None
    if prompt_y_n_question("Do you wish to recursively descend the folder tree? "):
        recursive = True
    else:
        recursive = False

    if prompt_y_n_question("Do you wish to destroy folders in addition to VMs? "):
        destroy_folders = True
    else:
        destroy_folders = False

    if prompt_y_n_question("Do you wish to destroy the folder itself? "):
        destroy_self = True
    else:
        destroy_self = False

    logging.info("Carrying out destruction of folder %s with following arguments: "
                 "Prefix: %s\tRecursive: %s\tFolder-destruction: %s\tSelf-destruction: %s",
                 folder_name, str(prefix), str(recursive), str(destroy_folders), str(destroy_self))

    cleanup(folder, prefix=prefix, recursive=recursive, destroy_folders=destroy_folders, destroy_self=destroy_self)
