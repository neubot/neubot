# neubot/runner_hosts.py

#
# Copyright (c) 2012-2013
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

''' Keeps track of known M-Lab hosts '''

import logging
import random

STATIC_TABLE_TIME = 'Sat Oct 12 10:21:57 2013'  # TODO: change the date

STATIC_TABLE = [
    # TODO: put your test servers here
]

class RunnerHosts(object):
    ''' Keeps track of known M-Lab hosts '''

    def __init__(self):
        self.closest = None
        self.random = None

    def set_closest_host(self, host):
        ''' Sets the closest M-Lab host '''
        logging.debug('runner_hosts: closest host: %s', host['fqdn'])
        self.closest = host['fqdn']

    def set_random_host(self, host):
        ''' Sets one random M-Lab host '''
        logging.debug('runner_hosts: random host: %s', host['fqdn'])
        self.random = host['fqdn']

    #
    # Why we don't cache latest random/closest host
    # ---------------------------------------------
    #
    # For the random host, it is wrong to cache it: if next mlab-ns query fails,
    # next test is going to reuse the cached host.  This is clearly not random.
    # So, use the random host returned by mlab-ns just once.
    #   For the closest host, it may be good to cache it: if next mlab-ns query
    # fails, next test is going to reuse it.  However, the static table should
    # be the exception, not the norm.  Therefore, behave same-as the random host
    # and avoid caching, such that, if there is a failure, the behavior changes
    # (e.g. warnings in the logs, big changes in RTT) and the problem (perhaps
    # just a local routing problem) is more likely to be spotted.  Moreover the
    # cached closest host may be down, and insisting with it in this case is
    # worst than choosing one host at random.
    #

    def get_closest_host(self):
        ''' Return the closest host '''
        if self.closest:
            result = self.closest
            self.closest = None
            return result
        return self.get_random_static_host()

    def get_random_host(self):
        ''' Return one random host '''
        if self.random:
            result = self.random
            self.random = None
            return result
        return self.get_random_static_host()

    @staticmethod
    def get_random_static_host():
        ''' Use static table to return one host at random '''
        logging.warning('runner_hosts: no discovered hosts: using static table')
        logging.info('runner_hosts: table: num-hosts: %d, generated: "%s"',
          len(STATIC_TABLE), STATIC_TABLE_TIME)
        logging.warning('runner_hosts: selecting one static host at random')
        return random.choice(STATIC_TABLE)

RUNNER_HOSTS = RunnerHosts()
