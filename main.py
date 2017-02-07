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

from automation.model import Spec


__version__ = "0.4.0"
__author__  = "Christopher Goes"
__email__   = "<goes8945@vandals.uidaho.edu>"


# TODO: setup.py file to enable easy installation using pip (see: https://github.com/imsweb/ezmomi/blob/master/setup.py)
# TODO: license?
def main():

    if args["--interactive"]:
        host = input("Hostname of vCenter server: ")
        port = input("Port of vCenter server: ")
        user = input("Username to login with: ")
        pswd = getpass("Password to login with: ")


if __name__ == '__main__':
    logging.basicConfig(filename='main.log', level=logging.DEBUG)
    args = docopt(__doc__, version=__version__, help=True)
    main()
