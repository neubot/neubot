# neubot/raw_srvr_glue.py

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
 Glue between raw_srvr.py and server-side negotiation.  Adds to raw_srvr.py
 access control capabilities.
'''

from neubot.negotiate.server_raw import NEGOTIATE_SERVER_RAW
from neubot.raw_srvr import RawServer

class RawServerEx(RawServer):
    ''' Negotiation-enabled RAW test server '''
    # Same-as RawServer but checks that the peer is authorized

    def filter_auth(self, stream, tmp):
        ''' Filter client auth '''
        if tmp not in NEGOTIATE_SERVER_RAW.peers:
            raise RuntimeError('raw_negotiate: unknown peer')
        context = stream.opaque
        context.state = NEGOTIATE_SERVER_RAW.peers[tmp]

RAW_SERVER_EX = RawServerEx()
