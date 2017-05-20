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

import sys
import os


# Credit to: http://stackoverflow.com/a/15707426/2214380
def time_execution(func):
    """
    Function decorator to time the execution of a function and log to debug.

    :param func: The function to time execution of
    :return: The decorated function
    :rtype: func
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
    Generates the human-readable version of a file size.

    >>> sizeof_fmt(512)
    512bytes
    >>> sizeof_fmt(2048)
    2KB

    :param float num: Robot-readable file size in bytes
    :return: Human-readable file size
    :rtype: str
    """
    for item in ['bytes', 'KB', 'MB', 'GB']:
        if num < 1024.0:
            return "%3.1f%s" % (num, item)
        num /= 1024.0
    return "%3.1f%s" % (num, 'TB')


def pad(value, length=2):
    """
    Adds leading and trailing zeros to value ("pads" the value).

    >>> pad(5)
    05
    >>> pad(9, 3)
    009

    :param int value: integer value to pad
    :param int length: Length to pad to [default: 2]
    :return: string of padded value
    :rtype: str
    """
    return "{0:0>{width}}".format(value, width=length)


def read_json(filename):
    """
    Reads input from a JSON file and returns the contents.

    :param str filename: Path to JSON file to read
    :return: Contents of the JSON file
    :rtype: dict or None
    """
    from json import load
    try:
        with open(filename) as json_file:
            return load(fp=json_file)
    except ValueError as message:
        logging.error("Syntax Error in JSON file '%s': %s",
                      filename, str(message))
        return None
    except Exception as message:
        logging.critical("Could not open JSON file '%s': %s",
                         filename, str(message))
        return None


def split_path(path):
    """
    Splits a filepath.

    >>> split_path('/path/To/A/f1le')
    (['path', 'To', 'A'], 'file')

    :param str path: Path to split
    :return: Path, basename
    :rtype: tuple(list(str), str)
    """
    # Separate basename and convert to lowercase
    folder_path, name = os.path.split(path.lower())

    # Transform path into list
    folder_path = folder_path.split('/')

    if folder_path[0] == '':
        del folder_path[0]
    return folder_path, name


def make_vsphere(filename=None):
    """
    Creates a vSphere object using either a JSON file or by prompting the user.

    :param str filename: Name of JSON file with connection info [default: None]
    :return: vSphere object
    :rtype: :class:`Vsphere`
    """
    from adles.vsphere.vsphere_class import Vsphere

    if filename is not None:
        info = read_json(filename)
        return Vsphere(username=info.get("user"),
                       password=info.get("pass"),
                       hostname=info.get("host"),
                       port=info.get("port", 443),
                       datacenter=info.get("datacenter"),
                       datastore=info.get("datastore"))
    else:
        logging.info("Enter information to connect to vSphere environment")
        datacenter = input("Datacenter  : ")
        datastore = input("Datastore   : ")
        return Vsphere(datacenter=datacenter, datastore=datastore)


def user_input(prompt, obj_name, func):
    """
    Continually prompts a user for input until the specified object is found.

    :param str prompt: Prompt to bother user with
    :param str obj_name: Name of the type of the object that we seek
    :param func: The function that shalt be called to discover the object
    :return: The discovered object and it's human name
    :rtype: tuple(vimtype, str)
    """
    while True:
        try:
            item_name = str(input(prompt))
        except KeyboardInterrupt:
            print()
            logging.info("Exiting...")
            sys.exit(0)
        item = func(item_name)
        if item:
            logging.info("Found %s: %s", obj_name, item.name)
            return item, item_name
        else:
            print("Couldn't find a %s with name %s. Perhaps try another? "
                  % (obj_name, item_name))


# Based on: http://code.activestate.com/recipes/577058/
def ask_question(question, default="no"):
    """
    Prompts user to answer a question.

    >>> ask_question("Do you like the color yellow?")
    Do you like the color yellow? [y/N]

    :param str question: Question to ask
    :param str default: No
    :return: True/False
    :rtype: bool
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
            choice = str(input(question + prompt)).lower()
        except KeyboardInterrupt:
            print()  # Output a blank line for readability
            logging.info("Exiting...")
            sys.exit(0)

        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            print("Please respond with 'yes' or 'no' or 'y' or 'n'")


def default_prompt(prompt, default=None):
    """
    Prompt the user for input. If they press enter, return the default.

    :param str prompt: Prompt to display to user (do not include default value)
    :param str default: Default return value [default: None]
    :return: Value entered or default
    :rtype: str or None
    """
    try:
        value = str(input(prompt + " [default: %s]: " % str(default)))
    except KeyboardInterrupt:
        print()  # Output a blank line for readability
        logging.info("Exiting...")
        sys.exit(0)
    else:
        return default if value == '' else value


def _script_warning_prompt():
    """
    Generates a warning prompt.

    :return: The warning prompt
    :rtype: str
    """
    from adles import __url__, __email__
    return str(
        '***** YOU RUN THIS SCRIPT AT YOUR OWN RISK *****\n'
        '\n ** Help and Documentation **'
        '\n+ "<script> --help": flags, arguments, and usage'
        '\n+ Read the latest documentation  : https://adles.readthedocs.io'
        '\n+ Open an issue on GitHub        : %s'
        '\n+ Email the script author        : %s'
        '\n' % (__url__, __email__))


def script_setup(logging_filename, args, script=None):
    """
    Does setup tasks that are common to all automation scripts.

    :param str logging_filename: Name of file to save logs to
    :param dict args: docopt arguments dict
    :param script: Tuple with name and version of the script [default: None]
    :type: tuple(str, str)
    :return: vSphere object
    :rtype: :class:`Vsphere`
    """

    # Setup logging
    colors = (False if args["--no-color"] else True)
    setup_logging(filename=logging_filename, colors=colors,
                  console_verbose=args["--verbose"])

    # Print information about script itself
    if script:
        logging.debug("Script name      %s", os.path.basename(script[0]))
        logging.debug("Script version   %s", script[1])
        print(_script_warning_prompt())  # Print warning for script users

    # Create the vsphere object and return it
    try:
        return make_vsphere(args["--file"])
    except KeyboardInterrupt:
        print()  # Output a blank line for readability
        logging.info("Exiting...")
        sys.exit(0)


def resolve_path(server, thing, prompt=""):
    """
    This is a hacked together script utility to get folders or VMs.

    :param server: Vsphere instance
    :type server: :class:`Vsphere`
    :param str thing: String name of thing to get (folder | vm)
    :param str prompt: Message to display [default: ""]
    :return: (thing, thing name)
    :rtype: tuple(vimtype, str)
    """
    from adles.vsphere.vm import VM
    if thing.lower() == "vm":
        get = server.get_vm
    elif thing.lower() == "folder":
        get = server.get_folder
    else:
        logging.error("Invalid thing passed to resolve_path: %s", thing)
        raise ValueError

    res = user_input("Name of or path to %s %s: " % (thing, prompt), thing,
                     lambda x: server.find_by_inv_path("vm/" + x)
                     if '/' in x else get(x))
    if thing.lower() == "vm":
        return VM(vm=res[0]), res[1]
    else:
        return res


def setup_logging(filename, colors=True, console_verbose=False,
                  server=('localhost', 514)):
    """
    Configures the logging interface used by everything for output.

    :param str filename: Name of file that logs should be saved to
    :param bool colors: Color the terminal output [default: True]
    :param bool console_verbose: Print DEBUG logs to terminal [default: False]
    :param server: SysLog server to forward logs to [default: (localhost, 514)]
    :type server: tuple(str, int)
    """

    # Prepend spaces to separate logs from previous runs
    with open(filename, 'a') as logfile:
        logfile.write(2 * '\n')

    # Format log output so it's human readable yet verbose
    base_format = "%(asctime)s %(levelname)-8s %(name)-7s %(message)s"
    time_format = "%H:%M:%S"  # %Y-%m-%d
    formatter = logging.Formatter(fmt=base_format, datefmt=time_format)

    # Configures the base logger to append to a file
    logging.basicConfig(level=logging.DEBUG, format=base_format,
                        datefmt=time_format, filename=filename, filemode='a')

    # Get the global root logger
    logger = logging.root

    # Configure logging to a SysLog server
    # This prevents students from simply deleting the log files
    syslog = logging.handlers.SysLogHandler(address=server)
    syslog.setLevel(logging.DEBUG)
    syslog.setFormatter(formatter)
    logger.addHandler(syslog)
    logging.debug("Configured logging to SysLog server %s:%s",
                  server[0], str(server[1]))

    # Configure console output
    console = logging.StreamHandler(stream=sys.stdout)
    if colors:  # Colored console output
        try:
            # noinspection PyUnresolvedReferences
            from colorlog import ColoredFormatter
            formatter = ColoredFormatter(fmt="%(log_color)s" + base_format,
                                         datefmt=time_format, reset=True)
            logging.debug("Configured COLORED console logging output")
        except ImportError:
            logging.error("Colorlog is not installed. "
                          "Using STANDARD console output...")
    else:  # Bland console output
        logging.debug("Configured STANDARD console logging output")
    console.setFormatter(formatter)
    console.setLevel((logging.DEBUG if console_verbose else logging.INFO))
    logger.addHandler(console)

    # Record system information to aid in auditing and debugging
    from getpass import getuser
    from os import getcwd
    from platform import python_version, system, release, node
    from datetime import date
    from adles import __version__ as adles_version
    logging.debug("Initialized logging, saving logs to %s", filename)
    logging.debug("Date             %s", str(date.today()))
    logging.debug("OS               %s", str(system() + " " + release()))
    logging.debug("Hostname         %s", str(node()))
    logging.debug("Username         %s", str(getuser()))
    logging.debug("Directory        %s", str(getcwd()))
    logging.debug("Python version   %s", str(python_version()))
    logging.debug("Adles version    %s", str(adles_version))


def get_vlan():
    """
    Generates globally unique VLAN tags.

    :return: VLAN tag
    :rtype: int
    """
    for i in range(2000, 4096):
        yield i


def is_folder(obj):
    """
    Checks if object is a vim.Folder.

    :param obj: The object to check
    :return: If the object is a folder
    :rtype: bool
    """
    return hasattr(obj, "childEntity")


def is_vm(obj):
    """
    Checks if object is a vim.VirtualMachine.

    :param obj: The object to check
    :return: If the object is a VM
    :rtype: bool
    """
    return hasattr(obj, "summary")
