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

"""Cleanup and Destroy Virtual Machines (VMs) and VM Folders in a vSphere environment.

Usage:
    cleanup-vms [options]

Options:
    -h, --help          Prints this page
    --version           Prints current version
    -n, --no-color      Do not color terminal output
    -v, --verbose       Emit debugging logs to terminal
    -f, --file FILE     Name of JSON file with server connection information

Examples:
    cleanup-vms -vf logins.json

"""

import logging

from docopt import docopt

from adles.utils import ask_question, default_prompt, script_setup, resolve_path
from adles.vsphere.folder_utils import format_structure

__version__ = "0.5.11"


def main():
    args = docopt(__doc__, version=__version__, help=True)
    server = script_setup('cleanup_vms.log', args, (__file__, __version__))

    if ask_question("Multiple VMs? ", default="yes"):
        folder, folder_name = resolve_path(server, "folder",
                                           "that has the VMs/folders "
                                           "you want to destroy")

        # Display folder structure
        if ask_question("Display the folder structure? "):
            logging.info("Folder structure: \n%s", format_structure(
                folder.enumerate(recursive=True, power_status=True)))

        # Prompt user to configure destruction options
        print("Answer the following questions to configure the cleanup")
        if ask_question("Destroy everything in and including the folder? "):
            vm_prefix = ''
            folder_prefix = ''
            recursive = True
            destroy_folders = True
            destroy_self = True
        else:
            vm_prefix = default_prompt("Prefix of VMs you wish to destroy"
                                       " (CASE SENSITIVE!)", default='')
            recursive = ask_question("Recursively descend into folders? ")
            destroy_folders = ask_question("Destroy folders "
                                           "in addition to VMs? ")
            if destroy_folders:
                folder_prefix = default_prompt("Prefix of folders "
                                               "you wish to destroy"
                                               " (CASE SENSITIVE!)", default='')
                destroy_self = ask_question("Destroy the folder itself? ")
            else:
                folder_prefix = ''
                destroy_self = False

        # Show user what options they selected
        logging.info("Options selected\nVM Prefix: %s\n"
                     "Folder Prefix: %s\nRecursive: %s\n"
                     "Folder-destruction: %s\nSelf-destruction: %s",
                     str(vm_prefix), str(folder_prefix), recursive,
                     destroy_folders, destroy_self)

        # Show how many items matched the options
        v, f = folder.retrieve_items(vm_prefix, folder_prefix, recursive=True)
        num_vms = len(v)
        if destroy_folders:
            num_folders = len(f)
            if destroy_self:
                num_folders += 1
        else:
            num_folders = 0
        logging.info("%d VMs and %d folders match the options",
                     num_vms, num_folders)

        # Confirm and destroy
        if ask_question("Continue with destruction? "):
            logging.info("Destroying folder '%s'...", folder_name)
            folder.cleanup(vm_prefix=vm_prefix,
                           folder_prefix=folder_prefix,
                           recursive=recursive,
                           destroy_folders=destroy_folders,
                           destroy_self=destroy_self)
        else:
            logging.info("Destruction cancelled")
    else:
        vm = resolve_path(server, "vm", "to destroy")[0]

        if ask_question("Display VM info? "):
            logging.info(vm.get_info(detailed=True, uuids=True,
                                     snapshot=True, vnics=True))

        if vm.is_template():  # Warn if template
            if not ask_question("VM '%s' is a Template. Continue? " % vm.name):
                exit(0)

        if ask_question("Continue with destruction? "):
            logging.info("Destroying VM '%s'", vm.name)
            vm.destroy()
        else:
            logging.info("Destruction cancelled")

if __name__ == '__main__':
    main()
