# neubot/backend_neubot.py

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

''' Neubot backend '''

#
# The traditional Neubot backend, which saves results into
# an sqlite3 database.  Codesigned with Alessio Palmero Aprosio
# and with comments and feedback from Roberto D'Auria.
#

from neubot.database import DATABASE
from neubot.database import table_bittorrent
from neubot.database import table_speedtest

from neubot.backend_null import BackendNull

class BackendNeubot(BackendNull):
    ''' Neubot backend '''

    def bittorrent_store(self, message):
        ''' Saves the results of a bittorrent test '''
        table_bittorrent.insert(DATABASE.connection(), message)

    def speedtest_store(self, message):
        ''' Saves the results of a speedtest test '''
        table_speedtest.insert(DATABASE.connection(), message)
