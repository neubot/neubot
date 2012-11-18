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

from neubot.runner_hosts import RUNNER_HOSTS

from neubot import utils_net

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

    def test_to_negotiate_uri(self, test):
        ''' Map test to its negotiate URI '''
        if test in self.avail:
            # Do not cache results (see runner_hosts comment on that)
            result = self.avail[test][0]
            self.avail.clear()
            return result
        else:
            fqdn = RUNNER_HOSTS.get_random_static_host()
            endpoint = (fqdn, 8080)
            uri = 'http://%s/' % utils_net.format_epnt(endpoint)
            return uri

RUNNER_TESTS = RunnerTests()
