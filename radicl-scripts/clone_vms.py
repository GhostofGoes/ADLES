#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

from vsphere import vSphere
from vm_utils import *
from utils import *

__version__ = "0.1.0"

args = docopt(__doc__, version=__version__, help=True)

# TODO: use six to allow python 2.7 to be used?
server = None  # Suppress warnings (sigh)
if args["--file"]:
    from json import load

    with open(args["--file"], "r") as login_file:
        info = load(fp=login_file)

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
    folder_name = input("Name of folder in which to create VMs (NOT the path!): ")
    folder = server.get_folder(folder_name=folder_name)  # find folder
    if folder:
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


# GO BABY GO
print("Starting clones...")
for lol in range(num_instances):
    name = base_name + ' ' + str(lol)
    print("Cloning {}...".format(name))
    spec = server.generate_clone_spec(pool_name=pool)
    clone_vm(vm, folder, name, spec)
