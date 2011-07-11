# neubot/bittorrent/config.py

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

#
# This module lists all the bittorrent module properties
# that you can configure.
# All the other submodules of bittorrent should fetch the
# definition of CONFIG from this one.
# We don't register descriptions unless we are running the
# bittorrent module, so the user does not see this settings
# in the common case (internals ought to be internals).
#

from neubot.config import CONFIG

NUMPIECES = 1<<20
PIECE_LEN = 1<<17

#
# When messages are bigger than SMALLMESSAGE we stop
# buffering the whole message and we pass upstream the
# incoming chunks.
# Note that SMALLMESSAGE is the maximum message size
# suggested by BEP 0003 ("All current implementations
# close connections which request an amount greater
# than 2^17").
# So, the original behavior is preserved for messages
# in the expected range, and we avoid buffering for
# "big" messages only.
#
SMALLMESSAGE = 1<<17

#
# This is the maximum time the test can run.  After that time,
# no matter what, the underlying stream is closed by the low-level
# code in <net/poller.py>.
# The typical test should take less than 15 seconds so here we
# are provisioning for more than 4x the time, which seems to be
# quite reasonable.
#
WATCHDOG = 60

_PROPERTIES = (
    ('bittorrent.address', "", 'Address to listen/connect to ("" = auto)'),
    ('bittorrent.bytes.down', 0, 'Num of bytes to download (0 = auto)'),
    ('bittorrent.bytes.up', 0, 'Num of bytes to upload (0 = auto)'),
    ('bittorrent.daemonize', False, 'Become a daemon and run in background'),
    ('bittorrent.infohash', '', 'Set InfoHash ("" = auto)'),
    ('bittorrent.listen', False, 'Run in server mode'),
    ('bittorrent.negotiate', True, 'Enable negotiate client/server'),
    ('bittorrent.my_id', '', 'Set local PeerId ("" = auto)'),
    ('bittorrent.numpieces', NUMPIECES, 'Num of pieces in bitfield'),
    ('bittorrent.piece_len', PIECE_LEN, 'Length of each piece'),
    ('bittorrent.port', 0, 'Port to listen/connect to (0 = auto)'),
    ('bittorrent.watchdog', WATCHDOG, 'Maximum test run-time in seconds'),
)

CONFIG.register_defaults(dict(zip(map(lambda t: t[0], _PROPERTIES),
                                  map(lambda t: t[1], _PROPERTIES))))

def register_descriptions():
    CONFIG.register_descriptions(dict(zip(map(lambda t: t[0], _PROPERTIES),
                                          map(lambda t: t[2], _PROPERTIES))))
