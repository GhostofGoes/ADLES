#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# http://multivax.com/last_question.html

"""main

Usage:
    main.py --logins FILE [options]
    main.py (-i | --interactive) [options]
    main.py [options]
    main.py --version
    main.py (-h | --help)

Options:
    -h, --help      Duh
    --version       Double duh
    --logins        File with login information for vSphere
    --interactive   Interactive input of login information
    -s, --host      vCenter server to connect to
    -o, --port      Port to connect on
    -u, --user      Username to login with
    -p, --password  Password to login with
    -f, --file      File with one or more actions to perform
    -a, --action    Action to perform
    -m, --method    Method used to perform action

"""

from docopt import docopt
from getpass import getpass
import atexit
from pyVim.connect import SmartConnect, Disconnect
import logging

from automation import vsphere

__version__ = "0.1.0"
__author__ = "Christopher Goes <cgoes@uidaho.edu>"

logger = logging.getLogger(__name__)


# NOTE: currently this is built around vSphere, using vCenter server and ESXi 6.0 U2
def main():
    args = docopt(__doc__, version=__version__, help=True)

    # TODO: could we put server info in the specification file? or have the login filename in the spec file?
    if args["--interactive"]:
        host = input("Hostname of vCenter server: ")
        port = input("Port of vCenter server: ")
        user = input("Username to login with: ")
        pswd = getpass("Password to login with: ")
        server = SmartConnect(host, port, user, pswd)
    elif args["--logins"]:
        from json import dump
        # TODO: login file definition
    else:
        server = SmartConnect(args["--host"], args["--port"], args["--user"], args["--password"])
    atexit.register(Disconnect, server)

    if args["-a"]:
        if args["-a"] == "an_action":
            pass


if __name__ == '__main__':
    logging.basicConfig(filename='main.log', level=logging.DEBUG)
    main()
