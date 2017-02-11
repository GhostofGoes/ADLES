#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Power operations for Virtual Machines in vSphere.

Usage:
    vm_power.py
    vm_power.py -f FILE
    vm_power.py --version
    vm_power.py (-h | --help)

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


operation = input("Enter the power operation you wish to perform [on | off | reset | suspend]: ")
guest_check = prompt_y_n_question("Do you wish to use guest power operations if VMware Tools is installed? ")
guest_op = None
if guest_check:
    guest_op = input("What guest operation do you wish to be performed [shutdown | reboot | standby]: ")

if prompt_y_n_question("Do you wish to do power operations on multiple VMs? "):
    while True:
        folder_name = input("Name of folder which contains the VMs (NOT the path): ")
        folder = server.get_folder(folder_name=folder_name)  # find folder
        if folder:
            break
        else:
            print("Couldn't find a folder with name {}. Perhaps try another? ".format(folder_name))

    if prompt_y_n_question("Found {} VMs in folder {}. Do you wish to continue? ".format(len(list(folder.childEntity)),
                                                                                         folder_name)):
        for vm in folder.childEntity:
            if guest_check and tools_status(vm):
                change_guest_state(vm, guest_op)
            else:
                change_power_state(vm, operation)


else:
    while True:
        vm_name = input("Name of the VM to do power operation on: ")
        vm = server.get_vm(vm_name=vm_name)  # find vm
        if vm:
            break
        else:
            print("Couldn't find a VM with name {}. Perhaps try another? ".format(vm_name))

    print("Changing power state of VM {} to {}".format(vm_name, operation))
    change_power_state(vm, operation)
