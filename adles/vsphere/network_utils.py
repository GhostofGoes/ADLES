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

import logging

from pyVmomi import vim


def create_portgroup(name, host, vswitch_name, vlan=0, promiscuous=False):
    """
    Creates a portgroup
    :param name: Name of portgroup to create
    :param host: vim.HostSystem on which to create the port group
    :param vswitch_name: Name of vSwitch on which to create the port group
    :param vlan: VLAN ID of the port group [default: 0]
    :param promiscuous: Put portgroup in promiscuous mode [default: False]
    """
    logging.info("Creating PortGroup %s on vSwitch %s on host %s", name, vswitch_name, host.name)
    logging.debug("VLAN ID: %d \t Promiscuous: %s", vlan, promiscuous)

    spec = vim.host.PortGroup.Specification()
    spec.name = name
    spec.vlanId = int(vlan)
    spec.vswitchName = vswitch_name
    policy = vim.host.NetworkPolicy()
    policy.security = vim.host.NetworkPolicy.SecurityPolicy()
    policy.security.allowPromiscuous = bool(promiscuous)
    policy.security.macChanges = False
    policy.security.forgedTransmits = False
    spec.policy = policy

    try:
        host.configManager.networkSystem.AddPortGroup(spec)
    except vim.fault.AlreadyExists:
        logging.error("PortGroup %s already exists on host %s", name, host.name)
    except vim.fault.NotFound:
        logging.error("vSwitch %s does not exist on host %s", vswitch_name, host.name)
