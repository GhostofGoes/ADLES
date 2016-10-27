#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from logging import getLogger

logger = getLogger(__name__)


def clone_vm(vm, clone_name):
    pass


def create_vm_from_template():
    pass


def destroy_vm(vm):
    pass


def move_vm(vm, dest_folder):
    pass


def convert_vm_to_template(vm, template_name):
    pass


def change_vm_power_state(vm, power_state):
    """ Power on, Power off, ACPI shutdown, Reset """
    pass


def add_device_to_vm(vm, device_spec):
    pass


def remove_device_from_vm(vm, device):
    pass


def modify_device(vm, device_name):
    pass


def create_network(name, type):
    pass


def destroy_network(name, type):
    pass


def modify_network(name, type, modification):
    pass


def main():
    """ For testing of vSphere """
    from json import dump
    from os import pardir, path
    from pyVim.connect import SmartConnect, Disconnect
    from atexit import register

    with open(path.join(pardir, "logins.json"), "r") as login_file:
        logins = dump(fp=login_file)["vsphere"]

    server = SmartConnect(logins["host"], logins["port"], logins["user"], logins["password"])
    register(Disconnect, server)


if __name__ == '__main__':
    main()


