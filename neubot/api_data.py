# neubot/api_data.py

#
# Copyright (c) 2011, 2013
#     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#     and Simone Basso <bassosimone@gmail.com>
#
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

''' API to fetch data '''

#
# Formerly api_results.py, then moved to api_data.py, since
# we needed to use api_results.py for the API that helps
# to build results.html dynamically.
#

import cgi

from neubot.backend import BACKEND

from neubot.compat import json
from neubot.database import DATABASE
from neubot.database import table_bittorrent
from neubot.database import table_speedtest
from neubot.database import table_raw
from neubot.http.message import Message

from neubot import utils

def api_data(stream, request, query):
    ''' Get data stored on the local database '''
    since, until = -1, -1
    test = ''

    dictionary = cgi.parse_qs(query)

    if "test" in dictionary:
        test = str(dictionary["test"][0])
    if "since" in dictionary:
        since = int(dictionary["since"][0])
    if "until" in dictionary:
        until = int(dictionary["until"][0])

    if test == 'bittorrent':
        table = table_bittorrent
    elif test == 'speedtest':
        table = table_speedtest
    elif test == 'raw':
        table = table_raw
    else:
        table = None

    indent, mimetype, sort_keys = None, "application/json", False
    if "debug" in dictionary and utils.intify(dictionary["debug"][0]):
        indent, mimetype, sort_keys = 4, "text/plain", True

    response = Message()

    if table:
        lst = table.listify(DATABASE.connection(), since, until)

    #
    # TODO We should migrate all the tests to use the new
    # generic interface. At that point, we can also change
    # the API to access "pages" of data by index.
    #
    # Until we change the API, we have an API that allows
    # the caller to specify date ranges. For this reason
    # below we emulate the date-ranges semantics provided
    # by database-based tests.
    #
    # Note: we assume that, whatever the test structure,
    # there is a field called "timestamp".
    #
    else:
        lst = []
        indexes = [None]
        indexes.extend(range(16))
        for index in indexes:
            tmp = BACKEND.walk_generic(test, index)
            if not tmp:
                break
            found_start = False
            for elem in reversed(tmp):
                if until >= 0 and elem["timestamp"] > until:
                    continue
                if since >= 0 and elem["timestamp"] < since:
                    found_start = True
                    break
                lst.append(elem)
            if found_start:
                break

    body = json.dumps(lst, indent=indent, sort_keys=sort_keys)
    response.compose(code="200", reason="Ok", body=body, mimetype=mimetype)
    stream.send_response(request, response)
