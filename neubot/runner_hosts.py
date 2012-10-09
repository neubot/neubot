# neubot/runner_hosts.py

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

''' Keeps track of known M-Lab hosts '''

import logging

class RunnerHosts(object):
    ''' Keeps track of known M-Lab hosts '''

    def __init__(self):
        self.closest = None
        self.random = None

    def set_closest_host(self, host):
        ''' Sets the closest M-Lab host '''
        logging.debug('runner_hosts: closest host: %s', host['fqdn'])
        self.closest = host

    def set_random_host(self, host):
        ''' Sets one random M-Lab host '''
        logging.debug('runner_hosts: random host: %s', host['fqdn'])
        self.random = host

    def get_closest_host(self):
        ''' Return the closest host '''
        return self.closest

    def get_random_host(self):
        ''' Return one random host '''
        return self.random

RUNNER_HOSTS = RunnerHosts()
