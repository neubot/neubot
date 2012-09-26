# neubot/negotiate/__init__.py

#
# Copyright (c) 2011 Simone Basso <bassosimone@gmail.com>,
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

''' Negotiate module '''

from neubot.config import CONFIG
from neubot.negotiate.server_speedtest import NEGOTIATE_SERVER_SPEEDTEST
from neubot.negotiate.server_bittorrent import NEGOTIATE_SERVER_BITTORRENT
from neubot.negotiate.server_raw import NEGOTIATE_SERVER_RAW
from neubot.negotiate.server import NEGOTIATE_SERVER
from neubot.http.server import HTTP_SERVER

CONFIG.register_defaults({
    'negotiate.parallelism': 7,
    'negotiate.min_thresh': 32,
    'negotiate.max_thresh': 64,
})

def run(poller, conf):
    ''' Start the negotiate server '''

    NEGOTIATE_SERVER.register_module('speedtest', NEGOTIATE_SERVER_SPEEDTEST)
    NEGOTIATE_SERVER.register_module('bittorrent', NEGOTIATE_SERVER_BITTORRENT)
    NEGOTIATE_SERVER.register_module('raw', NEGOTIATE_SERVER_RAW)

    HTTP_SERVER.register_child(NEGOTIATE_SERVER, '/negotiate/')
    HTTP_SERVER.register_child(NEGOTIATE_SERVER, '/collect/')

    CONFIG.register_descriptions({
        'negotiate.parallelism': 'Number of parallel tests',
        'negotiate.min_thresh': 'Minimum trehshold for RED',
        'negotiate.max_thresh': 'Maximum trehshold for RED',
    })
