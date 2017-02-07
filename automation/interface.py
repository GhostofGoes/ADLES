#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging


class Interface:
    def __init__(self, infrastructure, logins):
        # Select an API to use
        if infrastructure["platform"] is "vmware vsphere":
            self.platform = infrastructure["platform"]
            from automation.vsphere.vsphere import vSphere
            self.api = vSphere(datacenter=infrastructure["datacenter"],
                               username=logins["user"],
                               password=logins["pass"],
                               hostname=logins["host"],
                               port=int(logins["port"]),
                               datastore=infrastructure["datastore"])
        else:
            logging.error("Invalid platform {}".format(infrastructure["platform"]))
            exit(1)

    def create_masters(self):
        if self.platform is "vmware vsphere":
            self._vsphere_create_masters()

    def deploy_environment(self):
        if self.platform is "vmware vsphere":
            self._vsphere_deploy_environment()

    def _vsphere_create_masters(self):
        pass

    def _vsphere_deploy_environment(self):
        pass

if __name__ == '__main__':
    pass  # Testing
