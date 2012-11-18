# neubot/raw_defs.py

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

'''
 Definitions shared between raw_clnt.py and raw_srvr.py
'''

from neubot import six
import struct

AUTH_LEN = 64
EMPTY_MESSAGE = struct.pack('!I', 0)
FAKEAUTH = six.b('0') * AUTH_LEN

PING_CODE = six.b(chr(0))
PINGBACK_CODE = six.b(chr(1))
RAWTEST_CODE = six.b(chr(2))
PIECE_CODE = six.b(chr(3))

#
# XXX I wanted to follow the |length|code|body| pattern, unfortunately the
# length is wrong.  It is 5, but it should be 1 (we should not count the
# initial 4 bytes in the total length).  Note that this cannot be easily fixed,
# because we need to stay compatible with old clients.
#
PING = struct.pack('!I', 5) + PING_CODE
PINGBACK = struct.pack('!I', 5) + PINGBACK_CODE
RAWTEST = struct.pack('!I', 5) + RAWTEST_CODE
