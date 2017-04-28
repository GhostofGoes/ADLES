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
    vsphere_testing.py [-v] [options]
    vsphere_testing.py --version
    vsphere_testing.py (-h | --help)

Options:
    -h, --help          Shows this help
    --version           Prints current version
    --no-color          Do not color terminal output
    -v, --verbose       Emit debugging logs to terminal
    -f, --file FILE     Name of JSON file with server connection information

"""

from docopt import docopt

from adles.vsphere.vsphere_class import Vsphere
from adles.utils import script_setup

args = docopt(__doc__, version=Vsphere.__version__, help=True)
server = script_setup('vsphere_testing.log', args, (__file__, Vsphere.__version__))


# test = server.find_by_inv_path("vm/cgoes_testing/script_testing/monkeys/test-vm")
# print(test.get_info())
#
# test2 = server.find_by_inv_path("vm/cgoes_testing/script_testing/monkeys")
# print(test2)

# folder = server.get_folder("monkeys")
# folder.create("HAHAHAHhaHAHhaHA (hi)")
# print(folder.enumerate())

# from adles.vsphere.vm import VM
# folder = server.get_folder("monkeys")
# vm = server.get_vm("test-vm")
# service = VM(vm=vm)
# service = VM(name="test-vm", folder=folder, resource_pool=server.get_pool(),
#              datastore=server.get_datastore(), host=server.get_host())
# template = server.get_vm("dummy")
# service.create(template=template)
# service.change_state("on")
# print(service.screenshot())
# service.change_state("off")
# service.set_note("testing 1... 2... 3...")
# print(str(service))
# print(hash(service))
# print(service.get_info(True, True, True, True))
# service.upgrade(12)
# service.convert_template()
# service.destroy()

# from adles.vsphere.hosts import Host
# host = Host(server.get_host())
# print(str(host))
# print(hash(host))

# bios_uuid = "42053029-1098-6ef1-da79-5e2c4103f600"
# instance_uuid = "50056cfe-aaa0-c28d-a702-d72e68e50f3a"
# vm = server.find_by_uuid(uuid=instance_uuid)
# vm = server.find_by_ds_path(path="[Datastore] (MASTER) apache/(MASTER) apache.vmx")
# logging.info("%s", vm_utils.get_info(vm, uuids=True))

# net = server.get_network("ARP-LAN")
# logging.info(str(net))

# logging.info(str(server))
# logging.info(repr(server))

# datastore = server.get_datastore("Datastore")
# logging.info(get_datastore_info(datastore))

# portgroup = server.get_item(vim.Network, "test_network")
# logging.info("Portgroup: %s", str(portgroup))
# vm.add_nic(portgroup, "test_summary")
# vm.edit_nic(2, summary="lol")
# vm.remove_nic(2)
