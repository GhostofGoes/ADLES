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
from pprint import pprint

from automation.utils import prompt_y_n_question, setup_logging, make_vsphere, warning, user_input, default_prompt
from automation.vsphere.vm_utils import destroy_vm
from automation.vsphere.vsphere_utils import cleanup, enumerate_folder, traverse_path

__version__ = "0.3.0"

args = docopt(__doc__, version=__version__, help=True)
setup_logging(filename='destroy_vms.log', console_level=logging.DEBUG if args["--verbose"] else logging.INFO)

server = make_vsphere(args["--file"])
warning()

if prompt_y_n_question("Do you wish to destroy a single VM? "):
    # TODO: VM at path + folder at path utility func
    vm, vm_name = user_input("Name of or path to VM to destroy: ", "VM",
                             lambda x: traverse_path(server.get_folder(), x) if '/' in x else server.get_vm(x))
    if vm.config.template:  # Warn if template
        if not prompt_y_n_question("VM %s is a Template. Do you wish to continue? " % vm_name):
            exit(0)
    if prompt_y_n_question("Continue with destruction? "):
        logging.info("Destroying VM with name %s", vm_name)
        destroy_vm(vm)
    else:
        logging.info("Destruction cancelled")
else:
    folder, fname = user_input("Name of or path to folder to destroy: ", "folder",
                               lambda x: traverse_path(server.get_folder(), x) if '/' in x else server.get_folder(x))
    pprint(enumerate_folder(folder))  # Display folder structure

    prefix = default_prompt("What is the prefix of VMs you wish to destroy? Press Enter for none... ", default=None)
    recursive = prompt_y_n_question("Recursively descend into folders? ")
    destroy_folders = prompt_y_n_question("Destroy folders in addition to VMs? ")
    destroy_self = prompt_y_n_question("Destroy the folder itself? ")

    logging.info("Destruction options - Prefix: %s\tRecursive: %s\tFolder-destruction: %s\tSelf-destruction: %s",
                 fname, str(prefix), str(recursive), str(destroy_folders), str(destroy_self))
    if prompt_y_n_question("Continue with destruction? "):
        logging.info("Destroying...")
        cleanup(folder, prefix=prefix, recursive=recursive, destroy_folders=destroy_folders, destroy_self=destroy_self)
    else:
        logging.info("Destruction cancelled")
