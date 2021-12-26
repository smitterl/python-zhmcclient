# Copyright 2017-2021 IBM Corp. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
End2end tests for partitions (on CPCs in DPM mode).

These tests do not change any existing partitions, but create, modify and delete
test partitions.
"""

from __future__ import absolute_import, print_function

import warnings
import pytest
from requests.packages import urllib3

import zhmcclient
# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils.hmc_definition_fixtures import hmc_definition, hmc_session  # noqa: F401, E501
from zhmcclient.testutils.cpc_fixtures import dpm_mode_cpcs  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import

from .utils import runtest_find_list, TEST_PREFIX

urllib3.disable_warnings()

# Properties in minimalistic Partition objects (e.g. find_by_name())
PART_MINIMAL_PROPS = ['object-uri', 'name']

# Properties in Partition objects returned by list() without full props
PART_LIST_PROPS = ['object-uri', 'name', 'status', 'type']

# Properties whose values can change between retrievals of Partition objects
PART_VOLATILE_PROPS = []


def test_part_find_list(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test list(), find(), findall().
    """
    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled
        print("Testing on CPC {} (DPM mode)".format(cpc.name))

        session = cpc.manager.session

        # Pick a partition
        part_list = cpc.partitions.list()
        assert len(part_list) >= 1
        part = part_list[-1]  # Pick the last one returned

        runtest_find_list(
            session, cpc.partitions, part.name, 'name', 'status',
            PART_VOLATILE_PROPS, PART_MINIMAL_PROPS, PART_LIST_PROPS)


def test_part_crud(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test create, read, update and delete a partition.
    """
    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled
        print("Testing on CPC {} (DPM mode)".format(cpc.name))

        part_name = TEST_PREFIX + '.test_part_crud.part1'

        # Ensure a clean starting point for this test
        try:
            part = cpc.partitions.find(name=part_name)
        except zhmcclient.NotFound:
            pass
        else:
            warnings.warn(
                "Deleting test partition from previous run: '{p}' on CPC '{c}'".
                format(p=part_name, c=cpc.name), UserWarning)
            status = part.get_property('status')
            if status != 'stopped':
                part.stop()
            part.delete()

        # Test creating the partition

        part_input_props = {
            'name': part_name,
            'description': 'Test partition for zhmcclient end2end tests',
            'ifl-processors': 2,
            'initial-memory': 1024,
            'maximum-memory': 2048,
            'processor-mode': 'shared',  # used for filtering
            'type': 'linux',  # used for filtering
        }
        part_auto_props = {
            'status': 'stopped',
        }

        # The code to be tested
        part = cpc.partitions.create(part_input_props)

        for pn, exp_value in part_input_props.items():
            assert part.properties[pn] == exp_value, \
                "Unexpected value for property {!r}".format(pn)
        part.pull_full_properties()
        for pn, exp_value in part_input_props.items():
            assert part.properties[pn] == exp_value, \
                "Unexpected value for property {!r}".format(pn)
        for pn, exp_value in part_auto_props.items():
            assert part.properties[pn] == exp_value, \
                "Unexpected value for property {!r}".format(pn)

        # Test updating a property of the partition

        new_desc = "Updated partition description."

        # The code to be tested
        part.update_properties(dict(description=new_desc))

        assert part.properties['description'] == new_desc
        part.pull_full_properties()
        assert part.properties['description'] == new_desc

        # Test deleting the partition

        # The code to be tested
        part.delete()

        with pytest.raises(zhmcclient.NotFound):
            cpc.partitions.find(name=part_name)
