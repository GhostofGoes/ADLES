#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# http://multivax.com/last_question.html

"""main

Usage:
    main.py --environment FILE --logins FILE --exercise FILE [Options]
    main.py --interactive
    main.py --package-dir
    main.py [Options]
    main.py --version
    main.py (-h | --help)

Options:
    -h, --help          Shows this help
    --version           Prints current version
    --interactive       Interactive input of needed information
    --environment FILE  YAML file with environment confirmation information [default: environment.yaml]
    --logins FILE       JSON file with login information for the environment [default: logins.json]
    --exercise FILE     YAML file with the exercise specification [default: exercise.yaml]
    --package-dir       Name of the exercise package directory

"""

from docopt import docopt
from getpass import getpass
import atexit
from pyVim.connect import SmartConnect, Disconnect
import logging

from automation import vsphere
from parser.parser import parse_file

__version__ = "0.1.0"
__author__  = "Christopher Goes"
__email__   = "<cgoes@uidaho.edu>"

logger = logging.getLogger(__name__)


# NOTE: currently this is built around vSphere, using vCenter server and ESXi 6.0 U2
def main():

    if args["--interactive"]:
        host = input("Hostname of vCenter server: ")
        port = input("Port of vCenter server: ")
        user = input("Username to login with: ")
        pswd = getpass("Password to login with: ")
        server = SmartConnect(host, port, user, pswd)
    else:
        from json import dump
        # TODO: login file definition
        server = SmartConnect(args["--host"], args["--port"], args["--user"], args["--password"])

    atexit.register(Disconnect, server)


if __name__ == '__main__':
    logging.basicConfig(filename='main.log', level=logging.DEBUG)
    args = docopt(__doc__, version=__version__, help=True)
    main()
