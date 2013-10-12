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

STATIC_TABLE_TIME = 'Sat Oct 12 10:21:57 2013'

STATIC_TABLE = [
    'neubot.mlab.mlab1.akl01.measurement-lab.org',
    'neubot.mlab.mlab1.ams01.measurement-lab.org',
    'neubot.mlab.mlab1.ams02.measurement-lab.org',
    'neubot.mlab.mlab1.arn01.measurement-lab.org',
    'neubot.mlab.mlab1.ath01.measurement-lab.org',
    'neubot.mlab.mlab1.ath02.measurement-lab.org',
    'neubot.mlab.mlab1.atl01.measurement-lab.org',
    'neubot.mlab.mlab1.bog01.measurement-lab.org',
    'neubot.mlab.mlab1.dfw01.measurement-lab.org',
    'neubot.mlab.mlab1.dub01.measurement-lab.org',
    'neubot.mlab.mlab1.ham01.measurement-lab.org',
    'neubot.mlab.mlab1.hnd01.measurement-lab.org',
    'neubot.mlab.mlab1.iad01.measurement-lab.org',
    'neubot.mlab.mlab1.jnb01.measurement-lab.org',
    'neubot.mlab.mlab1.lax01.measurement-lab.org',
    'neubot.mlab.mlab1.lba01.measurement-lab.org',
    'neubot.mlab.mlab1.lca01.measurement-lab.org',
    'neubot.mlab.mlab1.lga01.measurement-lab.org',
    'neubot.mlab.mlab1.lga02.measurement-lab.org',
    'neubot.mlab.mlab1.lhr01.measurement-lab.org',
    'neubot.mlab.mlab1.lju01.measurement-lab.org',
    'neubot.mlab.mlab1.mad01.measurement-lab.org',
    'neubot.mlab.mlab1.mia01.measurement-lab.org',
    'neubot.mlab.mlab1.mil01.measurement-lab.org',
    'neubot.mlab.mlab1.nbo01.measurement-lab.org',
    'neubot.mlab.mlab1.nuq01.measurement-lab.org',
    'neubot.mlab.mlab1.nuq02.measurement-lab.org',
    'neubot.mlab.mlab1.nuq0t.measurement-lab.org',
    'neubot.mlab.mlab1.ord01.measurement-lab.org',
    'neubot.mlab.mlab1.par01.measurement-lab.org',
    'neubot.mlab.mlab1.prg01.measurement-lab.org',
    'neubot.mlab.mlab1.sea01.measurement-lab.org',
    'neubot.mlab.mlab1.svg01.measurement-lab.org',
    'neubot.mlab.mlab1.syd01.measurement-lab.org',
    'neubot.mlab.mlab1.syd02.measurement-lab.org',
    'neubot.mlab.mlab1.tpe01.measurement-lab.org',
    'neubot.mlab.mlab1.trn01.measurement-lab.org',
    'neubot.mlab.mlab1.tun01.measurement-lab.org',
    'neubot.mlab.mlab1.vie01.measurement-lab.org',
    'neubot.mlab.mlab1.wlg01.measurement-lab.org',
    'neubot.mlab.mlab2.akl01.measurement-lab.org',
    'neubot.mlab.mlab2.ams01.measurement-lab.org',
    'neubot.mlab.mlab2.ams02.measurement-lab.org',
    'neubot.mlab.mlab2.arn01.measurement-lab.org',
    'neubot.mlab.mlab2.ath01.measurement-lab.org',
    'neubot.mlab.mlab2.ath02.measurement-lab.org',
    'neubot.mlab.mlab2.atl01.measurement-lab.org',
    'neubot.mlab.mlab2.bog01.measurement-lab.org',
    'neubot.mlab.mlab2.dfw01.measurement-lab.org',
    'neubot.mlab.mlab2.dub01.measurement-lab.org',
    'neubot.mlab.mlab2.ham01.measurement-lab.org',
    'neubot.mlab.mlab2.hnd01.measurement-lab.org',
    'neubot.mlab.mlab2.iad01.measurement-lab.org',
    'neubot.mlab.mlab2.jnb01.measurement-lab.org',
    'neubot.mlab.mlab2.lax01.measurement-lab.org',
    'neubot.mlab.mlab2.lba01.measurement-lab.org',
    'neubot.mlab.mlab2.lca01.measurement-lab.org',
    'neubot.mlab.mlab2.lga01.measurement-lab.org',
    'neubot.mlab.mlab2.lga02.measurement-lab.org',
    'neubot.mlab.mlab2.lhr01.measurement-lab.org',
    'neubot.mlab.mlab2.lju01.measurement-lab.org',
    'neubot.mlab.mlab2.mad01.measurement-lab.org',
    'neubot.mlab.mlab2.mia01.measurement-lab.org',
    'neubot.mlab.mlab2.mil01.measurement-lab.org',
    'neubot.mlab.mlab2.nbo01.measurement-lab.org',
    'neubot.mlab.mlab2.nuq01.measurement-lab.org',
    'neubot.mlab.mlab2.nuq02.measurement-lab.org',
    'neubot.mlab.mlab2.nuq0t.measurement-lab.org',
    'neubot.mlab.mlab2.ord01.measurement-lab.org',
    'neubot.mlab.mlab2.par01.measurement-lab.org',
    'neubot.mlab.mlab2.prg01.measurement-lab.org',
    'neubot.mlab.mlab2.sea01.measurement-lab.org',
    'neubot.mlab.mlab2.svg01.measurement-lab.org',
    'neubot.mlab.mlab2.syd01.measurement-lab.org',
    'neubot.mlab.mlab2.syd02.measurement-lab.org',
    'neubot.mlab.mlab2.tpe01.measurement-lab.org',
    'neubot.mlab.mlab2.trn01.measurement-lab.org',
    'neubot.mlab.mlab2.tun01.measurement-lab.org',
    'neubot.mlab.mlab2.vie01.measurement-lab.org',
    'neubot.mlab.mlab2.wlg01.measurement-lab.org',
    'neubot.mlab.mlab3.akl01.measurement-lab.org',
    'neubot.mlab.mlab3.ams01.measurement-lab.org',
    'neubot.mlab.mlab3.ams02.measurement-lab.org',
    'neubot.mlab.mlab3.arn01.measurement-lab.org',
    'neubot.mlab.mlab3.ath01.measurement-lab.org',
    'neubot.mlab.mlab3.ath02.measurement-lab.org',
    'neubot.mlab.mlab3.atl01.measurement-lab.org',
    'neubot.mlab.mlab3.bog01.measurement-lab.org',
    'neubot.mlab.mlab3.dfw01.measurement-lab.org',
    'neubot.mlab.mlab3.dub01.measurement-lab.org',
    'neubot.mlab.mlab3.ham01.measurement-lab.org',
    'neubot.mlab.mlab3.hnd01.measurement-lab.org',
    'neubot.mlab.mlab3.iad01.measurement-lab.org',
    'neubot.mlab.mlab3.jnb01.measurement-lab.org',
    'neubot.mlab.mlab3.lax01.measurement-lab.org',
    'neubot.mlab.mlab3.lba01.measurement-lab.org',
    'neubot.mlab.mlab3.lca01.measurement-lab.org',
    'neubot.mlab.mlab3.lga01.measurement-lab.org',
    'neubot.mlab.mlab3.lga02.measurement-lab.org',
    'neubot.mlab.mlab3.lhr01.measurement-lab.org',
    'neubot.mlab.mlab3.lju01.measurement-lab.org',
    'neubot.mlab.mlab3.mad01.measurement-lab.org',
    'neubot.mlab.mlab3.mia01.measurement-lab.org',
    'neubot.mlab.mlab3.mil01.measurement-lab.org',
    'neubot.mlab.mlab3.nbo01.measurement-lab.org',
    'neubot.mlab.mlab3.nuq01.measurement-lab.org',
    'neubot.mlab.mlab3.nuq02.measurement-lab.org',
    'neubot.mlab.mlab3.nuq0t.measurement-lab.org',
    'neubot.mlab.mlab3.ord01.measurement-lab.org',
    'neubot.mlab.mlab3.par01.measurement-lab.org',
    'neubot.mlab.mlab3.prg01.measurement-lab.org',
    'neubot.mlab.mlab3.sea01.measurement-lab.org',
    'neubot.mlab.mlab3.svg01.measurement-lab.org',
    'neubot.mlab.mlab3.syd01.measurement-lab.org',
    'neubot.mlab.mlab3.syd02.measurement-lab.org',
    'neubot.mlab.mlab3.tpe01.measurement-lab.org',
    'neubot.mlab.mlab3.trn01.measurement-lab.org',
    'neubot.mlab.mlab3.tun01.measurement-lab.org',
    'neubot.mlab.mlab3.vie01.measurement-lab.org',
    'neubot.mlab.mlab3.wlg01.measurement-lab.org',
    'neubot.mlab.mlab4.nuq01.measurement-lab.org',
    'neubot.mlab.mlab4.nuq02.measurement-lab.org',
    'neubot.mlab.mlab4.nuq0t.measurement-lab.org',
    'neubot.mlab.mlab4.prg01.measurement-lab.org',
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
