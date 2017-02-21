#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from automation.utils import read_json, prompt_y_n_question
from automation.vsphere.vsphere import vSphere
from getpass import getpass


def make_vsphere(filename=None):
    """
    Creates a vSphere object using either a JSON file or by prompting the user for input
    :param filename: (Optional) Name of JSON file with information needed [default: None]
    :return: vSphere object
    """
    if filename:
        info = read_json(filename)
        return vSphere(datacenter=info["datacenter"], username=info["username"], password=info["password"],
                       hostname=info["hostname"], port=info["port"], datastore=info["datastore"])
    else:
        print("Enter information to connect to vSphere environment")
        host = input("Hostname: ")
        port = int(input("Port: "))
        user = input("Username: ")
        pswd = getpass("Password: ")
        datacenter = input("vSphere Datacenter: ")
        if prompt_y_n_question("Would you like to specify the datastore used "):
            datastore = input("vSphere Datastore: ")
        else:
            datastore = None
        return vSphere(datacenter=datacenter, username=user, password=pswd,
                       hostname=host, port=port, datastore=datastore)


def warning():
    """ Prints a warning prompt. """
    print("\nYou run this script at your own risk. If you break something, it's on YOU. "
          "\nIf you're paranoid, please read the code, and perhaps improve it =)\n")


def user_input(prompt, obj_name, func):
    """
    Continually bothers a user for input until we get what we want from them (mehehe)
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
            print("Couldn't find a {} with name {}. Perhaps try another? ".format(obj_name, item_name))
    return item, item_name
