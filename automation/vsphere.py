#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from atexit import register

from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim


class vSphere:
    def __init__(self, user, password, host, port=443):
        self._log = logging.getLogger(__name__)
        if not password:
            from getpass import getpass
            password = getpass(prompt='Enter password for host %s and user %s: ' % (host, user))
        self.server = SmartConnect(host=host, user=user, pwd=password, port=int(port))
        if not self.server:
            print("Could not connect to the specified host using specified username and password")
            raise Exception()
        register(Disconnect, self.server)

    # From: create_folder_in_datacenter.py in pyvmomi-community-samples
    def create_folder(self, folder, datacenter):
        """ Creates a VM folder in a datacenter """
        content = self.server.RetrieveContent()
        dc = get_obj(content, [vim.Datacenter], datacenter)
        if get_obj(content, [vim.Folder], folder):
            self._log.warning("Folder '%s' already exists" % folder)
        else:
            dc.vmFolder.CreateFolder(folder)

    def convert_vm_to_template(self, vm, template_name):
        pass

    def change_vm_power_state(self, vm, power_state):
        """ Power on, Power off, ACPI shutdown, Reset """
        pass


# Helper functions
# TODO: doctest
def get_obj(content, vimtype, name):
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
    return obj


def main():
    """ For testing of vSphere """
    from json import dump
    from os import pardir, path
    # from pyVim.connect import SmartConnect, Disconnect
    # from atexit import register

    logging.basicConfig(filename='vsphere_testing.log', filemode='w', level=logging.DEBUG)

    with open(path.join(pardir, "logins.json"), "r") as login_file:
        logins = dump(fp=login_file)["vsphere"]

    server = vSphere(logins["user"], logins["pass"], logins["host"], logins["port"])
    # server = SmartConnect(logins["host"], logins["port"], logins["user"], logins["pass"])
    # register(Disconnect, server)


if __name__ == '__main__':
    main()


