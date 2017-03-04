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
    vsphere_info.py [-v] [-f FILE]
    vsphere_info.py --version
    vsphere_info.py (-h | --help)

Options:
    -h, --help          Prints this page
    --version           Prints current version
    -f, --file FILE     Name of JSON file with server connection information
    -v, --verbose       Verbose output of whats going on

"""

import logging

from docopt import docopt

from adles.vsphere import *
from adles.utils import script_setup

__version__ = "0.3.1"
args = docopt(__doc__, version=__version__, help=True)
server = script_setup('vsphere_info.log', args)

# List of possible useful things
#   open_console
#   upload_file
#   get_status    Status of the overall environment (what VMs are on/off/deploys, what phase, etc.)

thing_type = input("What type of thing do you want to get information on? (vm | datastore | vsphere) ")

if thing_type == "vm":
    vm = server.get_vm(input("What is the name of the VM you want to get information on? "))
    vm_utils.print_vm_info(vm, print_uuids=True)
elif thing_type == "datastore":
    ds = server.get_datastore(input("What is the name of the Datastore you want to get information on? "))
    vsphere_utils.print_datastore_info(ds)
elif thing_type == "vsphere":
    logging.info("%s", str(server.content.about))
else:
    logging.info("Invalid type: ", thing_type)
