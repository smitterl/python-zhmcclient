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
End2end tests for adapters (on CPCs in DPM mode).

These tests do not change any existing adapters, but create, modify
and delete Hipersocket adapters.
"""

from __future__ import absolute_import, print_function

import uuid
import warnings
import pytest
from requests.packages import urllib3

import zhmcclient
# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils import hmc_definition, hmc_session  # noqa: F401, E501
from zhmcclient.testutils import dpm_mode_cpcs  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import

from .utils import pick_test_resources, runtest_find_list, TEST_PREFIX, \
    skip_warn, standard_partition_props

urllib3.disable_warnings()

# Properties in minimalistic Adapter objects (e.g. find_by_name())
ADAPTER_MINIMAL_PROPS = ['object-uri', 'name']

# Properties in Adapter objects returned by list() without full props
ADAPTER_LIST_PROPS = ['object-uri', 'name', 'adapter-id', 'adapter-family',
                      'type', 'status']

# Properties whose values can change between retrievals of Adapter objects
ADAPTER_VOLATILE_PROPS = []


def test_adapter_find_list(dpm_mode_cpcs):  # noqa: F811
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

        # Pick the adapters to test with
        adapter_list = cpc.adapters.list()
        if not adapter_list:
            skip_warn("No adapters on CPC {c} managed by HMC {h}".
                      format(c=cpc.name, h=hd.host))
        adapter_list = pick_test_resources(adapter_list)

        for adapter in adapter_list:
            print("Testing on CPC {c} with adapter {a!r}".
                  format(c=cpc.name, a=adapter.name))
            runtest_find_list(
                session, cpc.adapters, adapter.name, 'name', 'object-uri',
                ADAPTER_VOLATILE_PROPS, ADAPTER_MINIMAL_PROPS,
                ADAPTER_LIST_PROPS)


def test_adapter_hs_crud(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test create, read, update and delete a Hipersocket adapter.
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled

        print("Testing on CPC {c}".format(c=cpc.name))

        adapter_name = TEST_PREFIX + ' test_adapter_crud adapter1'
        adapter_name_new = adapter_name + ' new'

        # Ensure a clean starting point for this test
        try:
            adapter = cpc.adapters.find(name=adapter_name)
        except zhmcclient.NotFound:
            pass
        else:
            warnings.warn(
                "Deleting test Hipersocket adapter from previous run: "
                "{a!r} on CPC {c}".
                format(a=adapter_name, c=cpc.name), UserWarning)
            adapter.delete()
        try:
            adapter = cpc.adapters.find(name=adapter_name_new)
        except zhmcclient.NotFound:
            pass
        else:
            warnings.warn(
                "Deleting test Hipersocket adapter from previous run: "
                "{a!r} on CPC {c}".
                format(a=adapter_name_new, c=cpc.name), UserWarning)
            adapter.delete()

        # Create a Hipersocket adapter
        adapter_input_props = {
            'name': adapter_name,
            'description': 'Test adapter for zhmcclient end2end tests',
        }
        adapter_auto_props = {
            'type': 'hipersockets',
        }

        # The code to be tested
        adapter = cpc.adapters.create_hipersocket(adapter_input_props)

        for pn, exp_value in adapter_input_props.items():
            assert adapter.properties[pn] == exp_value, \
                "Unexpected value for property {!r}".format(pn)
        adapter.pull_full_properties()
        for pn, exp_value in adapter_input_props.items():
            assert adapter.properties[pn] == exp_value, \
                "Unexpected value for property {!r}".format(pn)
        for pn, exp_value in adapter_auto_props.items():
            assert adapter.properties[pn] == exp_value, \
                "Unexpected value for property {!r}".format(pn)

        # Test updating a property of the adapter

        new_desc = "Updated adapter description."

        # The code to be tested
        adapter.update_properties(dict(description=new_desc))

        assert adapter.properties['description'] == new_desc
        adapter.pull_full_properties()
        assert adapter.properties['description'] == new_desc

        # Test renaming the adapter

        # The code to be tested
        adapter.update_properties(dict(name=adapter_name_new))

        assert adapter.properties['name'] == adapter_name_new
        adapter.pull_full_properties()
        assert adapter.properties['name'] == adapter_name_new
        with pytest.raises(zhmcclient.NotFound):
            cpc.adapters.find(name=adapter_name)

        # Test deleting the adapter

        # The code to be tested
        adapter.delete()

        with pytest.raises(zhmcclient.NotFound):
            cpc.adapters.find(name=adapter_name_new)


def test_adapter_list_assigned_part(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test Adapter.list_assigned_partitions().
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled

        required_families = [
            'hipersockets',
            'osa',
            'roce',
            'cna',
            'ficon',
            'accelerator',
            'crypto',
            'nvme',
            'coupling',
            'ism',
            'zhyperlink',
        ]
        family_adapters = {}
        for family in required_families:
            family_adapters[family] = []

        # List all adapters on the CPC and group by family
        adapter_list = cpc.adapters.list()
        for adapter in adapter_list:
            family = adapter.get_property('adapter-family')
            if family not in family_adapters:
                warnings.warn(
                    "Ignoring adapter {a!r} on CPC {c} with an unknown "
                    "family: '{f}'".
                    format(c=cpc.name, a=adapter.name, f=family),
                    UserWarning)
                continue
            if adapter.get_property('type') == 'osm':
                # Skip OSM adapters since they cannot be assigned to partitions
                continue
            family_adapters[family].append(adapter)

        tmp_part = None
        try:

            # Create a temporary partition for test purposes
            part_name = "{}_{}".format(TEST_PREFIX, uuid.uuid4().hex)
            part_props = standard_partition_props(cpc, part_name)
            tmp_part = cpc.partitions.create(part_props)

            for family, all_adapters in family_adapters.items():
                if not all_adapters:
                    warnings.warn(
                        "CPC {c} has no adapters of family '{f}'".
                        format(c=cpc.name, f=family), UserWarning)
                    continue

                if family in ('hipersockets', 'osa'):

                    test_adapters = pick_test_resources(all_adapters)
                    for test_adapter in test_adapters:
                        print("Testing on CPC {c} with adapter {a!r} "
                              "(family '{f}')".
                              format(c=cpc.name, a=test_adapter.name, f=family))

                        # The method to be tested
                        before_parts = test_adapter.list_assigned_partitions()

                        # Find the virtual switch for the test adapter
                        filter_args = {'backing-adapter-uri': test_adapter.uri}
                        vswitches = cpc.virtual_switches.list(
                            filter_args=filter_args)
                        assert len(vswitches) >= 1
                        vswitch = vswitches[0]

                        # Create a NIC in the temporary partition
                        nic_name = "{}_{}".format(family, uuid.uuid4().hex)
                        nic_props = {
                            'name': nic_name,
                            'virtual-switch-uri': vswitch.uri,
                        }
                        tmp_part.nics.create(nic_props)

                        # The method to be tested
                        after_parts = test_adapter.list_assigned_partitions()

                        before_uris = [p.uri for p in before_parts]
                        new_parts = []
                        for part in after_parts:
                            if part.uri not in before_uris:
                                new_parts.append(part)

                        assert len(new_parts) == 1
                        new_part = new_parts[0]
                        assert new_part.uri == tmp_part.uri

                elif family in ('roce', 'cna'):

                    test_adapters = pick_test_resources(all_adapters)
                    for test_adapter in test_adapters:
                        print("Testing on CPC {c} with adapter {a!r} "
                              "(family '{f}')".
                              format(c=cpc.name, a=test_adapter.name, f=family))

                        # The method to be tested
                        before_parts = test_adapter.list_assigned_partitions()

                        test_port = test_adapter.ports.list()[0]

                        # Create a NIC in the temporary partition
                        nic_name = "{}_{}".format(family, uuid.uuid4().hex)
                        nic_props = {
                            'name': nic_name,
                            'network-adapter-port-uri': test_port.uri,
                        }
                        tmp_part.nics.create(nic_props)

                        # The method to be tested
                        after_parts = test_adapter.list_assigned_partitions()

                        before_uris = [p.uri for p in before_parts]
                        new_parts = []
                        for part in after_parts:
                            if part.uri not in before_uris:
                                new_parts.append(part)

                        assert len(new_parts) == 1
                        new_part = new_parts[0]
                        assert new_part.uri == tmp_part.uri

                elif family == 'ficon':

                    # Assigning storage adapters to partitions is complex,
                    # so we search for a storage adapter that is already
                    # assigned to a partition.

                    found_test_adapter = False
                    for test_adapter in all_adapters:

                        if test_adapter.get_property('type') != 'fcp':
                            # This test works only for FCP adapters
                            continue

                        # The method to be tested
                        before_parts = test_adapter.list_assigned_partitions()

                        if len(before_parts) == 0:
                            continue

                        found_test_adapter = True
                        print("Testing on CPC {c} with FCP adapter {a!r} "
                              "(family '{f}')".
                              format(c=cpc.name, a=test_adapter.name, f=family))

                        found_adapters = []
                        for part in before_parts:
                            sgroups = part.list_attached_storage_groups()
                            for sg in sgroups:
                                vsrs = sg.virtual_storage_resources.list()
                                for vsr in vsrs:
                                    port = vsr.adapter_port
                                    adapter = port.manager.parent
                                    if adapter.uri == test_adapter.uri:
                                        found_adapters.append(adapter)

                        assert len(found_adapters) >= 1
                        break

                    if not found_test_adapter:
                        warnings.warn(
                            "CPC {c} has no FCP adapter with that is assigned "
                            "to any partition - cannot test FCP adapters".
                            format(c=cpc.name), UserWarning)

                elif family == 'accelerator':

                    test_adapters = pick_test_resources(all_adapters)
                    for test_adapter in test_adapters:
                        print("Testing on CPC {c} with adapter {a!r} "
                              "(family '{f}')".
                              format(c=cpc.name, a=test_adapter.name, f=family))

                        # The method to be tested
                        before_parts = test_adapter.list_assigned_partitions()

                        # Create a VF in the temporary partition
                        vf_name = "{}_{}".format(family, uuid.uuid4().hex)
                        vf_props = {
                            'name': vf_name,
                            'adapter-uri': test_adapter.uri,
                        }
                        tmp_part.virtual_functions.create(vf_props)

                        # The method to be tested
                        after_parts = test_adapter.list_assigned_partitions()

                        before_uris = [p.uri for p in before_parts]
                        new_parts = []
                        for part in after_parts:
                            if part.uri not in before_uris:
                                new_parts.append(part)

                        assert len(new_parts) == 1
                        new_part = new_parts[0]
                        assert new_part.uri == tmp_part.uri

                elif family == 'crypto':

                    # Assigning crypto adapters to partitions is complex,
                    # so we search for a crypto adapter that is already
                    # assigned to a partition.

                    found_test_adapter = False
                    for test_adapter in all_adapters:

                        # The method to be tested
                        before_parts = test_adapter.list_assigned_partitions()

                        if len(before_parts) == 0:
                            continue

                        found_test_adapter = True
                        print("Testing on CPC {c} with adapter {a!r} "
                              "(family '{f}')".
                              format(c=cpc.name, a=test_adapter.name, f=family))

                        found_adapter_uris = []
                        for part in before_parts:
                            crypto_config = part.get_property(
                                'crypto-configuration')
                            if crypto_config is None:
                                continue
                            adapter_uris = crypto_config['crypto-adapter-uris']
                            for adapter_uri in adapter_uris:
                                if adapter_uri == test_adapter.uri:
                                    found_adapter_uris.append(adapter_uri)

                        assert len(found_adapter_uris) >= 1
                        break

                    if not found_test_adapter:
                        warnings.warn(
                            "CPC {c} has no Crypto adapter that is assigned "
                            "to any partition - cannot test Crypto adapters".
                            format(c=cpc.name), UserWarning)

                elif family == 'nvme':
                    print("TODO: Implement test for family {}".format(family))

                elif family == 'coupling':
                    print("TODO: Implement test for family {}".format(family))

                elif family == 'ism':
                    print("TODO: Implement test for family {}".format(family))

                elif family == 'zhyperlink':
                    print("TODO: Implement test for family {}".format(family))

        finally:
            # Cleanup
            if tmp_part:
                tmp_part.delete()
