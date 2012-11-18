# neubot/raw_analyze.py

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

''' Analyze client side results '''

import collections
import logging

from neubot import percentile

def compute_bottleneck_capacity(vector, mss):
    ''' Compute bottleneck capacity using packet pair '''
    # Note: here we group points having equal ticks
    return _compute_bottleneck_capacity(_preprocess_results(vector, True), mss)

def _preprocess_results(vector, join_if_equal_ticks):
    ''' Normalize results to ease further processing '''
    index, prev = 0, -1.0
    while index < len(vector):
        ticks, bytez = vector[index]
        if prev < 0.0:
            prev = ticks
        interval = ticks - prev
        if interval < 0:
            raise RuntimeError('raw_analyze: negative time interval')
        index = index + 1
        while (join_if_equal_ticks and index < len(vector)
          and vector[index][0] == ticks):
            bytez += vector[index][1]
            index = index + 1
        yield ticks, interval, bytez
        prev = ticks

def _compute_bottleneck_capacity(vector, mss):
    ''' Compute bottleneck capacity using packet pair '''
    #
    # 1. We ignore samples != 1-MSS because they can be caused by rexmits or
    #    jitter.  We want, instead, to limit the analysis to samples related to
    #    a single segment;
    #
    # 2. when options are used, the actual size is slightly lower than the MSS
    #    read using getsockopt().  So, the check is not very precise.  This
    #    shouldn't be a problem, since we assume the sender is sending at full
    #    speed, so it should be sending mainly full-size segments;
    #
    # 3. we use the median, because the average can be more easily biased by
    #    outliars caused by rare events.
    #
    # XXX I'm not sure #1 is correct.  I should investigate.
    #
    samples = []
    half_mss = mss / 2
    for _, interval, bytez in vector:
        if half_mss < bytez <= mss and interval > 0:
            samples.append(bytez / interval)
    return percentile.median(samples)

def select_likely_rexmits(vector, rtt, mss):
    ''' Selects the likely-retransmission samples only '''
    # Note: here we don't group points with equal ticks
    return list(_foreach_likely_rexmit(_preprocess_results(
      vector, False), rtt, mss))

def _foreach_likely_rexmit(vector, rtt, mss):
    ''' Select likely rexmits under certain conditions '''
    #
    # TODO split this function into two generators, one for each rule, to
    # aid testing, and then write a proper unit test.
    #
    # Rule 1: a likely rexmit takes > 0.7-RTT, yields > 1-MSS
    likely_rexmit = []
    mss_smpls = 0
    typical_mss = collections.defaultdict(int)
    min_interval = 0.7 * rtt
    for ticks, interval, bytez in vector:
        typical_mss[bytez] += 1
        mss_smpls += 1
        if interval > min_interval and bytez > mss:
            logging.debug('raw_analyze: likely rexmit: %f %f %f', ticks,
              interval, bytez)
            likely_rexmit.append((ticks, interval, bytez))
    # Rule 2: a likely rexmit has a non-frequent MSS
    for ticks, interval, bytez in likely_rexmit:
        freq = typical_mss[bytez] / float(mss_smpls)
        if freq < 0.01:
            logging.debug('raw_analyze: non-frequent rexmit: %f %f %f (%f)',
              ticks, interval, bytez, freq)
            yield ticks, interval, bytez
