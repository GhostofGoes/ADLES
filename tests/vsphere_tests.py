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

import unittest

from adles.vsphere.vsphere_class import Vsphere
import adles.vsphere.folder_utils as futils
import adles.vsphere.network_utils as nutils
import adles.vsphere.vm_utils as vm_utils
import adles.vsphere.vsphere_utils as vutils
from adles.utils import read_json


class TestVsphere(unittest.TestCase):

    def setUp(self):
        # TODO: make test logins.json file and test user-account
        # TODO: Use VCR to mock these
        info = read_json("test-logins.json")
        self.server = Vsphere(**info)  # Abusing keyword args
        # Create test VMs
        self.folder = self.server.create_folder("test_folder")
        self.template = None
        self.vm = None

    def tearDown(self):
        # Destroy test VMs (unless we are using VCR)
        pass

if __name__ == '__main__':
    unittest.main()
