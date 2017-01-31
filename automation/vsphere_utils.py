#!/usr/bin/env python3
# -*- coding: utf-8 -*-


def get_obj(content, vimtype, name):
    """
    Recursively finds and returns named object of specified type
    :param content:
    :param vimtype:
    :param name:
    :return:
    """
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
    return obj

# TODO: function to apply a given operation to all objects in a view


# From: getallvms.py in pyvmomi-community-samples
def print_vm_info(virtual_machine):
    """
    Print human-readable information for a virtual machine object
    :param virtual_machine:
    :return:
    """
    summary = virtual_machine.summary
    print("Name          : ", summary.config.name)
    print("Template      : ", summary.config.template)
    print("Path          : ", summary.config.vmPathName)
    print("Guest         : ", summary.config.guestFullName)
    print("Instance UUID : ", summary.config.instanceUuid)
    print("Bios UUID     : ", summary.config.uuid)
    print("State         : ", summary.runtime.powerState)
    if summary.guest:
        ip_address = summary.guest.ipAddress
        tools_version = summary.guest.toolsStatus
        print("VMware-tools  : ", tools_version)
        print("IP            : ", ip_address)
    if summary.runtime.question:
        print("Question  : ", summary.runtime.question.text)
    if summary.config.annotation:
        print("Annotation    : ", summary.config.annotation)
