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
import timeit
import json

try:
    import tqdm
    TQDM = True

    class TqdmHandler(logging.StreamHandler):
        def __init__(self, level=logging.NOTSET):
            super(self.__class__, self).__init__(level)

        def emit(self, record):
            try:
                msg = self.format(record)
                tqdm.tqdm.write(msg)
                self.flush()
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                self.handleError(record)
except ImportError:
    TQDM = False


# Credit to: http://stackoverflow.com/a/15707426/2214380
def time_execution(func):
    """
    Function decorator to time the execution of a function and log to debug.

    :param func: The function to time execution of
    :return: The decorated function
    :rtype: func
    """
    def wrapper(*args, **kwargs):
        start_time = timeit.default_timer()
        ret = func(*args, **kwargs)
        end_time = timeit.default_timer()
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
    :param int length: Length to pad to
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
    try:
        with open(filename) as json_file:
            return json.load(fp=json_file)
    except ValueError as message:
        logging.error("Syntax Error in JSON file '%s': %s",
                      filename, str(message))
    except FileNotFoundError:
        logging.error("Could not find file %s", filename)
    except Exception as message:
        logging.error("Could not open JSON file '%s': %s",
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
    folder_path, name = os.path.split(path.lower())  # Separate basename
    folder_path = folder_path.split('/')  # Transform path into list
    if folder_path[0] == '':
        del folder_path[0]
    return folder_path, name


def handle_keyboard_interrupt(func):
    """Function decorator to handle
    keyboard interrupts in a consistent manner."""

    # Based on: http://code.activestate.com/recipes/577058/
    def wrapper(*args, **kwargs):
        try:
            ret = func(*args, **kwargs)
        except KeyboardInterrupt:
            print()  # Output a blank line for readability
            logging.info("Exiting...")
            sys.exit(0)
        return ret
    return wrapper


@handle_keyboard_interrupt
def get_args(docstring, version, logging_filename):
    """
    Handles commandline argument parsing and logging setup.

    :param str docstring: docopt-formatting docstring
    :param str version: version string
    :param str logging_filename: Name of file to save logs to
    :return: Commandline arguments the user provided
    :rtype: Object
    """
    from argopt import argopt

    # Suppress argopt logging messages (TODO: open an issue about this)
    for noisy_logger in ['argopt', '_argopt', 'argopt._argopt']:
        logging.getLogger(noisy_logger).setLevel(logging.CRITICAL)

    # TODO: add shim for Gooey

    # Handle case where user provides no arguments
    if len(sys.argv) == 1:
        sys.argv.append("--help")

    # Get and process commandline arguments
    parser = argopt(docstring, version=version)
    args = parser.parse_args()

    # Set if console output should be colored
    colors = (False if args.no_color else True)

    # Syslog server
    if args.syslog:
        syslog = (str(args.syslog), 514)
    else:
        syslog = None

    # Configure logging globally
    setup_logging(filename=logging_filename, colors=colors,
                  console_verbose=args.verbose, server=syslog)
    return args


def setup_logging(filename, colors=True, console_verbose=False,
                  server=None, show_progress=True):
    """
    Configures the logging interface used by everything for output.

    :param str filename: Name of file that logs should be saved to
    :param bool colors: Color the terminal output
    :param bool console_verbose: Print DEBUG logs to terminal
    :param server: SysLog server to forward logs to
    :type server: tuple(str, int)
    :param bool show_progress: Show live status as operations progress
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
    # Handlers added to this will propagate to all loggers
    logger = logging.root

    # Configure logging to a SysLog server
    # This prevents students from simply deleting the log files
    if server is not None:
        syslog = logging.handlers.SysLogHandler(address=server)
        syslog.setLevel(logging.DEBUG)
        syslog.setFormatter(formatter)
        logger.addHandler(syslog)
        logging.debug("Configured logging to SysLog server %s:%d",
                      server[0], server[1])

    # Record system information to aid in auditing and debugging
    # We do this before configuring console output to reduce verbosity
    from getpass import getuser
    from platform import python_version, system, release, node
    from datetime import date
    from adles import __version__ as adles_version
    logging.debug("Initialized logging, saving logs to %s", filename)
    logging.debug("Date             %s", str(date.today()))
    logging.debug("OS               %s", str(system() + " " + release()))
    logging.debug("Hostname         %s", str(node()))
    logging.debug("Username         %s", str(getuser()))
    logging.debug("Directory        %s", str(os.getcwd()))
    logging.debug("Python version   %s", str(python_version()))
    logging.debug("Adles version    %s", str(adles_version))

    # If any of the libraries we're using have warnings, capture and log them
    logging.captureWarnings(capture=True)

    # Configure console output
    if TQDM and show_progress:
        console = TqdmHandler()
    else:
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

    # Warn if using old Python version
    if python_version() < '3.4':
        logger.error("Python version %s is unsupported. "
                     "Please use Python 3.4+ instead. "
                     "Proceed at your own risk!")


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
