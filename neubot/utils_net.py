# neubot/utils_net.py

#
# Copyright (c) 2010-2012 Simone Basso <bassosimone@gmail.com>,
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

''' Network utils '''

import errno
import logging
import os
import socket
import sys

from neubot.config import CONFIG

# Winsock returns EWOULDBLOCK
INPROGRESS = [ 0, errno.EINPROGRESS, errno.EWOULDBLOCK, errno.EAGAIN ]

def format_epnt(epnt):
    ''' Format endpoint for printing '''
    address, port = epnt[:2]
    if not address:
        address = ''
    if ':' in address:
        address = ''.join(['[', address, ']'])
    return ':'.join([address, str(port)])

def format_ainfo(ainfo):
    ''' Format addrinfo for printing '''
    family, socktype, proto, canonname, sockaddr = ainfo

    if family == socket.AF_INET:
        family = 'AF_INET'
    elif family == socket.AF_INET6:
        family = 'AF_INET6'
    else:
        family = str(family)

    if socktype == socket.SOCK_STREAM:
        socktype = 'SOCK_STREAM'
    elif socktype == socket.SOCK_DGRAM:
        socktype = 'SOCK_DGRAM'
    else:
        socktype = str(socktype)

    if proto == socket.IPPROTO_TCP:
        proto = 'IPPROTO_TCP'
    elif proto == socket.IPPROTO_UDP:
        proto = 'IPPROTO_UDP'
    else:
        proto = str(proto)

    if not canonname:
        canonname = '""'

    return '(%s, %s, %s, %s, %s)' % (family, socktype, proto,
      canonname, sockaddr)

# Make sure AF_INET < AF_INET6
__COMPARE_AF = {
    socket.AF_INET: 1,
    socket.AF_INET6: 2,
}

def __compare_af(left, right):
    ''' Compare address families '''
    left = __COMPARE_AF[left[0]]
    right = __COMPARE_AF[right[0]]
    return cmp(left, right)

def listen(epnt):
    ''' Listen to all sockets represented by epnt '''

    logging.debug('listen(): about to listen to: %s', str(epnt))

    sockets = []

    # Allow to set any-address from command line
    if not epnt[0]:
        epnt = (None, epnt[1])

    # Allow to listen on a list of addresses
    if ' ' in epnt[0]:
        for address in epnt[0].split():
            result = listen((address.strip(), epnt[1]))
            sockets.extend(result)
        return sockets

    try:
        addrinfo = socket.getaddrinfo(epnt[0], epnt[1], socket.AF_UNSPEC,
                            socket.SOCK_STREAM, 0, socket.AI_PASSIVE)
    except socket.error:
        exception = sys.exc_info()[1]
        logging.error('listen(): cannot listen to %s: %s',
                      format_epnt(epnt), str(exception))
        return sockets

    prefer_ipv6 = CONFIG['prefer_ipv6']
    addrinfo.sort(cmp=__compare_af, reverse=prefer_ipv6)

    for ainfo in addrinfo:
        try:
            logging.debug('listen(): trying with: %s', format_ainfo(ainfo))

            sock = socket.socket(ainfo[0], socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setblocking(False)
            sock.bind(ainfo[4])
            # Probably the backlog here is too big
            sock.listen(128)

            logging.debug('listen(): listening at: %s', format_epnt(ainfo[4]))
            sockets.append(sock)

        except socket.error:
            exception = sys.exc_info()[1]
            logging.warning('listen(): cannot listen to %s: %s',
              format_epnt(ainfo[4]), str(exception))
        except:
            exception = sys.exc_info()[1]
            logging.warning('listen(): cannot listen to %s: %s',
              format_epnt(ainfo[4]), str(exception))

    if not sockets:
        logging.error('listen(): cannot listen to %s: %s',
          format_epnt(epnt), 'all attempts failed')

    return sockets

def connect(epnt):
    ''' Connect to epnt '''

    logging.debug('connect(): about to connect to: %s', str(epnt))

    try:
        addrinfo = socket.getaddrinfo(epnt[0], epnt[1], socket.AF_UNSPEC,
                                      socket.SOCK_STREAM)
    except socket.error:
        exception = sys.exc_info()[1]
        logging.error('connect(): cannot connect to %s: %s',
                      format_epnt(epnt), str(exception))
        return None

    prefer_ipv6 = CONFIG['prefer_ipv6']
    addrinfo.sort(cmp=__compare_af, reverse=prefer_ipv6)

    for ainfo in addrinfo:
        try:
            logging.debug('connect(): trying with: %s', format_ainfo(ainfo))

            sock = socket.socket(ainfo[0], socket.SOCK_STREAM)
            sock.setblocking(False)
            result = sock.connect_ex(ainfo[4])
            if result not in INPROGRESS:
                raise socket.error(result, os.strerror(result))

            logging.debug('connect(): connection to %s in progress...',
                          format_epnt(ainfo[4]))
            return sock

        except socket.error:
            exception = sys.exc_info()[1]
            logging.warning('connect(): cannot connect to %s: %s',
              format_epnt(ainfo[4]), str(exception))
        except:
            exception = sys.exc_info()[1]
            logging.warning('connect(): cannot connect to %s: %s',
              format_epnt(ainfo[4]), str(exception))

    logging.error('connect(): cannot connect to %s: %s',
      format_epnt(epnt), 'all attempts failed')
    return None
