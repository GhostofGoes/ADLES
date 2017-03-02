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


def create_vswitch(name, host, num_ports=512):
    """
    Creates a vSwitch
    :param name: Name of the vSwitch to create
    :param host: vim.HostSystem to create the vSwitch on
    :param num_ports: Number of ports the vSwitch should have [default: 512]
    """
    logging.info("Creating vSwitch %s with %s ports on host %s", name, str(num_ports), host.name)
    vswitch_spec = vim.host.VirtualSwitch.Specification()
    vswitch_spec.numPorts = num_ports
    try:
        host.configManager.networkSystem.AddVirtualSwitch(name, vswitch_spec)
    except vim.fault.AlreadyExists:
        logging.error("vSwitch %s already exists on host %s", name, host.name)

# TODO: edit vswitch


def delete_vswitch(name, host):
    """
    Deletes the named vSwitch from the host
    :param name: Name of the vSwitch to delete
    :param host: vim.HostSystem to delete vSwitch from
    """
    logging.info("Deleting vSwitch %s from host %s", name, host.name)
    try:
        host.configManager.networkSystem.RemoveVirtualSwitch(name)
    except vim.fault.NotFound:
        logging.error("Tried to remove a vSwitch %s that does not exist from host %s", name, host.name)
    except vim.fault.ResourceInUse:
        logging.error("vSwitch %s can't be removed because there are virtual network adapters associated with it", name)


def create_portgroup(name, host, vswitch_name, vlan=0, promiscuous=False):
    """
    Creates a portgroup
    :param name: Name of portgroup to create
    :param host: vim.HostSystem on which to create the port group
    :param vswitch_name: Name of vSwitch on which to create the port group
    :param vlan: (Optional) VLAN ID of the port group [default: 0]
    :param promiscuous: (Optional) Sets the promiscuous mode of the switch, allowing for monitoring [default: False]
    """
    logging.info("Creating PortGroup %s on vSwitch %s on host %s", name, vswitch_name, host.name)
    logging.debug("VLAN ID: %s \t Promiscuous: %s", str(vlan), str(promiscuous))
    spec = vim.host.PortGroup.Specification()
    spec.name = name
    spec.vlanId = int(vlan)
    spec.vswitchName = vswitch_name
    policy = vim.host.NetworkPolicy()
    policy.security = vim.host.NetworkPolicy.SecurityPolicy()
    policy.security.allowPromiscuous = promiscuous
    policy.security.macChanges = False
    policy.security.forgedTransmits = False
    spec.policy = policy

    try:
        host.configManager.networkSystem.AddPortGroup(spec)
    except vim.fault.AlreadyExists:
        logging.error("PortGroup %s already exists on host %s", name, host.name)
    except vim.fault.NotFound:
        logging.error("vSwitch %s does not exist on host %s", str(vswitch_name), host.name)

# TODO: edit portgroup


def delete_portgroup(name, host):
    """
    Deletes a portgroup
    :param name: Name of the portgroup
    :param host: vim.HostSystem with the portgroup
    """
    logging.info("Deleting PortGroup %s from host %s", name, host.name)
    try:
        host.configManager.networkSystem.RemovePortGroup(name)
    except vim.fault.NotFound:
        logging.error("Tried to remove a portgroup %s that does not exist from host %s", name, host.name)
    except vim.fault.ResourceInUse:
        logging.error("PortGroup %s can't be removed because there are "
                      "virtual network adapters associated with it", name)


def get_net_item(host, object_type, name):
    """
    Retrieves a network object of the specified type and name from a host
    :param host: vim.HostSystem
    :param object_type: Type of object to get: (portgroup | vswitch | proxyswitch | vnic | pnic)
    :param name: (Optional) Name of network object [default: all objects of the type]
    :return: The network object
    """
    if name:
        return get_net_obj(host, object_type, name)
    else:
        return get_net_objs(host, object_type)[0]


def get_net_obj(host, object_type, name):
    """
    Retrieves a network object of the specified type and name from a host
    :param host: vim.HostSystem
    :param object_type: Type of object to get: (portgroup | vswitch | proxyswitch | vnic | pnic)
    :param name: Name of network object
    :return: The network object
    """
    for obj in get_net_objs(host=host, object_type=object_type):
        if obj.name == name:
            return obj
    return None


def get_net_objs(host, object_type):
    """
    Retrieves all network objects of the specified type from the host
    :param host: vim.HostSystem
    :param object_type: Type of object to get: (portgroup | vswitch | proxyswitch | vnic | pnic)
    :return: list of the network objects
    """
    host.configManager.networkSystem.RefreshNetworkSystem()  # Pick up any changes that might have occurred
    if object_type == "portgroup":
        objects = host.configManager.networkSystem.networkInfo.portgroup
    elif object_type == "vswitch":
        objects = host.configManager.networkSystem.networkInfo.vswitch
    elif object_type == "proxyswitch":
        objects = host.configManager.networkSystem.networkInfo.proxySwitch
    elif object_type == "vnic ":
        objects = host.configManager.networkSystem.networkInfo.vnic
    elif object_type == "pnic ":
        objects = host.configManager.networkSystem.networkInfo.pnic
    else:
        logging.error("Invalid type %s for get_net_obj", object_type)
        return None
    return objects
