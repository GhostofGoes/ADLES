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


def get_net_item(host, object_type, name):
    """
    Retrieves a network object of the specified type and name from a host
    :param host: vim.HostSystem
    :param object_type: Type of object to get: (portgroup | vswitch | proxyswitch | vnic | pnic)
    :param name: Name of network object [default: first object found]
    :return: The network object
    """
    if name:
        return get_net_obj(host, object_type, name)
    else:
        return get_net_objs(host, object_type)[0]


def get_net_obj(host, object_type, name, refresh=False):
    """
    Retrieves a network object of the specified type and name from a host
    :param host: vim.HostSystem
    :param object_type: Type of object to get: (portgroup | vswitch | proxyswitch | vnic | pnic)
    :param name: Name of network object
    :param refresh: Refresh the host's network system information [default: False]
    :return: The network object
    """
    objs = get_net_objs(host=host, object_type=object_type, refresh=refresh)
    obj_name = name.lower()
    if objs is not None:
        for obj in objs:
            if object_type == "portgroup" or object_type == "proxyswitch":
                if obj.spec.name.lower() == obj_name:
                    return obj
            elif object_type == "pnic" or object_type == "vnic":
                if obj.device.lower() == obj_name:
                    return obj
            elif obj.name.lower() == obj_name:
                return obj
    return None


def get_net_objs(host, object_type, refresh=False):
    """
    Retrieves all network objects of the specified type from the host
    :param host: vim.HostSystem
    :param object_type: Type of object to get: (portgroup | vswitch | proxyswitch | vnic | pnic)
    :param refresh: Refresh the host's network system information [default: False]
    :return: list of the network objects
    """
    if refresh:
        host.configManager.networkSystem.RefreshNetworkSystem()  # Pick up any recent changes

    net_type = object_type.lower()
    if net_type == "portgroup":
        objects = host.configManager.networkSystem.networkInfo.portgroup
    elif net_type == "vswitch":
        objects = host.configManager.networkSystem.networkInfo.vswitch
    elif net_type == "proxyswitch":
        objects = host.configManager.networkSystem.networkInfo.proxySwitch
    elif net_type == "vnic ":
        objects = host.configManager.networkSystem.networkInfo.vnic
    elif net_type == "pnic ":
        objects = host.configManager.networkSystem.networkInfo.pnic
    else:
        logging.error("Invalid type %s for get_net_objs", object_type)
        return None
    return list(objects)


def create_vswitch(name, host, num_ports=512):
    """
    Creates a vSwitch
    :param name: Name of the vSwitch to create
    :param host: vim.HostSystem to create the vSwitch on
    :param num_ports: Number of ports the vSwitch should have [default: 512]
    """
    logging.info("Creating vSwitch %s with %d ports on host %s", name, num_ports, host.name)

    vswitch_spec = vim.host.VirtualSwitch.Specification()
    vswitch_spec.numPorts = int(num_ports)

    try:
        host.configManager.networkSystem.AddVirtualSwitch(name, vswitch_spec)
    except vim.fault.AlreadyExists:
        logging.error("vSwitch %s already exists on host %s", name, host.name)


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


def delete_network(name, host, network_type):
    """
    Deletes the named network from the host
    :param name: Name of the vSwitch to delete
    :param host: vim.HostSystem to delete network from
    :param network_type: Type of the network to remove ("vswitch" | "portgroup")
    """
    logging.info("Deleting %s '%s' from host '%s'", network_type, name, host.name)
    try:
        if network_type.lower() == "vswitch":
            host.configManager.networkSystem.RemoveVirtualSwitch(name)
        elif network_type.lower() == "portgroup":
            host.configManager.networkSystem.RemovePortGroup(name)
    except vim.fault.NotFound:
        logging.error("Tried to remove %s '%s' that does not exist from host '%s'",
                      network_type, name, host.name)
    except vim.fault.ResourceInUse:
        logging.error("%s '%s' can't be removed because there are vNICs associated with it",
                      network_type, name)
