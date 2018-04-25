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


class Group:
    """ Manages a group of users that has been loaded from a specification """

    def __init__(self, name, group, instance=None):
        """
        :param str name: Name of the group
        :param dict group: Dict specification of the group
        :param int instance: Instance number of a template group
        """
        self._log = logging.getLogger('Group')
        self._log.debug("Initializing Group '%s'", name)

        if instance:
            self.is_template = True
            self.instance = instance
        else:
            self.is_template = False

        # !!! NOTE: ad-groups must be handled externally by caller !!!
        if "ad-group" in group:
            group_type = "ad"
            self.ad_group = group["ad-group"]
            users = []
            if instance:  # Template groups
                # This is the " X" in the spec
                self.ad_group += " " + str(instance)

        elif "filename" in group:
            from adles.utils import read_json
            group_type = "standard"
            if instance:    # Template group
                users = [(user, pw)
                         for user, pw in read_json(group["filename"])
                         [str(instance)].items()]
            else:           # Standard group
                users = [(user, pw)
                         for user, pw in read_json(group["filename"]).items()]

        elif "user-list" in group:
            group_type = "standard"
            users = group["user-list"]

        else:
            self._log.error("Invalid group dict for group '%s': %s",
                            name, str(group))
            raise Exception()

        self.group_type = group_type
        self.users = users
        self.size = int(len(self.users))
        self.name = str(name)
        self._log.debug("Finished initializing Group '%s' with %d users",
                        self.name, self.size)

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return self.name == other.name and self.users == other.users and \
               self.group_type == other.group_type

    def __ne__(self, other):
        return not self.__eq__(other)


def get_ad_groups(groups):
    """
    Extracts Active Directory-type groups from a dict of groups.

    :param dict groups: Dict of groups and lists of groups
    :return: List of AD groups extracted
    :rtype: list(:class:`Group`)
    """
    ad_groups = []
    for _, group in groups.items():  # Ignore the group name, nab the group
        if isinstance(group, list):
            for i in group:
                if isinstance(i, Group):
                    if i.group_type == "ad":
                        ad_groups.append(i)
        elif isinstance(group, Group):
            if group.group_type == "ad":
                ad_groups.append(group)
        else:
            logging.error("Invalid type '%s' for a group in get_ad_groups: %s",
                          type(group).__name__, str(group))
    return ad_groups
