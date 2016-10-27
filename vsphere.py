#!/usr/bin/env python3
# http://multivax.com/last_question.html

"""vsphere

Usage:
    vsphere.py --logins FILE [options]
    vsphere.py (-i | --interactive) [options]
    vsphere.py [options]
    vsphere.py --version
    vsphere.py (-h | --help)

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

__version__ = "0.1.0"
__author__ = "Christopher Goes <cgoes@uidaho.edu>"


def clone_vm():


def main():
    args = docopt(__doc__, version=__version__, help=True)

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
        if args["-a"]:
            pass

if __name__ == '__main__':
    main()
