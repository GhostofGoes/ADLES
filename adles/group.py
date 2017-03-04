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


class Group:
    """ Manages a group of users that has been loaded from a specification """

    def __init__(self, group):
        """ :param group: Dict specification of a group """

        if type(group) != dict:
            logging.error("Class Group must be initialized with a dict, not %s", str(type(group)))
            raise Exception()

        logging.debug("Initializing Group %s", str(group[0]))
        if "ad-group" in group:
            self.users = None  # TODO: implement active directory group retrieval...will need to get AD server info
        elif "filename" in group:
            from adles.utils import read_json
            self.users = [(user, pw) for user, pw in read_json(group["filename"]).items()]
        elif "user-list" in group:
            self.users = group["user-list"]
        else:
            logging.error("Invalid group: %s", str(group))
            raise Exception()

        self.size = int(len(self.users))
