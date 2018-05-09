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
import sys

from adles.utils import read_json, handle_keyboard_interrupt


# TODO: cli args instead of filename
# e.g. "--vsphere-user" on all vsphere scripts, so ConfigArgParse can do it's thing globally
def make_vsphere(filename=None):
    """
    Creates a vSphere object using either a JSON file or by prompting the user.

    :param str filename: Name of JSON file with connection info
    :return: vSphere object
    :rtype: :class:`Vsphere`
    """
    from adles.vsphere.vsphere_class import Vsphere
    if filename is not None:
        info = read_json(filename)
        if info is None:
            sys.exit(1)
        return Vsphere(username=info.get("user"),
                       password=info.get("pass"),
                       hostname=info.get("host"),
                       port=info.get("port", 443),
                       datacenter=info.get("datacenter"),
                       datastore=info.get("datastore"))
    else:
        logging.info("Enter information to connect to the vSphere environment")
        datacenter = input("Datacenter  : ")
        datastore = input("Datastore   : ")
        return Vsphere(datacenter=datacenter, datastore=datastore)


@handle_keyboard_interrupt
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
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("Invalid default answer: '%s'" % default)

    while True:
        choice = str(input(question + prompt)).lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            print("Please respond with 'yes' or 'no' or 'y' or 'n'")


@handle_keyboard_interrupt
def default_prompt(prompt, default=None):
    """
    Prompt the user for input. If they press enter, return the default.

    :param str prompt: Prompt to display to user (do not include default value)
    :param str default: Default return value
    :return: Value entered or default
    :rtype: str or None
    """
    value = str(input(prompt + " [default: %s]: " % str(default)))
    return default if value == '' else value


@handle_keyboard_interrupt
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
        item_name = str(input(prompt))
        item = func(item_name)
        if item:
            logging.info("Found %s: %s", obj_name, item.name)
            return item, item_name
        else:
            print("Couldn't find a %s with name %s. Perhaps try another? "
                  % (obj_name, item_name))


def resolve_path(server, thing, prompt=""):
    """
    This is a hacked together script utility to get folders or VMs.

    :param server: Vsphere instance
    :type server: :class:`Vsphere`
    :param str thing: String name of thing to get (folder | vm)
    :param str prompt: Message to display
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