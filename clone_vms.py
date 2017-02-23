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

"""Clone multiple Virtual Machines in vSphere.

Usage:
    clone_vms.py [-v] [-f FILE]
    clone_vms.py --version
    clone_vms.py (-h | --help)

Options:
    -h, --help          Prints this page
    --version           Prints current version
    -f, --file FILE     Name of JSON file with server connection information
    -v, --verbose       Verbose output of whats going on

"""

from docopt import docopt
import logging

from automation.utils import prompt_y_n_question, setup_logging, make_vsphere, warning, user_input, pad, default_prompt
from automation.vsphere.vm_utils import clone_vm
from automation.vsphere.vsphere_utils import traverse_path

__version__ = "0.4.0"

args = docopt(__doc__, version=__version__, help=True)
setup_logging(filename='clone_vms.log', console_level=logging.DEBUG if args["--verbose"] else logging.INFO)

server = make_vsphere(args["--file"])
warning()

vm, vm_name = user_input("Name of or path to the VM or template you wish to clone: ", "VM",
                         lambda x: traverse_path(server.get_folder(), x) if '/' in x else server.get_vm(x))

if not vm.config.template:  # check type
    if not prompt_y_n_question("VM %s is not a Template. Do you wish to continue? " % vm_name):
        exit(0)

folder, folder_name = user_input("Name of or path to the folder in which to create VMs: ", "folder",
                                 lambda x: traverse_path(server.get_folder(), x) if '/' in x else server.get_folder(x))

base_name = input("Base name for instances to be created: ")
num_instances = int(input("Number of instances to be created: "))
# TODO: specify a group of VMs to put into a instance folder, then number of folder group instances

pool = server.get_pool().name
pool = default_prompt(prompt="Resource pool to assign VMs to", default=pool)

logging.info("Cloning %d VMs with a base name of %s", num_instances, base_name)
for instance in range(num_instances):
    name = base_name + pad(value=instance, length=2)    # Ensure zeros are being prepended
    spec = server.generate_clone_spec(pool_name=pool)   # Generate clone specification
    logging.info("Cloning %s...", name)
    clone_vm(vm, folder, name, spec)                    # Clone the VM using the generated spec
