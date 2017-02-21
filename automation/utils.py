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
from getpass import getpass
from sys import stdout
from time import time
import logging


# From: virtual_machine_power_cycle_and_question.py in pyvmomi-community-samples
from automation.vsphere.vsphere import Vsphere


def _create_char_spinner():
    """ Creates a generator yielding a char based spinner """
    while True:
        for c in '|/-\\':
            yield c

_spinner = _create_char_spinner()


def spinner(label=''):
    """
    Prints label with a spinner. When called repeatedly from inside a loop this prints a one line CLI spinner.
    :param label: (Optional) The message to display while spinning (e.g "Loading", or the current percentage)
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
    :return:
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
        raise ValueError("Invalid default answer: '{}'".format(default))

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
    :param length: Length to pad to
    :return: string of padded value
    """
    return "{0:0>{width}}".format(value, width=length)


def read_json(filename):
    """
    Reads input from a JSON file and returns the contents
    :param filename:
    :return:
    """
    from json import load
    try:
        with open(filename, "r") as json_file:
            return load(fp=json_file)
    except Exception as e:
        logging.error("Could not open file %s. Error: %s", filename, str(e))
        return None


def setup_logging(filename, console_level=logging.INFO, file_level=logging.DEBUG):
    """
    Configures the logging interface used by everything for output
    :param filename: Name of file that logs should be saved to
    :param console_level: Level of logs that should be printed to terminal [default: logging.INFO]
    :param file_level: Level of logs that should be written to file [default: logging.DEBUG]
    """
    with open(filename, 'a') as logfile:
        logfile.write(5 * '\n')  # Prepend spaces to separate logs from different runs
    base_format = "[%(asctime)s] %(name)-12s %(levelname)-8s %(message)s"
    time_format = "%y-%m-%d %H:%M:%S"
    logging.basicConfig(level=file_level,
                        format=base_format,
                        datefmt=time_format,
                        filename=str(filename),
                        filemode='a')
    from sys import stdout
    console = logging.StreamHandler(stream=stdout)
    console.setLevel(console_level)
    formatter = logging.Formatter(fmt=base_format, datefmt=time_format)
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    from getpass import getuser
    from os import getcwd
    from sys import version, platform
    logging.debug("Initialized logging, saving logs to %s", filename)
    logging.debug("Python %s", str(version))
    logging.debug("Platform: %s", str(platform))
    logging.debug("Username: %s", str(getuser()))
    logging.debug("Current directory: %s\n", str(getcwd()))


# Credit to: http://stackoverflow.com/a/15707426/2214380
def time_execution(func):
    """
    Wrapper to time the execution of a function and log to debug
    :param func: The function to time execution of
    :return: The function (It's a wrapper...)
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
    :param filename: (Optional) Name of JSON file with information needed [default: None]
    :return: vSphere object
    """
    if filename:
        info = read_json(filename)
        user = (info["username"] if info["username"] else input("Username: "))
        pswd = (info["password"] if info["password"] else getpass("Password: "))
        return Vsphere(datacenter=info["datacenter"], username=user, password=pswd,
                       hostname=info["hostname"], port=info["port"], datastore=info["datastore"])
    else:
        logging.info("Enter information to connect to vSphere environment")
        host = input("Hostname: ")
        port = int(input("Port: "))
        user = input("Username: ")
        pswd = getpass("Password: ")
        datacenter = input("vSphere Datacenter: ")
        if prompt_y_n_question("Would you like to specify the datastore used "):
            datastore = input("vSphere Datastore: ")
        else:
            datastore = None
        return Vsphere(datacenter=datacenter, username=user, password=pswd,
                       hostname=host, port=port, datastore=datastore)


def warning():
    """ Prints a warning prompt. """
    logging.info("\nYou run this script at your own risk. If you break something, it's on YOU"
                 "\nIf you're paranoid, please read the code, and perhaps improve it =)\n")


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
            break
        else:
            logging.info("Couldn't find a {} with name {}. Perhaps try another? ".format(obj_name, item_name))
    return item, item_name
