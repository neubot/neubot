# neubot/http_utils.py

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

''' HTTP utils '''

# Adapted from neubot/http/message.py

from neubot import six

def urlsplit(uri):
    ''' Wrapper for urlparse.urlsplit() '''

    scheme, netloc, path, query, fragment = six.urlparse.urlsplit(uri)
    if scheme != 'http' and scheme != 'https':
        raise RuntimeError('http_utils: unknown scheme')

    # Unquote IPv6 [<address>]:<port> or [<address>]
    if netloc.startswith('['):
        netloc = netloc[1:]
        index = netloc.find(']')
        if index == -1:
            raise RuntimeError('http_utils: invalid quoted IPv6 address')
        address = netloc[:index]

        port = netloc[index + 1:].strip()
        if not port:
            if scheme == 'https':
                port = '443'
            else:
                port = '80'
        elif not port.startswith(':'):
            raise RuntimeError('http_utils: missing port separator')
        else:
            port = port[1:]

    elif ':' in netloc:
        address, port = netloc.split(':', 1)
    elif scheme == 'https':
        address, port = netloc, '443'
    else:
        address, port = netloc, '80'

    if not path:
        path = '/'
    pathquery = path
    if query:
        pathquery = pathquery + '?' + query

    return scheme, address, port, pathquery
