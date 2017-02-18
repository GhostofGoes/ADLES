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
    destroy_vms.py
    destroy_vms.py -f FILE
    destroy_vms.py -f FILE --folder FOLDER
    destroy_vms.py --version
    destroy_vms.py (-h | --help)

Options:
    -h, --help          Prints this page
    --version           Prints current version
    -f, --file FILE     Name of JSON file with server connection and login information
    --folder FOLDER     Name of a folder to recursively destroy

"""

from docopt import docopt

from automation.vsphere.vsphere_utils import *
from automation.vsphere.vm_utils import *
from automation.utils import prompt_y_n_question
from .radicl_utils import make_vsphere, warning

__version__ = "0.1.3"

args = docopt(__doc__, version=__version__, help=True)
server = make_vsphere(args["--file"])
warning()

if prompt_y_n_question("Do you wish to destroy a folder and it's sub-trees? "):
    while True:
        folder_name = input("Name of folder to destroy: ")
        folder = server.get_folder(folder_name=folder_name)  # find folder
        if folder:
            break
        else:
            print("Couldn't find a folder with name {}. Perhaps try another? ".format(folder_name))

    print("Recursively destroying folder {}".format(folder.name))
    destroy_everything(folder)

elif prompt_y_n_question("Do you wish to destroy all VMs in a folder? "):
    while True:
        folder_name = input("Name of folder: ")
        folder = server.get_folder(folder_name=folder_name)  # find folder
        if folder:
            break
        else:
            print("Couldn't find a folder with name {}. Perhaps try another? ".format(folder_name))

    print("Destroying all VMs in folder {}".format(folder_name))
    for vm in folder.childEntity:
        destroy_vm(vm)

else:
    while True:
        vm_name = input("Name of VM to destroy: ")
        vm = server.get_vm(vm_name=vm_name)  # find folder
        if vm:
            break
        else:
            print("Couldn't find a VM with name {}. Perhaps try another? ".format(vm_name))

    print("Destroying VM with name {}".format(vm_name))
    destroy_vm(vm)
