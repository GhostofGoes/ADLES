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

from sys import stdout, exit
import os


def check(arg_type, kwarg_name):
    """
    Function decorator that validates types of parameters
    :param arg_type: Type to validate
    :param kwarg_name: Name of keyword argument to validate
    :return: The decorated function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if args and isinstance(args[0], arg_type):  # We assume it is the first argument
                return func(*args, **kwargs)
            elif kwargs and isinstance(kwargs.get(kwarg_name, None), arg_type):
                return func(*args, **kwargs)
            else:
                logging.error("Function '%s' failed check for type '%s'\nArgs: %s\nkwargs: %s",
                              func.__name__, arg_type.__name__, str(args), str(kwargs))
        return wrapper
    return decorator


# Credit to: http://stackoverflow.com/a/15707426/2214380
def time_execution(func):
    """
    Function decorator to time the execution of a function and log to debug
    :param func: The function to time execution of
    :return: The decorated function
    """
    from timeit import default_timer

    def wrapper(*args, **kwargs):
        start_time = default_timer()
        ret = func(*args, **kwargs)
        end_time = default_timer()
        logging.debug("Elapsed time for %s: %f seconds", func.__name__,
                      float(end_time - start_time))
        return ret
    return wrapper


# From: list_dc_datastore_info in pyvmomi-community-samples
# http://stackoverflow.com/questions/1094841/
def sizeof_fmt(num):
    """
    Generates the human-readable version of a file size

    >>> sizeof_fmt(512)
    512bytes
    >>> sizeof_fmt(2048)
    2KB

    :param num: Robot-readable file size in bytes
    :return: Human-readable file size
    """
    for item in ['bytes', 'KB', 'MB', 'GB']:
        if num < 1024.0:
            return "%3.1f%s" % (num, item)
        num /= 1024.0
    return "%3.1f%s" % (num, 'TB')


# From: virtual_machine_power_cycle_and_question in pyvmomi-community-samples
def _create_char_spinner():
    """ Creates a generator yielding a char based spinner """
    while True:
        for c in '|/-\\':
            yield c

_spinner = _create_char_spinner()


def spinner(label=""):
    """
    When called repeatedly from inside a loop this prints a CLI spinner
    :param label: The message to display while spinning [default: ""]
    """
    stdout.write("\r\t%s %s" % (label, next(_spinner)))
    stdout.flush()


def pad(value, length=2):
    """
    Adds leading and trailing zeros to value ("pads" the value)

    >>> pad(5)
    05
    >>> pad(9, 3)
    009

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
    except ValueError as e:
        logging.error("Syntax Error in JSON file '%s': %s", filename, str(e))
        return None
    except Exception as e:
        logging.error("Could not open file '%s': %s", filename, str(e))
        return None


def make_vsphere(filename=None):
    """
    Creates a vSphere object using either a JSON file or by prompting the user
    :param filename: Name of JSON file with information needed [default: None]
    :return: vSphere object
    """
    from getpass import getpass
    from adles.vsphere.vsphere_class import Vsphere

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
        try:
            item_name = str(input(prompt))
        except KeyboardInterrupt:
            print()
            logging.info("Exiting...")
            exit(0)
        item = func(item_name)
        if item:
            logging.info("Found %s: %s", obj_name, item.name)
            return item, item_name
        else:
            print("Couldn't find a %s with name %s. Perhaps try another? "
                  % (obj_name, item_name))


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
    choice = ''
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("Invalid default answer: '%s'", default)

    while True:
        try:
            choice = input(question + prompt).lower()
        except KeyboardInterrupt:
            print()
            logging.info("Exiting...")
            exit(0)

        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            print("Please respond with 'yes' or 'no' or 'y' or 'n'")


def default_prompt(prompt, default=None):
    """
    Prompt the user for input. If they press enter, return the default
    :param prompt: Prompt to display to user (do not include default value)
    :param default: Default return value
    :return: Value returned
    """
    try:
        value = input(prompt + " [default: %s]: " % str(default))
    except KeyboardInterrupt:
        print()
        logging.info("Exiting...")
        exit(0)

    # noinspection PyUnboundLocalVariable
    if value == '':
        return default
    else:
        return value


def script_warning_prompt():
    """ Prints a warning prompt. """
    from adles import __url__, __email__
    return str(
        '***** YOU RUN THIS SCRIPT AT YOUR OWN RISK *****\n'
        '\nGetting help:'
        '\n\t* "<script>.py --help": flags, arguments, and usage'
        '\n\t* "cat <script>.py": read the source code and see how it works'
        '\n\t* "cd ./documentation && ls -la": show available documentation'
        '\n\t+ Open an issue on the project GitHub: %s'
        '\n\t+ Email the script author: %s'
        '\n\n' % (__url__, __email__))


def script_setup(logging_filename, args, script=None):
    """
    Does setup tasks that are common to all automation scripts
    :param logging_filename: Name of file to save logs to
    :param args: docopt arguments dict
    :param script: Tuple with name and version of the script [default: None]
    :return: vSphere object
    """

    # Setup logging
    colors = (False if args["--no-color"] else True)
    setup_logging(filename=logging_filename, colors=colors,
                  console_verbose=args["--verbose"])

    # Print information about script itself
    if script:
        logging.debug("Script name      %s", os.path.basename(script[0]))
        logging.debug("Script version   %s", script[1])
        print(script_warning_prompt())  # Print warning for script users

    # Create the vsphere object and return it
    try:
        return make_vsphere(args["--file"])
    except KeyboardInterrupt:
        print()
        logging.info("Exiting...")
        exit(0)


def resolve_path(server, thing, prompt=""):
    """
    This is a hacked together script util to get folders or VMs
    :param server: Vsphere instance
    :param thing: String name of thing to get (folder | vm)
    :param prompt: Message to display [default: ""]
    :return: (thing, thing name)
    """
    from adles.vsphere.folder_utils import traverse_path
    if thing.lower() == "vm":
        get = server.get_vm
    elif thing.lower() == "folder":
        get = server.get_folder
    else:
        logging.error("Invalid thing passed to resolve_path: %s", thing)
        raise ValueError

    return user_input("Name of or path to %s %s: " % (thing, prompt), thing,
                      lambda x: traverse_path(server.get_folder(), x, lookup_root=server)
                      if '/' in x else get(x))


def setup_logging(filename, colors=True, console_verbose=False,
                  server=('localhost', 514)):
    """
    Configures the logging interface used by everything for output
    :param filename: Name of file that logs should be saved to
    :param colors: Color the terminal output [default: True]
    :param console_verbose: Print DEBUG logs to terminal [default: False]
    :param server: SysLog server to forward logs to [default: (localhost, 514)]
    """

    # Prepend spaces to separate logs from previous runs
    with open(filename, 'a') as logfile:
        logfile.write(2 * '\n')

    # Format log output so it's human readable yet verbose
    base_format = "[%(asctime)s] %(name)-8s %(levelname)-8s %(message)s"
    time_format = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt=base_format, datefmt=time_format)

    # Configures the base logger to append to a file
    logging.basicConfig(level=logging.DEBUG, format=base_format, datefmt=time_format,
                        filename=filename, filemode='a')

    # Get the global root logger
    logger = logging.root

    # Configure logging to a SysLog server
    # This prevents students from simply deleting the log files
    syslog = logging.handlers.SysLogHandler(address=server)
    syslog.setLevel(logging.DEBUG)
    syslog.setFormatter(formatter)
    logger.addHandler(syslog)
    logging.debug("Configured logging to SysLog server %s:%s", server[0], str(server[1]))

    # Configure console output
    console = logging.StreamHandler(stream=stdout)
    if colors:  # Colored console output
        try:
            # noinspection PyUnresolvedReferences
            from colorlog import ColoredFormatter
            formatter = ColoredFormatter(fmt="%(log_color)s" + base_format,
                                         datefmt=time_format, reset=True)
            logging.debug("Configured COLORED console logging output")
        except ImportError:
            logging.error("Colorlog is not installed. Using STANDARD console output...")
    else:  # Bland console output
        logging.debug("Configured STANDARD console logging output")
    console.setFormatter(formatter)
    console.setLevel((logging.DEBUG if console_verbose else logging.INFO))
    logger.addHandler(console)

    # Record system information to aid in auditing and debugging
    from getpass import getuser
    from os import getcwd
    from platform import python_version, platform
    from adles import __version__ as adles_version
    from adles.vsphere.vsphere_class import Vsphere
    logging.debug("Initialized logging, saving logs to %s", filename)
    logging.debug("Python           %s", str(python_version()))
    logging.debug("Platform         %s", str(platform()))
    logging.debug("Username         %s", str(getuser()))
    logging.debug("Directory        %s", str(getcwd()))
    logging.debug("Adles version    %s", str(adles_version))
    logging.debug("Vsphere version  %s", str(Vsphere.__version__))
