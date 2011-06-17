# neubot/net/dns.py

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

import socket
from neubot import utils

DNS_CACHE = {}
DNS_TIMEOUT = 5

#
# Cache recent lookups so that DNS lookup has no effect
# on the measured RTT when we connect() more than one socket
# at once, i.e. in speedtest.
#
def getaddrinfo(address, port, family=0, socktype=0, proto=0, flags=0):
    now = utils.ticks()
    if address in DNS_CACHE:
        addrinfo, ticks = DNS_CACHE[(address, port)]
        if now - ticks <= DNS_TIMEOUT:
            return addrinfo
    addrinfo = socket.getaddrinfo(address, port, family,
                                  socktype, proto, flags)
    DNS_CACHE[(address, port)] = (addrinfo, now)
    return addrinfo
