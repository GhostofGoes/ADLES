#!/usr/bin/env python3
# -*- coding: utf-8 -*-


def create_vswitch(name, host, num_ports=1024):
    """
    Creates a vSwitch
    :param name: Name of the vSwitch to create
    :param host: vim.HostSystem to create the vSwitch on
    :param num_ports: Number of ports the vSwitch should have [default: 1024]
    """
    print("Creating vSwitch {} with {} ports on host {}".format(name, str(num_ports), host.name))
    vswitch_spec = vim.host.VirtualSwitch.Specification()
    vswitch_spec.numPorts = num_ports
    host.configManager.networkSystem.AddVirtualSwitch(name, vswitch_spec)


def delete_vswitch(name, host):
    """
    Deletes the named vSwitch from the host
    :param name: Name of the vSwitch to delete
    :param host: vim.HostSystem to delete vSwitch from
    """
    print("Deleting vSwitch {} from host {}".format(name, host.name))
    host.configManager.networkSystem.RemoveVirtualSwitch(name)
