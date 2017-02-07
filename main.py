#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# http://multivax.com/last_question.html

"""main

Usage:
    main.py --spec FILE
    main.py --interactive
    main.py --package-dir
    main.py --version
    main.py (-h | --help)

Options:
    -h, --help              Shows this help
    --version               Prints current version
    --spec FILE             YAML file with the environment specification [default: spec.yaml]
    --package-dir           Name of the exercise package directory
    --interactive           Interactive mode

"""

from docopt import docopt
from getpass import getpass
import logging
import coloredlogs

from automation.model import Spec
from automation.parser import parse_file, verify_syntax


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

    if args["--spec"]:
        spec = parse_file(args["--spec"])
        print("Successfully ingested specification\nChecking syntax...")
        logging.info("Successfully ingested specification\nChecking syntax...")
        if verify_syntax(spec):
            logging.info("Syntax check successful!")
            print("Syntax check successful!")
        else:
            print("Syntax check failed!\nExiting...")
            return 1
        model = Spec(spec["metadata"])


if __name__ == '__main__':
    coloredlogs.install(level='DEBUG', fmt="[%(asctime)s] (%(levelname)s)  %(message)s", datefmt="%H:%M:%S")
    args = docopt(__doc__, version=__version__, help=True)
    main()
