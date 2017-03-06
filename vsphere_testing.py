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

"""vsphere_testing. Entrypoint used to test the vSphere class. Has examples of API usage.

Usage:
    vsphere_testing.py [-v] [-f FILE]
    vsphere_testing.py --version
    vsphere_testing.py (-h | --help)

Options:
    -h, --help          Shows this help
    --version           Prints current version
    -f, --file FILE     JSON file with server connection information
    -v, --verbose       Emits debugging logs to terminal in addition to a file

"""
import logging

from docopt import docopt

from adles.vsphere.vsphere_class import Vsphere
from adles.vsphere import vm_utils
from adles.utils import script_setup

args = docopt(__doc__, version=Vsphere.__version__, help=True)
server = script_setup('vsphere-testing.log', args, (__file__, Vsphere.__version__))

net = server.get_network("ARP-LAN")
logging.info(str(net))
# vm = server.get_vm("dummy")
# logging.info(vm_utils.get_vm_info(vm, uuids=True, snapshot=True))

# host = server.get_host()
# logging.info(host)

# logging.info((str(server))
# logging.info((repr(server))

# folder = server.get_folder("script_testing")
# vm = traverse_path(folder, "/Templates/Routers/VyOS 1.1.7 (64-bit)")
# logging.info((get_vm_info(vm))

# folder = traverse_path(folder, "/Templates/Servers/Windows")
# logging.info((folder.name)

# datastore = server.get_datastore("Datastore")
# logging.info((get_datastore_info(datastore))

# folder = server.get_folder("script_testing")
# pool = get_objs(server.content, [vim.ResourcePool])[0]
# file_info = vim.vm.FileInfo()
# file_info.vmPathName = "[Datastore]"
# vm_spec = vim.vm.ConfigSpec(name="test_vm", guestId="ubuntuGuest", numCPUs=1, numCoresPerSocket=1,
#                             memoryMB=1024, annotation="it worked!", files=file_info)
# create_vm(folder, vm_spec, pool)
# attach_iso(vm, "ISO-Images/vyos-1.1.7-amd64.iso", server.get_datastore("Datastore"))

# portgroup = get_obj(server.content, [vim.Network], "test_network")
# add_nic(vm, portgroup, "test_summary")
# edit_nic(vm, 2, summary="lol")
# delete_nic(vm, 1)

# create_portgroup("test_portgroup", server.get_host(), "test_vswitch")
# delete_portgroup("test_portgroup", server.get_host())
