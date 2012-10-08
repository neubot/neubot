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

''' Keeps track of known M-Lab nodes '''

import logging

class RunnerHosts(object):
    ''' Keeps track of known M-Lab nodes '''

    def __init__(self):
        self.closest = None
        self.random = None

    def set_closest_node(self, node):
        ''' Sets the closest M-Lab node '''
        logging.debug('runner_hosts: closest node: %s', node['fqdn'])
        self.closest = node

    def set_random_node(self, node):
        ''' Sets one random M-Lab node '''
        logging.debug('runner_hosts: random node: %s', node['fqdn'])
        self.random = node

    def get_closest_node(self):
        ''' Return the closest node '''
        return self.closest

    def get_random_node(self):
        ''' Return one random node '''
        return self.random

RUNNER_HOSTS = RunnerHosts()
