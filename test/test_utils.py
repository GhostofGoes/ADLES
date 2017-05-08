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


def test_sizeof_fmt():
    from adles.utils import sizeof_fmt
    
    assert sizeof_fmt(0) == '0.0bytes'
    assert sizeof_fmt(10.12345) == '10.1bytes'
    assert sizeof_fmt(10.19) == '10.2bytes'
    assert sizeof_fmt(1023) == '1023.0bytes'
    assert sizeof_fmt(1024) == '1.0KB'
    assert sizeof_fmt(10000) == '9.8KB'
    assert sizeof_fmt(1000000000) == '953.7MB'
    assert sizeof_fmt(100000000000000000) == '90949.5TB'


def test_pad():
    from adles.utils import pad

    assert pad(0) == "00"
    assert pad(5) == "05"
    assert pad(9, 3) == "009"
    assert pad(value=10, length=4) == "0010"
    assert pad(50, 5) == "00050"


def test_split_path():
    from adles.utils import split_path

    assert split_path('/path/To/A/file') == (['path', 'To', 'A'], 'file')
    assert split_path('') == ([''], '')
    assert split_path('/') == (['', ''], '')


def test_get_vlan():
    from adles.utils import get_vlan

    assert get_vlan() >= 2000
    assert get_vlan() <= 4096


def test_read_json():
    from adles.utils import read_json

    assert isinstance(read_json('../users.json'), dict)
    assert read_json('lame.jpg') is None
