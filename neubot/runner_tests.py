# neubot/runner_tests.py

#
# Copyright (c) 2012 Simone Basso <bassosimone@gmail.com>,
#  NEXA Center for Internet & Society at Politecnico di Torino
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

''' List of available tests '''

# Formerly runner_lst.py

#
# This component is periodically updated by the rendezvous
# component and keeps track of the available tests, so that
# other components can ask it the URI for negotiating and
# running a test.
#

import random

STATIC_TESTS = {
    'raw': [
        'http://neubot.mlab.mlab4.nuq01.measurement-lab.org:8080/',
    ],
}

class RunnerTests(object):

    ''' Implements list of available tests '''

    # Adapted from rendezvous/client.py

    def __init__(self):
        ''' Initialize list of available tests '''
        self.avail = {}
        self.last = None

    def update(self, avail):
        ''' Update the list of available tests '''
        # For now just trust what the rendezvous passes us
        self.avail = avail
        for name, vector in STATIC_TESTS.items():
            self.avail.setdefault(name, []).extend(vector)

    def test_to_negotiate_uri(self, test):
        ''' Map test to its negotiate URI '''
        # For now just return the first item in the list
        if test in self.avail:
            return self.avail[test][0]
        else:
            return None

    def get_next_test(self):
        ''' Returns next test that must be performed '''
        #
        # This is the same strategy that was implemented in
        # rendezvous/client.py: return any test as long as
        # it's not the last one.  It can be improved by using
        # and rotating a collections.deque.
        #
        keys = self.avail.keys()
        # At the beginning keys is empty
        if self.last in keys:
            keys.remove(self.last)
        if not keys:
            # Just one test available
            return self.last
        choice = random.choice(keys)
        self.last = choice
        return choice

    def get_test_names(self):
        ''' Return names of all registered tests '''
        return self.avail.keys()

RUNNER_TESTS = RunnerTests()
