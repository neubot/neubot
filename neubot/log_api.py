# neubot/log_api.py

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

''' Implements /api/log '''

import cgi

from neubot.compat import json
from neubot.http.message import Message
from neubot.log import LOG

from neubot import utils

def log_api(stream, request, query):
    ''' Implements /api/log '''

    #
    # CAVEAT Currently Neubot do not update logs "in real
    # time" using AJAX.  If it did we would run in trouble
    # because each request for /api/log would generate a
    # new access log record.  In turn, a new access log
    # record will cause a new "logwritten" event, leading
    # to a log-caused Comet storm.
    #

    # Get logs and options
    logs = LOG.listify()
    options = cgi.parse_qs(query)

    # Reverse logs on request
    if utils.intify(options.get('reversed', ['0'])[0]):
        logs = reversed(logs)

    # Filter according to verbosity
    if utils.intify(options.get('verbosity', ['1'])[0]) < 2:
        logs = [ log for log in logs if log['severity'] != 'DEBUG' ]
    if utils.intify(options.get('verbosity', ['1'])[0]) < 1:
        logs = [ log for log in logs if log['severity'] != 'INFO' ]

    # Human-readable output?
    if utils.intify(options.get('debug', ['0'])[0]):
        logs = [ '%(timestamp)d [%(severity)s]\t%(message)s\r\n' % log
                 for log in logs ]
        body = ''.join(logs).encode('utf-8')
        mimetype = 'text/plain; encoding=utf-8'
    else:
        body = json.dumps(logs)
        mimetype = 'application/json'

    # Compose and send response
    response = Message()
    response.compose(code='200', reason='Ok', body=body, mimetype=mimetype)
    stream.send_response(request, response)
