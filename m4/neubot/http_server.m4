# @DEST@

#
# Copyright (c) 2011-2013
#     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#     and Simone Basso <bassosimone@gmail.com>
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

""" HTTP servers """

include(`m4/include/aaa_base.m4')
include(`m4/include/http.m4')

NEUBOT_PY3_READY()

import logging

from neubot.network_core import BuffStreamSocket
from neubot.network_ssl import BuffSSLSocket

from neubot import six

HTTP_DEFS()

dnl
dnl HTTP_SERVER(<class-name>, <base-class>, <docstring>)
dnl
define(`HTTP_SERVER',
`class $1($2):
    """ $3 """

    HTTP_INIT_CLEANUP_DEL($2, response, protocol, code, reason, request,
      method, uri, protocol)

    HTTP_READ_HEADERS(request, method, uri, protocol)

    HTTP_SERVER_READ_BODY()

    HTTP_READ_BOUNDED(request)

    HTTP_READ_CHUNKED(request)

    HTTP_SEND(response, protocol, code, reason)
')

HTTP_SERVER(HTTPServer, BuffStreamSocket, HTTP server)

HTTP_SERVER(HTTPSServer, BuffSSLSocket, HTTPS server)
