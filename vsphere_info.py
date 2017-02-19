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
    vsphere_info.py
    vsphere_info.py -f FILE
    vsphere_info.py --version
    vsphere_info.py (-h | --help)

Options:
    -h, --help          Prints this page
    --version           Prints current version
    -f, --file FILE     Name of JSON file with server connection and login information

"""

from docopt import docopt

from automation.radicl_utils import make_vsphere, warning
from automation.vsphere.vm_utils import print_vm_info
from automation.vsphere.vsphere_utils import print_datastore_info

__version__ = "0.1.0"

args = docopt(__doc__, version=__version__, help=True)
server = make_vsphere(args["--file"])
warning()

# List of possible useful things
#   open_console
#   upload_file
#   get_status    Status of the overall environment (what VMs are on/off/deploys, what phase, etc.)

thing_type = input("What type of thing do you want to get information on? (vm | datastore ) ")
thing_name = input("What is the name of the thing you want to get information on? ")
if thing_type == "vm":
    vm = server.get_vm(thing_name)
    print_vm_info(vm, print_uuids=True)
elif thing_type == "datastore":
    ds = server.get_datastore(thing_name)
    print_datastore_info(ds)
else:
    print("Invalid type: ", thing_type)
