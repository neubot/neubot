# neubot/runner_policy.py

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

''' Policy for selecting the next test '''

import collections
import logging
import random

#
# XXX Ideally the master server should set the policy, and here
# we should also fetch the test names automatically. However,
# it takes too much time to modify the master server now (which
# is a change that touches a lot of legacy code), therefore
# I think it's wiser to hardcode the policy for now.
#
TEST_NAMES = [
              # probability: 9%
              'raw',

              # probability: 27%
              'bittorrent',
              'bittorrent',
              'bittorrent',

              # probability: 27%
              'speedtest',
              'speedtest',
              'speedtest',

              # probability: 36%
              'dash',
              'dash',
              'dash',
              'dash',
             ]

class RunnerPolicy(object):
    ''' Policy for selecting next test '''

    def __init__(self):
        test_names = TEST_NAMES
        random.shuffle(test_names)
        self.sequence = collections.deque(test_names)

    def get_next_test(self):
        ''' Returns next test that must be performed '''
        selected = self.sequence[0]
        logging.info('runner_policy: test sequence: %s', list(self.sequence))
        self.sequence.rotate(1)
        return selected

    def get_random_test(self):
        ''' Returns one test at random '''
        selected = random.choice(self.sequence)
        return selected

RUNNER_POLICY = RunnerPolicy()
