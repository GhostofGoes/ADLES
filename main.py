#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# http://multivax.com/last_question.html

"""main

Usage:
    main.py --environment FILE --logins FILE --exercise FILE
    main.py --interactive --exercise FILE
    main.py --package-dir
    main.py --version
    main.py (-h | --help)

Options:
    -h, --help          Shows this help
    --version           Prints current version
    --interactive       Interactive input of login information
    --environment FILE  YAML file with environment confirmation information [default: environment.yaml]
    --logins FILE       JSON file with login information for the environment [default: logins.json]
    --exercise FILE     YAML file with the exercise specification [default: exercise.yaml]
    --package-dir       Name of the exercise package directory

"""

from docopt import docopt
from getpass import getpass
import logging

from automation.vsphere import vSphere
from parser.parser import parse_file

__version__ = "0.1.0"
__author__  = "Christopher Goes"
__email__   = "<cgoes@uidaho.edu>"

logger = logging.getLogger(__name__)


# TODO: Make a class?
# TODO: setup.py file to enable easy installation using pip (see: https://github.com/imsweb/ezmomi/blob/master/setup.py)
# TODO: license?
# NOTE: currently this is built around vSphere, using vCenter server and ESXi 6.0 U2
def main():

    if args["--interactive"]:
        host = input("Hostname of vCenter server: ")
        port = input("Port of vCenter server: ")
        user = input("Username to login with: ")
        pswd = getpass("Password to login with: ")
    # elif args["--package-dir"]:  # TODO: implement this when we functionalize the parsing
    # TODO: package structure
    else:
        # TODO: all of this will change to a generic parsing later, handled by function(s)/class(s)
        from json import load
        # TODO: login file definition
        with open(args["--logins"], "r") as login_file:
            logins = load(login_file)
        user = logins["user"]
        pswd = logins["password"]
        # TODO: environment file definition
        environment = parse_file(args["--environment"])  # We assume environment file is there
        host = environment["hostname"]
        port = environment["port"]

    server = vSphere(username=user, password=pswd, host=host, port=port)


if __name__ == '__main__':
    logging.basicConfig(filename='main.log', level=logging.DEBUG)
    args = docopt(__doc__, version=__version__, help=True)
    main()
