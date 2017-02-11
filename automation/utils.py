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

from sys import stdout


# From: virtual_machine_power_cycle_and_question.py in pyvmomi-community-samples
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
        print(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            print("Please, respond with 'yes' or 'no' or 'y' or 'n'.")
