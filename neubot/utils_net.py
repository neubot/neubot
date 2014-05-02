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

def format_epnt_web100(epnt):
    ''' Format endpoint for web100 '''
    address, port = epnt[:2]
    if not address:
        address = ''
    if ':' in address:
        sep = '.'
    else:
        sep = ':'
    return sep.join([address, str(port)])

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

def resolve(family, protocol, address, port, passive):

    logging.debug("resolve: '%s' '%s' '%s' '%s' '%s'", family, protocol,
      address, port, passive)

    prefer_ipv6_map = {
        "PF_INET": False,
        "PF_UNSPEC": False,
        "PF_INET6": True,
        "PF_UNSPEC6": True,
        # The family may be boolean for compatibility with below
        True: True,
        False: False,
    }
    prefer_ipv6 = prefer_ipv6_map[family]
    logging.debug("resolve: prefer_ipv6 %s", prefer_ipv6)

    family_map = {
        "PF_INET6": socket.AF_INET6,
        "PF_INET": socket.AF_INET,
        "PF_UNSPEC6": socket.AF_UNSPEC,
        "PF_UNSPEC": socket.AF_UNSPEC,
        # The family may be boolean for compatibility with below
        True: socket.AF_UNSPEC,
        False: socket.AF_UNSPEC,
    }
    family = family_map[family]

    protocol_map = {
        "SOCK_STREAM": socket.SOCK_STREAM,
        "SOCK_DGRAM": socket.SOCK_DGRAM,
    }
    protocol = protocol_map[protocol]

    passive_map = {
        "AI_PASSIVE": socket.AI_PASSIVE,
        "": 0,
    }
    passive = passive_map[passive]

    logging.debug("resolve: getaddrinfo '%s' '%s' %d %d 0 %d", address, port,
      family, protocol, passive)

    try:
        addrinfo = socket.getaddrinfo(address, port, family,
          protocol, 0, passive)
    except socket.error:
        logging.warning('resolve: cannot resolve', exc_info=1)
        return None

    logging.debug("resolve: getaddrinfo() returned:")
    for ainfo in addrinfo:
        logging.debug("resolve:\t%s", format_ainfo(ainfo))

    compare_af = {
        socket.AF_INET: 1,
        socket.AF_INET6: 2,
    }
    def addrinfo_map_key(ainfo):
        return compare_af[ainfo[0]]
    addrinfo.sort(key=addrinfo_map_key, reverse=prefer_ipv6)

    logging.debug("resolve: prioritized ainfo list:")
    for ainfo in addrinfo:
        logging.debug("resolve:\t%s", format_ainfo(ainfo))

    return addrinfo

def listen(epnt, prefer_ipv6):
    ''' Listen to all sockets represented by epnt '''

    logging.debug('listen(): about to listen to: %s', str(epnt))

    sockets = []

    # Allow to set any-address from command line
    if not epnt[0]:
        epnt = (None, epnt[1])

    # Allow to listen on a list of addresses
    if epnt[0] and ' ' in epnt[0]:
        for address in epnt[0].split():
            result = listen((address.strip(), epnt[1]), prefer_ipv6)
            sockets.extend(result)
        return sockets

    addrinfo = resolve(prefer_ipv6, "SOCK_STREAM", epnt[0],
      epnt[1], "AI_PASSIVE")
    if not addrinfo:
        return sockets

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
            logging.warning('listen(): cannot listen to %s',
              format_epnt(ainfo[4]), exc_info=1)
        except:
            logging.warning('listen(): cannot listen to %s',
              format_epnt(ainfo[4]), exc_info=1)

    if not sockets:
        logging.error('listen(): cannot listen to %s: %s',
          format_epnt(epnt), 'all attempts failed')

    return sockets

def connect(epnt, prefer_ipv6):
    ''' Connect to epnt '''

    logging.debug('connect(): about to connect to: %s', str(epnt))

    addrinfo = resolve(prefer_ipv6, "SOCK_STREAM", epnt[0], epnt[1], "")
    if not addrinfo:
        return None

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
            logging.warning('connect(): cannot connect to %s',
              format_epnt(ainfo[4]), exc_info=1)
        except:
            logging.warning('connect(): cannot connect to %s',
              format_epnt(ainfo[4]), exc_info=1)

    logging.error('connect(): cannot connect to %s: %s',
      format_epnt(epnt), 'all attempts failed')
    return None

def isconnected(endpoint, sock):
    ''' Check whether connect() succeeded '''

    # See http://cr.yp.to/docs/connect.html

    logging.debug('isconnected(): checking whether connect() to %s succeeded',
                  format_epnt(endpoint))

    exception, peername = None, None
    try:
        peername = getpeername(sock)
    except socket.error:
        exception = sys.exc_info()[1]

    if not exception:
        logging.debug('isconnected(): connect() to %s succeeded', (
                      format_epnt(peername)))
        return peername

    # MacOSX getpeername() fails with EINVAL
    if exception.args[0] not in (errno.ENOTCONN, errno.EINVAL):
        logging.error('isconnected(): connect() to %s failed',
                      format_epnt(endpoint), exc_info=1)
        return None

    try:
        sock.recv(1024)
    except socket.error:
        logging.error('isconnected(): connect() to %s failed',
                      format_epnt(endpoint), exc_info=1)
        return None

    raise RuntimeError('isconnected(): internal error')

def __strip_ipv4mapped_prefix(function):
    ''' Strip IPv4-mapped and IPv4-compatible prefix when the kernel does
        not implement a hard separation between IPv4 and IPv6 '''
    return __strip_ipv4mapped_prefix1(function())

def __strip_ipv4mapped_prefix1(result):
    ''' Strip IPv4-mapped and IPv4-compatible prefix when the kernel does
        not implement a hard separation between IPv4 and IPv6 '''
    result = list(result)
    if result[0].startswith('::ffff:'):
        result[0] = result[0][7:]
    elif result[0].startswith('::') and result[0] != '::1':
        result[0] = result[0][2:]
    return tuple(result)

def getpeername(sock):
    ''' getpeername() wrapper that strips IPv4-mapped prefix '''
    return __strip_ipv4mapped_prefix(sock.getpeername)

def getsockname(sock):
    ''' getsockname() wrapper that strips IPv4-mapped prefix '''
    return __strip_ipv4mapped_prefix(sock.getsockname)
