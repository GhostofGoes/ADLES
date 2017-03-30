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

"""Query information about a vSphere environment and objects within it.

Usage:
    vsphere_info.py [options]
    vsphere_info.py --version
    vsphere_info.py (-h | --help)

Options:
    -h, --help          Prints this page
    --version           Prints current version
    --no-color          Do not color terminal output
    -v, --verbose       Emit debugging logs to terminal
    -f, --file FILE     Name of JSON file with server connection information

"""

import logging

from docopt import docopt

from adles.vsphere import vm_utils, vsphere_utils
from adles.utils import script_setup, resolve_path, prompt_y_n_question
from adles.vsphere.folder_utils import enumerate_folder, format_structure

__version__ = "0.5.1"


def main():
    args = docopt(__doc__, version=__version__, help=True)
    server = script_setup('vsphere_info.log', args, (__file__, __version__))

    thing_type = str(input("What type of thing do you want to get information on?"
                           " (vm | datastore | vsphere | folder) "))

    # Single Virtual Machine
    if thing_type == "vm":
        vm, vm_name = resolve_path(server, "vm", "you want to get information on")
        logging.info(vm_utils.get_vm_info(vm, detailed=True, uuids=True, snapshot=True, vnics=True))

    # Datastore
    elif thing_type == "datastore":
        ds = server.get_datastore(str(input("Enter name of the Datastore [leave blank "
                                            "for first datastore found]: ")))
        logging.info(vsphere_utils.get_datastore_info(ds))

    # vCenter server
    elif thing_type == "vsphere":
        logging.info("%s", str(server))

    # VM Folder
    elif thing_type == "folder":
        folder, folder_name = resolve_path(server, "folder")
        if prompt_y_n_question("Want to see power state of VMs in the folder?"):
            contents = enumerate_folder(folder, recursive=True, power_status=True)
        else:
            contents = enumerate_folder(folder, recursive=True, power_status=False)
        logging.info("Contents of Folder %s\n%s", folder_name, format_structure(contents))

    # That's not a thing!
    else:
        logging.info("Invalid thing: %s", thing_type)


if __name__ == '__main__':
    main()
