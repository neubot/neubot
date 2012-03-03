# neubot/runner_updates.py

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

''' Available updates information '''

# Adapted from runner_lst.py

#
# This component is periodically updated by the rendezvous
# component and keeps track of the update information, so
# that other components can ask it whether there is an update
# and, in case, where to download it from.
#

class RunnerUpdates(object):

    ''' Available updates information '''

    # Adapted from runner_lst.py

    def __init__(self):
        ''' Initialize '''
        self.updates = {}

    def update(self, updates):
        ''' Update the list of available tests '''
        # For now just trust what the rendezvous passes us
        self.updates = updates

    def get_update_version(self):
        ''' Return available update version '''
        return self.updates.get('version')

    def get_update_uri(self):
        ''' Return available update URI '''
        return self.updates.get('uri')

RUNNER_UPDATES = RunnerUpdates()
