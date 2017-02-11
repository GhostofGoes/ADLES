#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# http://multivax.com/last_question.html

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Program used to create cybersecurity educational environments from formal specifications.

Usage:
    main.py [-d] --check-syntax FILE
    main.py [-d] --spec FILE
    main.py [-d] --package-dir NAME
    main.py --version
    main.py (-h | --help)

Options:
    -h, --help                  Shows this help
    --version                   Prints current version
    -d, --debug                 Emits debugging logs to terminal in addition to file
    -c, --check-syntax FILE     Validates syntax is valid per specification
    -s, --spec FILE             YAML file with the environment specification
    -p, --package-dir NAME      Filepath of the exercise package directory

Examples:
    main.py --check-syntax ../examples/tutorial.yaml
    main.py -d --spec ../examples/research.yaml
    main.py -s ../examples/competition.yaml

"""

from docopt import docopt
import logging

from automation.model import Model
from automation.parser import parse_file, verify_syntax

__version__ = "0.5.0"
__author__ = "Christopher Goes"
__email__ = "<goes8945@vandals.uidaho.edu>"


def main():
    from os.path import basename
    from os.path import exists

    if args["--spec"]:
        if not exists(args["--spec"]):
            exit(1)
        spec = parse_file(args["--spec"])
        logging.info("Successfully ingested %s", str(basename(args["--spec"])))
        logging.info("Checking syntax...")
        if verify_syntax(spec):
            logging.info("Syntax check successful!")
        else:
            logging.error("Syntax check failed!")
            exit(1)
        model = Model(spec)
        model.create_masters()
        model.deploy_environment()

    elif args["--check-syntax"]:
        if not exists(args["--check-syntax"]):
            exit(1)
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
    if args["--debug"]:
        console.setLevel(logging.DEBUG)
    else:
        console.setLevel(logging.INFO)
    formatter = logging.Formatter("%(levelname)-12s %(message)s")
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    main()
