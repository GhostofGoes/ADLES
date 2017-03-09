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
    destroy_vms.py [options]
    destroy_vms.py --version
    destroy_vms.py (-h | --help)

Options:
    -h, --help          Prints this page
    --version           Prints current version
    --no-color          Do not color termianl output
    -v, --verbose       Emit debugging logs to terminal
    -f, --file FILE     Name of JSON file with server connection information

"""

import logging

from docopt import docopt

from adles.utils import prompt_y_n_question, user_input, default_prompt, script_setup
import adles.vsphere.vm_utils as vm_utils
from adles.vsphere.folder_utils import traverse_path, enumerate_folder, format_structure, cleanup, retrieve_items

__version__ = "0.4.0"
args = docopt(__doc__, version=__version__, help=True)
server = script_setup('destroy_vms.log', args, (__file__, __version__))

if prompt_y_n_question("Do you wish to destroy a single VM? "):
    # TODO: VM at path + folder at path utility func
    vm, vm_name = user_input("Name of or path to VM to destroy: ", "VM",
                             lambda x: traverse_path(server.get_folder(), x) if '/' in x else server.get_vm(x))
    if vm.config.template:  # Warn if template
        if not prompt_y_n_question("VM %s is a Template. Do you wish to continue? " % vm_name):
            exit(0)
    if prompt_y_n_question("Continue with destruction? "):
        logging.info("Destroying VM with name %s", vm_name)
        vm_utils.destroy_vm(vm)
    else:
        logging.info("Destruction cancelled")
else:
    folder, fname = user_input("Name of or path to the folder that has the VMs/folders you want to destroy: ", "folder",
                               lambda x: traverse_path(server.get_folder(), x) if '/' in x else server.get_folder(x))

    # Display folder structure
    logging.info("Folder structure: %s", format_structure(enumerate_folder(folder)))

    vm_prefix = default_prompt("Prefix of VMs you wish to destroy (CASE SENSITIVE!)", default=None)
    recursive = prompt_y_n_question("Recursively descend into folders? ")
    destroy_folders = prompt_y_n_question("Destroy folders in addition to VMs? ")
    folder_prefix = None
    if destroy_folders:
        folder_prefix = default_prompt("Prefix of folders you wish to destroy (CASE SENSITIVE!)", default=None)
    destroy_self = prompt_y_n_question("Destroy the folder itself? ")

    logging.info("VM Prefix: '%s'\tFolder Prefix: '%s'\tRecursive: %s",
                 str(vm_prefix), str(folder_prefix), str(recursive))
    logging.info("Folder-destruction: %s\tSelf-destruction: %s", str(destroy_folders), str(destroy_self))
    v, f = retrieve_items(folder, vm_prefix, True)
    logging.info("%d VMs and %d folders match the options", int(len(v)), int(len(f)))
    if prompt_y_n_question("Continue with destruction? "):
        logging.info("Destroying...")
        cleanup(folder, vm_prefix=vm_prefix, folder_prefix=folder_prefix, recursive=recursive,
                destroy_folders=destroy_folders, destroy_self=destroy_self)
    else:
        logging.info("Destruction cancelled")
