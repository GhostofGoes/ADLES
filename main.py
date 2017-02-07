#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# http://multivax.com/last_question.html

"""Program used to create cybersecurity educational environments from formal specifications.

Usage:
    main.py --check-syntax FILE
    main.py --spec FILE
    main.py --package-dir NAME
    main.py --version
    main.py (-h | --help)

Options:
    -h, --help                  Shows this help
    --version                   Prints current version
    -c, --check-syntax FILE     Validates syntax is valid per specification
    -s, --spec FILE             YAML file with the environment specification
    -p, --package-dir NAME      Filepath of the exercise package directory

"""

from docopt import docopt
import logging

from automation.model import Model
from automation.parser import parse_file, verify_syntax


__version__ = "0.4.0"
__author__  = "Christopher Goes"
__email__   = "<goes8945@vandals.uidaho.edu>"


# TODO: setup.py file to enable easy installation using pip (see: https://github.com/imsweb/ezmomi/blob/master/setup.py)
# TODO: license?
def main():
    from os.path import basename

    if args["--spec"]:
        spec = parse_file(args["--spec"])
        logging.info("Successfully ingested %s", str(basename(args["--spec"])))
        logging.info("Checking syntax...")
        if verify_syntax(spec):
            logging.info("Syntax check successful!")
        else:
            logging.error("Syntax check failed!")
            return 1
        model = Model(spec["metadata"])
        model.create_masters()
        model.deploy_environment()

    elif args["--check-syntax"]:
        spec = parse_file(args["--check-syntax"])
        logging.info("Successfully ingested %s", str(basename(args["--check-syntax"])))
        logging.info("Checking syntax...")
        if verify_syntax(spec):
            logging.info("Syntax check successful!")
        else:
            logging.error("Syntax check failed!")
            exit(1)

    elif args["--package-dir"]:
        logging.error("CURRENTLY UNSUPPORTED")


if __name__ == '__main__':
    args = docopt(__doc__, version=__version__, help=True)

    logging.basicConfig(level=logging.DEBUG,
                        format="[%(asctime)s] %(name)-12s %(levelname)-8s %(message)s",
                        datefmt="%y-%m-%d %H:%M:%S",
                        filename="environment-creator.log",
                        filemode='w')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter("%(levelname)-12s %(message)s")
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)


    main()
