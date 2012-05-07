# neubot/api_results.py

#
# Copyright (c) 2011 Simone Basso <bassosimone@gmail.com>,
#  NEXA Center for Internet & Society at Politecnico di Torino
# Copyright (c) 2012 Marco Scopesi <marco.scopesi@gmail.com>
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

''' API results '''

import StringIO
import cgi

from neubot.compat import json
from neubot.database import DATABASE
from neubot.database import table_bittorrent
from neubot.database import table_speedtest
from neubot.http.message import Message

from neubot import utils


class NotImplementedTest(Exception):
    ''' Raised when a test is not implemented '''


def api_results(stream, request, query):
    ''' Provide results for queried tests '''
    since, until = -1, -1
    test = ''

    dictionary = cgi.parse_qs(query)

    if dictionary.has_key("test"):
        test = str(dictionary["test"][0])
    if dictionary.has_key("since"):
        since = int(dictionary["since"][0])
    if dictionary.has_key("until"):
        until = int(dictionary["until"][0])

    if test == 'bittorrent':
        table = table_bittorrent
    elif test == 'speedtest':
        table = table_speedtest
    else:
        raise NotImplementedTest

    indent, mimetype, sort_keys = None, "application/json", False
    if "debug" in dictionary and utils.intify(dictionary["debug"][0]):
        indent, mimetype, sort_keys = 4, "text/plain", True

    response = Message()
    lst = table.listify(DATABASE.connection(), since, until)
    s = json.dumps(lst, indent=indent, sort_keys=sort_keys)
    stringio = StringIO.StringIO(s)
    response.compose(code="200", reason="Ok", body=stringio,
                     mimetype=mimetype)
    stream.send_response(request, response)
