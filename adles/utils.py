#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

import logging
import logging.handlers

from sys import stdout
from time import time

from adles.vsphere import Vsphere


# From: virtual_machine_power_cycle_and_question.py in pyvmomi-community-samples
def _create_char_spinner():
    """ Creates a generator yielding a char based spinner """
    while True:
        for c in '|/-\\':
            yield c

_spinner = _create_char_spinner()


def spinner(label=""):
    """
    Prints label with a spinner. When called repeatedly from inside a loop this prints a one line CLI spinner.
    :param label: The message to display while spinning (e.g "Loading", or the current percentage) [default: ""]
    """
    stdout.write("\r\t%s %s" % (label, next(_spinner)))
    stdout.flush()


# From: list_dc_datastore_info.py in pyvmomi-community-samples
# http://stackoverflow.com/questions/1094841/
# Could also use humanize for this sort of thing: https://pypi.python.org/pypi/humanize/0.5.1
def sizeof_fmt(num):
    """
    Returns the human readable version of a file size
    :param num:
    :return: Human readable version of a file size
    """
    for item in ['bytes', 'KB', 'MB', 'GB']:
        if num < 1024.0:
            return "%3.1f%s" % (num, item)
        num /= 1024.0
    return "%3.1f%s" % (num, 'TB')


# Based on: http://code.activestate.com/recipes/577058/
def prompt_y_n_question(question, default="no"):
    """
    Prompts user to answer a question
    :param question: Question to ask
    :param default: No
    :return: True/False
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("Invalid default answer: '%s'", default)

    while True:
        logging.info(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            print("Please, respond with 'yes' or 'no' or 'y' or 'n'.")


def pad(value, length=2):
    """
    Adds leading and trailing ("pads") zeros to value to ensure it is a constant length
    :param value: integer value to pad
    :param length: Length to pad to [default: 2]
    :return: string of padded value
    """
    return "{0:0>{width}}".format(value, width=length)


def read_json(filename):
    """
    Reads input from a JSON file and returns the contents
    :param filename: Path to JSON file to read
    :return: Contents of the JSON file
    """
    from json import load
    try:
        with open(filename, "r") as json_file:
            return load(fp=json_file)
    except Exception as e:
        logging.error("Could not open file %s. Error: %s", filename, str(e))
        return None


def setup_logging(filename, colors=True, console_level=logging.INFO, server=('localhost', 514)):
    """
    Configures the logging interface used by everything for output
    :param filename: Name of file that logs should be saved to
    :param colors: Whether log output on terminal should be colored (requires colorlog package) [default: True]
    :param console_level: Level of logs that should be printed to terminal [default: logging.INFO]
    :param server: (address, port) of a SysLog server to forward logs to [default: (localhost, 514)]
    """

    # Prepend spaces to separate logs from previous
    with open(filename, 'a') as logfile:
        logfile.write(5 * '\n')

    # Format log output so it's human readable yet verbose
    base_format = "[%(asctime)s] %(name)-12s %(levelname)-8s %(message)s"
    time_format = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt=base_format, datefmt=time_format)

    # Configures the base logger to append to a file
    logging.basicConfig(level=logging.DEBUG,
                        format=base_format,
                        datefmt=time_format,
                        filename=str(filename),
                        filemode='a')

    # Get the global root logger
    logger = logging.root

    # Configure logging to a SysLog server (This prevents students from deleting the log files)
    syslog = logging.handlers.SysLogHandler(address=server)
    syslog.setLevel(logging.DEBUG)
    syslog.setFormatter(formatter)
    logger.addHandler(syslog)
    logging.debug("Configured system logging to SysLog")

    # Configure console output
    console = logging.StreamHandler(stream=stdout)
    if colors:  # Colored console output
        from colorlog import ColoredFormatter
        console.setFormatter(ColoredFormatter(fmt="%(log_color)s" + base_format,
                                              datefmt=time_format, reset=True, log_colors={
                                                            'DEBUG': 'white', 'INFO': 'green',
                                                            'WARNING': 'yellow', 'ERROR': 'red', 'CRITICAL': 'red'}))
        logging.debug("Configured COLORED console logging output")
    else:  # Bland console output
        console.setFormatter(formatter)
        logging.debug("Configured STANDARD console logging output")
    console.setLevel(console_level)
    logger.addHandler(console)

    # Record system information to aid in auditing and debugging
    from getpass import getuser
    from os import getcwd
    from sys import version, platform
    logging.debug("Initialized logging, saving logs to %s", str(filename))
    logging.debug("Python       %s", str(version))
    logging.debug("Platform     %s", str(platform))
    logging.debug("Username     %s", str(getuser()))
    logging.debug("Directory    %s", str(getcwd()))
    print("\n\n")


# Credit to: http://stackoverflow.com/a/15707426/2214380
def time_execution(func):
    """
    Wrapper to time the execution of a function and log to debug
    :param func: The function to time execution of
    :return: The function
    """
    def wrapper(*args, **kwargs):
        start_time = time()
        ret = func(*args, **kwargs)
        end_time = time()
        logging.debug("Elapsed time for %s: %f seconds", str(func.__name__), float(end_time - start_time))
        return ret
    return wrapper


def make_vsphere(filename=None):
    """
    Creates a vSphere object using either a JSON file or by prompting the user for input
    :param filename: Name of JSON file with information needed [default: None]
    :return: vSphere object
    """
    from getpass import getpass
    if filename:
        info = read_json(filename)
        user = (info["user"] if "user" in info else input("Username: "))
        pswd = (info["pass"] if "pass" in info else getpass("Password: "))
        datacenter = (info["datacenter"] if "datacenter" in info else None)
        datastore = (info["datastore"] if "datastore" in info else None)
        port = (info["port"] if "port" in info else 443)
        return Vsphere(datacenter=datacenter, username=user, password=pswd,
                       hostname=info["host"], port=port, datastore=datastore)
    else:
        logging.info("Enter information to connect to vSphere environment")
        host = input("Hostname: ")
        port = int(input("Port: "))
        user = input("Username: ")
        pswd = getpass("Password: ")
        datacenter = input("vSphere Datacenter: ")
        datastore = input("vSphere Datastore: ")
        return Vsphere(username=user, password=pswd, hostname=host,
                       datacenter=datacenter, datastore=datastore, port=port)


def user_input(prompt, obj_name, func):
    """
    Continually bothers a user for input until we get what we want from them
    :param prompt: Prompt to bother user with
    :param obj_name: Name of the type of the object that we seek
    :param func: The function that shalt be called to discover the object
    :return: The discovered object and it's human name
    """
    while True:
        item_name = input(prompt)
        item = func(item_name)
        if item:
            logging.debug("Found %s: %s", obj_name, item.name)
            return item, item_name
        else:
            print("Couldn't find a %s with name %s. Perhaps try another? " % (obj_name, item_name))


def default_prompt(prompt, default=None):
    """
    Prompt the user for input. If they press enter, return the default
    :param prompt: Prompt to display to user. Do not include the default, it will be appended.
    :param default: Default return value
    :return: Value returned
    """
    value = input(prompt + " [default: %s]: " % str(default))
    if value == '':
        return default
    else:
        return value


def script_warning_prompt():
    """ Prints a warning prompt. """
    print("\n\n\n** YOU RUN THIS SCRIPT AT YOUR OWN RISK **"
          "\nPlease read the source code or documentation for information on proper script usage\n\n")


def script_setup(logging_filename, args):
    """

    :param logging_filename:
    :param args:
    :return: vSphere object
    """

    # Setup logging
    setup_logging(filename=logging_filename, console_level=logging.DEBUG if args["--verbose"] else logging.INFO)

    # Print warning
    script_warning_prompt()

    # Create the vsphere object and return it
    return make_vsphere(args["--file"])
