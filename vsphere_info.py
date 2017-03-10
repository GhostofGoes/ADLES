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
from adles.utils import script_setup, user_input
from adles.vsphere.folder_utils import traverse_path, enumerate_folder, format_structure


__version__ = "0.4.1"
args = docopt(__doc__, version=__version__, help=True)
server = script_setup('vsphere_info.log', args, (__file__, __version__))

# List of possible useful things
#   open_console
#   upload_file
#   get_status    Status of the overall environment (what VMs are on/off/deploys, what phase, etc.)

thing_type = str(input("What type of thing do you want to get information on? (vm | datastore | vsphere | folder) "))

if thing_type == "vm":
    vm = server.get_vm(str(input("What is the name of the VM you want to get information on? ")))
    logging.info(vm_utils.get_vm_info(vm, uuids=True, snapshot=True))

elif thing_type == "datastore":
    ds = server.get_datastore(str(input("What is the name of the Datastore you want to get information on? ")))
    logging.info(vsphere_utils.get_datastore_info(ds))

elif thing_type == "vsphere":
    logging.info("%s", str(server))

elif thing_type == "folder":
    folder, folder_name = user_input("Name of or path to the folder: ", "folder",
                                lambda x: traverse_path(server.get_folder(), x) if '/' in x else server.get_folder(x))
    logging.info("Folder: %s\n%s", folder_name, format_structure(enumerate_folder(folder)))

else:
    logging.info("Invalid type: %s", thing_type)
