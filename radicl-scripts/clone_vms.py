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
    clone_vms.py
    clone_vms.py -f FILE
    clone_vms.py --version
    clone_vms.py (-h | --help)

Options:
    -h, --help          Prints this page
    --version           Prints current version
    -f, --file FILE     Name of JSON file with server connection and login information

"""

from docopt import docopt

from automation.vsphere.vsphere import vSphere
from automation.vsphere.vsphere_utils import traverse_path
from automation.vsphere.vm_utils import *
from automation.utils import prompt_y_n_question, read_json

__version__ = "0.2.1"

args = docopt(__doc__, version=__version__, help=True)

server = None  # Suppress warnings (sigh)
if args["--file"]:
    info = read_json(args["--file"])
    server = vSphere(datacenter=info["datacenter"], username=info["username"], password=info["password"],
                     hostname=info["hostname"], port=info["port"], datastore=info["datastore"])
else:
    from getpass import getpass
    print("Enter information to connect to vSphere environment")
    host = input("Hostname: ")
    port = int(input("Port: "))
    user = input("Username: ")
    pswd = getpass("Password: ")
    datacenter = input("vSphere Datacenter (should be one level below the vCenter server instance "
                       "in the VMs and Templates view): ")
    if prompt_y_n_question("Would you like to specify the datastore used "):
        datastore = input("vSphere Datastore: ")
        server = vSphere(datacenter=datacenter, username=user, password=pswd,
                         hostname=host, port=port, datastore=datastore)
    else:
        server = vSphere(datacenter=datacenter, username=user, password=pswd, hostname=host, port=port)

print("You run this script at your own risk. If you break something, it's on YOU. "
      "\nThe source code for the script is easily readable, so if you're paranoid feel free to check/improve it :)")

# this is the ugliest python i hath ever wroten since me early dayz as a nofice
# Well, it isn't anymore. But the comment was funny so I'm leaving it in for you, the GitHub stalker
while True:
    vm_name = input("Name of the VM or template you wish to clone: ")
    vm = server.get_vm(vm_name=vm_name)  # find vm
    if vm:
        break
    else:
        print("Couldn't find a VM with name {}. Perhaps try another? ".format(vm_name))

if not vm.config.template:  # check type
    if not prompt_y_n_question("VM {} is not a Template. Do you wish to continue? ".format(vm_name)):
        exit(0)

while True:
    folder_name = input("Name of folder or path to folder in which to create VMs: ")
    if '/' in folder_name:
        folder = traverse_path(server.get_folder(), folder_name)
    else:
        folder = server.get_folder(folder_name=folder_name)
    if folder:
        print("Found folder {}".format(folder.name))
        break
    else:
        print("Couldn't find a folder with name {}. Perhaps try another? ".format(folder_name))

base_name = input("Base name for instances to be created: ")
num_instances = int(input("Number of instances to be created: "))
pool = None

if prompt_y_n_question("Would you like to assign the new VMs to a specific resource pool? "):
    pool = input("Resource pool: ")
else:
    pool = server.get_pool().name
    print("Proceeding with default pool {}".format(pool))


print("Starting clones...")
for lol in range(num_instances):
    name = base_name + ' ' + str(lol)
    print("Cloning {}...".format(name))
    spec = server.generate_clone_spec(pool_name=pool)
    clone_vm(vm, folder, name, spec)
