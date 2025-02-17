# Copyright 2021 IBM Corp. All Rights Reserved.
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
End2end tests for capacity groups (on CPCs in DPM mode).

These tests do not change any existing capacity groups, but create, modify and
delete test capacity groups.
"""

from __future__ import absolute_import, print_function

import warnings
import pytest
from requests.packages import urllib3

import zhmcclient
# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils import hmc_definition, hmc_session  # noqa: F401, E501
from zhmcclient.testutils import dpm_mode_cpcs  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import

from .utils import pick_test_resources, runtest_find_list, TEST_PREFIX, \
    skip_warn

urllib3.disable_warnings()

# Properties in minimalistic CapacityGroup objects (e.g. find_by_name())
CAPGRP_MINIMAL_PROPS = ['element-uri', 'name']

# Properties in CapacityGroup objects returned by list() without full props
CAPGRP_LIST_PROPS = ['element-uri', 'name']

# Properties whose values can change between retrievals of CapacityGroup objects
CAPGRP_VOLATILE_PROPS = []


def test_capgrp_find_list(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test list(), find(), findall().
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled

        session = cpc.manager.session
        hd = session.hmc_definition

        # Pick the capacity groups to test with
        capgrp_list = cpc.capacity_groups.list()
        if not capgrp_list:
            skip_warn("No capacity groups defined on CPC {c} managed by "
                      "HMC {h}".format(c=cpc.name, h=hd.host))
        capgrp_list = pick_test_resources(capgrp_list)

        for capgrp in capgrp_list:
            print("Testing on CPC {c} with capacity group {g!r}".
                  format(c=cpc.name, g=capgrp.name))
            runtest_find_list(
                session, cpc.capacity_groups, capgrp.name, 'name',
                'element-uri', CAPGRP_VOLATILE_PROPS, CAPGRP_MINIMAL_PROPS,
                CAPGRP_LIST_PROPS)


def test_capgrp_crud(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test create, read, update and delete a capacity group.
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled

        print("Testing on CPC {c}".format(c=cpc.name))

        capgrp_name = TEST_PREFIX + ' test_capgrp_crud capgrp1'
        capgrp_name_new = capgrp_name + ' new'

        # Ensure a clean starting point for this test
        try:
            capgrp = cpc.capacity_groups.find(name=capgrp_name)
        except zhmcclient.NotFound:
            pass
        else:
            warnings.warn(
                "Deleting test capacity group from previous run: {p!r} "
                "on CPC {c}".
                format(p=capgrp_name, c=cpc.name), UserWarning)
            capgrp.delete()
        try:
            capgrp = cpc.capacity_groups.find(name=capgrp_name_new)
        except zhmcclient.NotFound:
            pass
        else:
            warnings.warn(
                "Deleting test capacity group from previous run: {p!r} "
                "on CPC {c}".
                format(p=capgrp_name_new, c=cpc.name), UserWarning)
            capgrp.delete()

        # Test creating the capacity group

        capgrp_input_props = {
            'name': capgrp_name,
            'description': 'Test capacity group for zhmcclient end2end tests',
            'absolute-ifl-proc-cap': 1.0,
        }
        capgrp_auto_props = {
            'capping-enabled': True,
        }

        # The code to be tested
        capgrp = cpc.capacity_groups.create(capgrp_input_props)

        for pn, exp_value in capgrp_input_props.items():
            assert capgrp.properties[pn] == exp_value, \
                "Unexpected value for property {!r}".format(pn)
        capgrp.pull_full_properties()
        for pn, exp_value in capgrp_input_props.items():
            assert capgrp.properties[pn] == exp_value, \
                "Unexpected value for property {!r}".format(pn)
        for pn, exp_value in capgrp_auto_props.items():
            assert capgrp.properties[pn] == exp_value, \
                "Unexpected value for property {!r}".format(pn)

        # Test updating a property of the capacity group

        new_desc = "Updated capacity group description."

        # The code to be tested
        capgrp.update_properties(dict(description=new_desc))

        assert capgrp.properties['description'] == new_desc
        capgrp.pull_full_properties()
        assert capgrp.properties['description'] == new_desc

        # Test renaming the capacity group

        # The code to be tested
        capgrp.update_properties(dict(name=capgrp_name_new))

        assert capgrp.properties['name'] == capgrp_name_new
        capgrp.pull_full_properties()
        assert capgrp.properties['name'] == capgrp_name_new
        with pytest.raises(zhmcclient.NotFound):
            cpc.capacity_groups.find(name=capgrp_name)

        # Test deleting the capacity group

        # The code to be tested
        capgrp.delete()

        with pytest.raises(zhmcclient.NotFound):
            cpc.capacity_groups.find(name=capgrp_name_new)
