# neubot/web100.py

#
# Copyright (c) 2012
#     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#     and Simone Basso <bassosimone@gmail.com>
#
# I wrote this python interface for web100 using libweb100 sources as
# documentation, so I inevitably translated portions of it from C to python.
# Below there's libweb100 copyright statement: this python adaptation is
# available under the same license.
#
# ======================================================================
# Copyright (c) 2001 Carnegie Mellon University,
#                    The Board of Trustees of the University of Illinois,
#                    and University Corporation for Atmospheric Research.
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation; either version 2.1 of the License, or (at your
# option) any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA
# ======================================================================
#

''' Pure python interface to web100 '''

#
# N.B. This implementation does not follow the model of the original libweb100
# C implementation, i.e. there is no web100 agent.  I have just implemented
# the minimal set of features that I need to allow Neubot to snap at web100's
# variables.
#

import logging
import getopt
import pprint
import struct

import sys
import os

TYPES = (
         INTEGER,
         INTEGER32,
         INET_ADDRESS_IPV4,
         COUNTER32,
         GAUGE32,
         UNSIGNED32,
         TIME_TICKS,
         COUNTER64,
         INET_PORT_NUMBER,
         INET_ADDRESS,
         INET_ADDRESS_IPV6,
         STR32,
         OCTET
        ) = range(13)

SIZES = {
         COUNTER32: 4,
         COUNTER64: 8,
         GAUGE32: 4,
         INET_ADDRESS: 17,
         INET_ADDRESS_IPV4: 4,
         INET_ADDRESS_IPV6: 17,
         INET_PORT_NUMBER: 2,
         INTEGER32: 4,
         INTEGER: 4,
         OCTET: 1,
         STR32: 32,
         TIME_TICKS: 4,
         UNSIGNED32: 4,
        }

# Note: in struct '=' means native byte order, standard alignment, no padding
CONVERT = {
           COUNTER32: lambda raw: struct.unpack('=I', raw)[0],
           COUNTER64: lambda raw: struct.unpack('=Q', raw)[0],
           GAUGE32: lambda raw: struct.unpack('=I', raw)[0],
           INET_ADDRESS: lambda raw: struct.unpack('=17s', raw)[0],
           INET_ADDRESS_IPV4: lambda raw: struct.unpack('=I', raw)[0],
           INET_ADDRESS_IPV6: lambda raw: struct.unpack('=17s', raw)[0],
           INET_PORT_NUMBER: lambda raw: struct.unpack('=H', raw)[0],
           INTEGER32: lambda raw: struct.unpack('=I', raw)[0],
           INTEGER: lambda raw: struct.unpack('=I', raw)[0],
           OCTET: lambda raw: struct.unpack('=B', raw)[0],
           STR32: lambda raw: struct.unpack('=32s', raw)[0],
           TIME_TICKS: lambda raw: struct.unpack('=I', raw)[0],
           UNSIGNED32: lambda raw: struct.unpack('=I', raw)[0],
          }

ADDRTYPES = (
             ADDRTYPE_UNKNOWN,
             ADDRTYPE_IPV4,
             ADDRTYPE_IPV6,
             ADDRTYPE_DNS
            ) = (0, 1, 2, 16)

def _web100_init():
    ''' Read web100 header at /proc/web100/header '''
    hdr, group = {}, ''
    filep = open('/proc/web100/header', 'r')
    for line in filep:
        line = line.strip()
        if not line:
            continue
        if line.startswith('/'):
            group = line
            hdr[group] = {}
            continue
        if not group:
            continue
        name, off, kind, size = line.split()
        if name.startswith('X_') or name.startswith('_'):  # XXX
            continue
        off, kind, size = int(off), int(kind), int(size)
        if kind not in TYPES or size != SIZES[kind]:
            raise RuntimeError('web100: internal consistency error: %s', name)
        hdr[group][name] = (off, kind, size)
    filep.close()
    return hdr

def web100_init():
    ''' Read web100 hdr at /proc/web100/header '''
    try:
        return _web100_init()
    except IOError:
        logging.warning('web100: no information available', exc_info=1)
        return {}

def web100_find_dirname(hdr, spec):
    ''' Find /proc/web100/<dirname> with the given spec '''
    result = ''
    if hdr:
        matching = []
        for name in os.listdir('/proc/web100'):
            dirname = os.sep.join(['/proc/web100', name])
            if not os.path.isdir(dirname):
                continue
            tmp = os.sep.join([dirname, 'spec-ascii'])
            if not os.path.isfile(tmp):
                continue
            data = _web100_readfile(tmp)
            if not data:
                continue
            data = data.strip()
            # Work-around web100 kernel bug
            if ':::' in data:
                data = data.replace(':::', '::')
            if data == spec:
                matching.append(dirname)
        if len(matching) == 1:
            result = matching[0]
        elif len(matching) > 1:
            logging.warning('web100: multiple matching entries')  # XXX
    else:
        logging.warning('web100: no information available')
    return result

def web100_snap(hdr, dirname):
    ''' Take a snapshot of standard web100 variables '''
    if not hdr:
        logging.warning('web100: no information available')
        return {}
    result = {}
    path = os.sep.join([dirname, 'read'])
    data = _web100_readfile(path)
    if data:
        for name, value in hdr['/read'].items():
            off, kind, size = value
            tmp = data[off:off + size]
            value = CONVERT[kind](tmp)
            result[name] = value
        _web100_normalise_addr(result, 'LocalAddress', 'LocalAddressType')
        _web100_normalise_addr(result, 'RemAddress', 'LocalAddressType')
    return result

def _web100_readfile(path):
    ''' Read the specified path in a robust way '''
    # Web100 files may disappear at any time
    try:
        filep = open(path, 'rb')
        data = filep.read()
        filep.close()
        return data
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        return ''

IPV4_MAPPED = '00000000000000000000ffff'
IPV4_COMPAT = '000000000000000000000000'

def _web100_normalise_addr(result, value_name, addrtype_name):
    ''' Normalise IPv4 or IPv6 address '''
    addrtype = result[addrtype_name]
    # Note: it seems the last byte of the address is unused
    if addrtype == ADDRTYPE_IPV4:
        value = result[value_name][:4].encode('hex')
    elif addrtype == ADDRTYPE_IPV6:
        value = result[value_name][:16].encode('hex')
        # Let IPv4-mapped and -compatible addresses look like IPv4
        if value[:12] in (IPV4_MAPPED, IPV4_COMPAT):
            value = value[12:16]
            addrtype = ADDRTYPE_IPV4
    else:
        raise RuntimeError('web100: invalid address type')
    result[addrtype_name] = addrtype
    result[value_name] = value

def __autocheck(hdr):
    ''' Autocheck this implementation '''
    for dirname in os.listdir('/proc/web100'):
        dirpath = os.sep.join(['/proc/web100', dirname])
        if not os.path.isdir(dirpath):
            continue
        filepath = os.sep.join([dirpath, 'spec-ascii'])
        ascii_spec = _web100_readfile(filepath)
        ascii_spec = ascii_spec.strip()
        if not ascii_spec:
            continue
        result = web100_snap(hdr, dirpath)
        if not result or result['LocalAddressType'] != ADDRTYPE_IPV4:
            continue
        local, remote = result['LocalAddress'], result['RemAddress']
        xxx_spec = '%d.%d.%d.%d:%d %d.%d.%d.%d:%d' % (int(local[0:2], 16),
          int(local[2:4], 16), int(local[4:6], 16), int(local[6:8], 16),
          result['LocalPort'], int(remote[0:2], 16), int(remote[2:4], 16),
          int(remote[4:6], 16), int(remote[6:8], 16), result['RemPort'])
        assert(ascii_spec == xxx_spec)
    return 'web100: autocheck OK'

WEB100_HEADER = web100_init()

def main(args):
    ''' Main function '''
    try:
        options, arguments = getopt.getopt(args[1:], 'af:s:')
    except getopt.error:
        sys.exit('usage: neubot web100 [-a] [-f spec] [-s dirname]')
    if arguments:
        sys.exit('usage: neubot web100 [-a] [-f spec] [-s dirname]')

    autocheck, spec, dirname = 0, None, None
    for name, value in options:
        if name == '-a':
            autocheck = 1
        elif name == '-f':
            spec = value
        elif name == '-s':
            dirname = value

    hdr = WEB100_HEADER
    if autocheck:
        result = __autocheck(hdr)
    elif dirname:
        result = web100_snap(hdr, dirname)
    elif spec:
        result = web100_find_dirname(hdr, spec)
    else:
        result = hdr
    pprint.pprint(result)

if __name__ == '__main__':
    main(sys.argv)
