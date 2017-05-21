#!/usr/bin/env python
# Copyright 2016 IBM Corp. All Rights Reserved.
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
Tests for time statistics (`_timestats` module).
"""

from __future__ import absolute_import, print_function

import time
import unittest

from zhmcclient import TimeStatsKeeper, TimeStats


PRINT_HEADER = \
    "Time statistics (times in seconds):\n" \
    "Count  Average  Minimum  Maximum  Operation name"

PRINT_HEADER_DISABLED = \
    "Time statistics (times in seconds):\n" \
    "Disabled."


def time_abs_delta(t1, t2):
    """
    Return the positive difference between two float values.
    """
    return abs(t1 - t2)


def measure(stats, duration):
    """
    Return the measured duration of one begin/end cycle of a TimeStats object
    of a given intended duration.  The runtime behavior may be that the actual
    duration is larger than the intended duration, therefore we need to measure
    the actual duration.
    """
    begin = time.time()
    stats.begin()
    time.sleep(duration)
    stats.end()
    end = time.time()
    return end - begin


class TimeStatsTests(unittest.TestCase):
    """All tests for TimeStatsKeeper and TimeStats."""

    def test_enabling(self):
        """Test enabling and disabling."""

        keeper = TimeStatsKeeper()

        self.assertFalse(keeper.enabled,
                         "Verify that initial state is disabled")

        keeper.disable()
        self.assertFalse(keeper.enabled,
                         "Verify that disabling a disabled keeper works")

        keeper.enable()
        self.assertTrue(keeper.enabled,
                        "Verify that enabling a disabled keeper works")

        keeper.enable()
        self.assertTrue(keeper.enabled,
                        "Verify that enabling an enabled keeper works")

        keeper.disable()
        self.assertFalse(keeper.enabled,
                         "Verify that disabling an enabled keeper works")

    def test_get(self):
        """Test getting time statistics."""

        keeper = TimeStatsKeeper()
        snapshot_length = len(keeper.snapshot())
        self.assertEqual(snapshot_length, 0,
                         "Verify that initial state has no time statistics. "
                         "Actual number = %d" % snapshot_length)

        stats = keeper.get_stats('foo')
        snapshot_length = len(keeper.snapshot())
        self.assertEqual(snapshot_length, 0,
                         "Verify that getting a new stats with a disabled "
                         "keeper results in no time statistics. "
                         "Actual number = %d" % snapshot_length)
        self.assertEqual(stats.keeper, keeper)
        self.assertEqual(stats.name, "disabled")  # stats for disabled keeper
        self.assertEqual(stats.count, 0)
        self.assertEqual(stats.avg_time, 0)
        self.assertEqual(stats.min_time, float('inf'))
        self.assertEqual(stats.max_time, 0)

        keeper.enable()

        stats = keeper.get_stats('foo')
        snapshot_length = len(keeper.snapshot())
        self.assertEqual(snapshot_length, 1,
                         "Verify that getting a new stats with an enabled "
                         "keeper results in one time statistics. "
                         "Actual number = %d" % snapshot_length)

        self.assertEqual(stats.keeper, keeper)
        self.assertEqual(stats.name, 'foo')
        self.assertEqual(stats.count, 0)
        self.assertEqual(stats.avg_time, 0)
        self.assertEqual(stats.min_time, float('inf'))
        self.assertEqual(stats.max_time, 0)

        keeper.get_stats('foo')
        snapshot_length = len(keeper.snapshot())
        self.assertEqual(snapshot_length, 1,
                         "Verify that getting an existing stats with an "
                         "enabled keeper results in the same number of time "
                         "statistics. "
                         "Actual number = %d" % snapshot_length)

    def test_measure_enabled(self):
        """Test measuring time with enabled keeper."""

        keeper = TimeStatsKeeper()
        keeper.enable()

        # TimeStatsKeeper on Windows has only a precision of 1/60 sec
        duration = 1.6
        delta = duration / 10.0

        stats = keeper.get_stats('foo')
        dur = measure(stats, duration)

        for _, stats in keeper.snapshot():
            self.assertEqual(stats.count, 1)
            self.assertLess(time_abs_delta(stats.avg_time, dur), delta,
                            "avg time: actual: %f, expected: %f, delta: %f" %
                            (stats.avg_time, dur, delta))
            self.assertLess(time_abs_delta(stats.min_time, dur), delta,
                            "min time: actual: %f, expected: %f, delta: %f" %
                            (stats.min_time, dur, delta))
            self.assertLess(time_abs_delta(stats.max_time, dur), delta,
                            "max time: actual: %f, expected: %f, delta: %f" %
                            (stats.max_time, dur, delta))

        stats.reset()
        self.assertEqual(stats.count, 0)
        self.assertEqual(stats.avg_time, 0)
        self.assertEqual(stats.min_time, float('inf'))
        self.assertEqual(stats.max_time, 0)

    def test_measure_disabled(self):
        """Test measuring time with disabled keeper."""

        keeper = TimeStatsKeeper()

        duration = 0.2

        stats = keeper.get_stats('foo')
        self.assertEqual(stats.name, 'disabled')

        stats.begin()
        time.sleep(duration)
        stats.end()

        for _, stats in keeper.snapshot():
            self.assertEqual(stats.count, 0)
            self.assertEqual(stats.avg_time, 0)
            self.assertEqual(stats.min_time, float('inf'))
            self.assertEqual(stats.max_time, 0)

    def test_snapshot(self):
        """Test that snapshot() takes a stable snapshot."""

        keeper = TimeStatsKeeper()
        keeper.enable()

        duration = 0.2

        stats = keeper.get_stats('foo')

        # produce a first data item
        stats.begin()
        time.sleep(duration)
        stats.end()

        # take the snapshot
        snapshot = keeper.snapshot()

        # produce a second data item
        stats.begin()
        time.sleep(duration)
        stats.end()

        # verify that only the first data item is in the snapshot
        for _, snap_stats in snapshot:
            self.assertEqual(snap_stats.count, 1)

        # verify that both data items are in the original stats object
        self.assertEqual(stats.count, 2)

    def test_measure_avg_min_max(self):
        """Test measuring avg min max values."""

        keeper = TimeStatsKeeper()
        keeper.enable()

        # TimeStatsKeeper on Windows has only a precision of 1/60 sec
        durations = (0.6, 1.2, 1.5)
        delta = 0.08
        count = len(durations)

        stats = keeper.get_stats('foo')
        m_durations = []
        for duration in durations:
            m_durations.append(measure(stats, duration))

        min_dur = min(m_durations)
        max_dur = max(m_durations)
        avg_dur = sum(m_durations) / float(count)

        for _, stats in keeper.snapshot():
            self.assertEqual(stats.count, 3)
            self.assertLess(time_abs_delta(stats.avg_time, avg_dur), delta,
                            "avg time: actual: %f, expected: %f, delta: %f" %
                            (stats.avg_time, avg_dur, delta))
            self.assertLess(time_abs_delta(stats.min_time, min_dur), delta,
                            "min time: actual: %f, expected: %f, delta: %f" %
                            (stats.min_time, min_dur, delta))
            self.assertLess(time_abs_delta(stats.max_time, max_dur), delta,
                            "max time: actual: %f, expected: %f, delta: %f" %
                            (stats.max_time, max_dur, delta))

    def test_only_end(self):
        """Test that invoking end() before begin() has ever been called raises
        a RuntimeError exception."""

        keeper = TimeStatsKeeper()
        keeper.enable()
        stats = keeper.get_stats('foo')

        with self.assertRaises(RuntimeError):
            stats.end()

    def test_end_after_end(self):
        """Test that invoking end() after a begin/end sequence raises
        a RuntimeError exception."""

        keeper = TimeStatsKeeper()
        keeper.enable()
        stats = keeper.get_stats('foo')

        stats.begin()
        time.sleep(0.01)
        stats.end()

        with self.assertRaises(RuntimeError):
            stats.end()

    def test_str_empty(self):
        """Test TimestatsKeeper.__str__() for an empty enabled keeper."""

        keeper = TimeStatsKeeper()
        keeper.enable()
        s = str(keeper)
        self.assertEqual(s, PRINT_HEADER)

    def test_str_disabled(self):
        """Test TimestatsKeeper.__str__() for a disabled keeper."""

        keeper = TimeStatsKeeper()
        s = str(keeper)
        self.assertEqual(s, PRINT_HEADER_DISABLED)

    def test_str_one(self):
        """Test TimestatsKeeper.__str__() for an enabled keeper with one data
        item."""

        keeper = TimeStatsKeeper()
        keeper.enable()

        duration = 0.1

        stats = keeper.get_stats('foo')

        # produce a data item
        stats.begin()
        time.sleep(duration)
        stats.end()

        s = str(keeper)
        self.assertTrue(s.startswith(PRINT_HEADER),
                        "Unexpected str(keeper): %r" % s)
        num_lines = len(s.split('\n'))
        self.assertEqual(num_lines, 3,
                         "Unexpected str(keeper): %r" % s)

    def test_ts_str(self):
        """Test Timestats.__str__()."""

        keeper = TimeStatsKeeper()
        timestats = TimeStats(keeper, "foo")

        s = str(timestats)
        self.assertTrue(s.startswith("TimeStats:"),
                        "Unexpected str(timestats): %r" % s)
        num_lines = len(s.split('\n'))
        self.assertEqual(num_lines, 1,
                         "Unexpected str(timestats): %r" % s)


if __name__ == '__main__':
    unittest.main()
