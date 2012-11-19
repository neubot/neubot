#!/usr/bin/env python

#
# Copyright (c) 2012
#     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#     and Simone Basso <bassosimone@gmail.com>
#
# This file is part of Neubot <http://www.neubot.org/>.
#
# Neubot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Neubot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Neubot.  If not, see <http://www.gnu.org/licenses/>.
#

''' Regression test for raw_analyze.py '''

import unittest
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot import raw_analyze

#
# We're accessing private methods of `raw_analyze` for testing and we don't
# maintain unittest, so we don't care about the number of methods.
#
# pylint: disable=W0212,R0904
#

class TestPreprocessResults(unittest.TestCase):
    ''' Regression tests for raw_analyze._preprocess_results() '''

    def test_empty(self):
        ''' Make sure it works for empty input '''
        self.assertEqual(list(raw_analyze._preprocess_results([], False)), [])

    def test_first_point(self):
        ''' Make sure that the first point interval is computed properly '''
        result = list(raw_analyze._preprocess_results([
                                                       (1234567890, 1440),
                                                       (1234567891, 1440),
                                                       (1234567892, 1440),
                                                      ],
                                                      False))
        self.assertEqual(result[0][1], 0)

    def test_merge_points(self):
        ''' Make sure that the points are correctly merged '''
        result = list(raw_analyze._preprocess_results([
                                                       (1234567890, 1440),
                                                       (1234567890, 1440),
                                                       (1234567892, 1440),
                                                       (1234567892, 1440),
                                                      ],
                                                      True))
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0][2], 2880)
        self.assertEqual(result[1][2], 2880)

    def test_nonmerge_points(self):
        ''' Make sure interval is zero when we don't merge points '''
        result = list(raw_analyze._preprocess_results([
                                                       (1234567890, 1440),
                                                       (1234567890, 1440),
                                                       (1234567892, 1440),
                                                       (1234567892, 1440),
                                                      ],
                                                      False))
        self.assertEqual(len(result), 4)
        self.assertEqual(result[1][1], 0.0)
        self.assertEqual(result[1][2], 1440)
        self.assertEqual(result[3][1], 0.0)
        self.assertEqual(result[3][2], 1440)

    def test_negative_interval(self):
        ''' Make sure we raise RuntimeError on negative interval '''
        generator = raw_analyze._preprocess_results([
                                                     (1234567890, 1440),
                                                     (1234567889, 1440)
                                                    ],
                                                    False)
        self.assertRaises(RuntimeError, list, generator)

    def test_functionality(self):
        ''' Make sure it produces a reasonable result for typical input '''
        result = list(raw_analyze._preprocess_results([
                                                       (1234567890, 1440),
                                                       (1234567891, 1440),
                                                       (1234567894, 1440),
                                                       (1234567894, 1440),
                                                       (1234567899, 1440),
                                                      ],
                                                      True))
        self.assertEqual(result, [
                                  (1234567890, 0, 1440),
                                  (1234567891, 1, 1440),
                                  (1234567894, 3, 2880),
                                  (1234567899, 5, 1440)
                                 ])
        # Same as above, but without merging points with equal ticks
        result = list(raw_analyze._preprocess_results([
                                                       (1234567890, 1440),
                                                       (1234567891, 1440),
                                                       (1234567894, 1440),
                                                       (1234567894, 1440),
                                                       (1234567899, 1440),
                                                      ],
                                                      False))
        self.assertEqual(result, [
                                  (1234567890, 0, 1440),
                                  (1234567891, 1, 1440),
                                  (1234567894, 3, 1440),
                                  (1234567894, 0, 1440),
                                  (1234567899, 5, 1440)
                                 ])

class TestComputeBottleneckCapacity(unittest.TestCase):
    ''' Regression tests for raw_analyze._compute_bottleneck_capacity() '''

    def test_empty(self):
        ''' Make sure it works for empty input '''
        self.assertEqual(raw_analyze._compute_bottleneck_capacity([], 1440),
          None)

    def test_ignore_big_mss(self):
        ''' Make sure we ignore samples bigger than one MSS '''
        self.assertEqual(raw_analyze._compute_bottleneck_capacity(
          [(1234567894, 3, 1441)], 1440), None)

    def test_ignore_small_mss(self):
        ''' Make sure we ignore samples <= than 1/2 MSS '''
        self.assertEqual(raw_analyze._compute_bottleneck_capacity(
          [(1234567894, 3, 720)], 1440), None)

    def test_percentile(self):
        ''' Garner confidence that we're not biases by rare events '''
        samples = [
                   (1234567893, 1, 1440),
                   (1234567894, 1, 1440),
                   (1234567895, 1, 1440),
                   (1234567896, 1, 1440),
                   (1234567196, 100, 1440),
                  ]
        self.assertEqual(raw_analyze._compute_bottleneck_capacity(
          samples, 1440), 1440)

    def test_float_division(self):
        ''' Make sure it deals gracefully with zero interval '''
        self.assertEqual(raw_analyze._compute_bottleneck_capacity(
          [(1234567894, 0, 1380)], 1440), None)

    def test_functionality(self):
        ''' Make sure it produces a reasonable result for typical input '''
        samples = [
                   (0.050997, 0.000000, 1440),
                   (0.052390, 0.001393, 1440),
                   (0.142646, 0.090256, 1440),
                   (0.145038, 0.002392, 1440),
                   (0.147341, 0.002303, 1440),
                   (0.196586, 0.049245, 1440),
                   (0.196947, 0.000361, 1440),
                   (0.199582, 0.002635, 1440),
                   (0.245488, 0.045906, 1440),
                   (0.247373, 0.001885, 1440),
                  ]
        capacity = raw_analyze._compute_bottleneck_capacity(samples, 1440)
        self.assertEqual(capacity, 602006.68896321068)

if __name__ == '__main__':
    unittest.main()
