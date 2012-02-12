# neubot/config_api.py

#
# Copyright (c) 2011-2012 Simone Basso <bassosimone@gmail.com>,
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

''' Implements /api/config API '''

# Adapted from neubot/api/server.py

import cgi

from neubot.compat import json
from neubot.config import ConfigError
from neubot.config import CONFIG
from neubot.database import DATABASE
from neubot.http.message import Message
from neubot.state import STATE

from neubot import marshal
from neubot import privacy
from neubot import utils

def config_api(stream, request, query):

    ''' Implements /api/config API '''

    # Adapted from neubot/api/server.py

    #
    # Fetch and process common options from the query
    # string, for now the only implemented option is
    # debug, which modifies the semantic to return text
    # for humans instead of JSON.
    #

    mimetype = 'application/json'
    indent = None

    options = cgi.parse_qs(query)

    if utils.intify(options.get('debug', ['0'])[0]):
        mimetype = 'text/plain'
        indent = 4

    #
    # Now that we know the response format, decide what is
    # the content of the response.  If the labels option is
    # available we return the documentation coupled with a
    # setting.  When the method is not POST, return instead
    # the name and value of each setting.
    #

    if utils.intify(options.get('labels', ['0'])[0]):
        obj = CONFIG.descriptions
    elif request.method != 'POST':
        obj = CONFIG.conf
    else:

        #
        # When the method is POST we need to read the
        # new settings from the request body.  Settings
        # are a x-www-form-urlencoded dictionary to
        # ease AJAX programming.
        #

        body = request.body.read()
        updates = marshal.qs_to_dictionary(body)

        #
        # PRE-update checks.  We need to make sure that
        # the following things are True:
        #
        # 1. that the incoming dictionary does not contain
        #    invalid privacy settings;
        #
        # 2. that the interval between automatic tests is
        #    either reasonable or set to zero, which means
        #    that it needs to be extracted randomly.
        #

        count = privacy.count_valid(updates, 'privacy.')
        if count < 0:
            raise ConfigError('Passed invalid privacy settings')

        agent_interval = int(updates.get('agent.interval', 0))
        if agent_interval != 0 and agent_interval < 1380:
            raise ConfigError('Passed invalid agent.interval')

        # Merge settings
        CONFIG.merge_api(updates, DATABASE.connection())

        #
        # Update the state, such that, if the AJAX code is
        # tracking the state it gets a notification that
        # some configurations variable have been modified.
        # Given that we communicate the update via that
        # channel, the response body is an empty dict to
        # keep happy the AJAX code.
        #

        STATE.update('config', updates)
        obj = '{}'

    #
    # Now that we know the body, prepare and send
    # the response for the client.
    #

    response = Message()

    body = json.dumps(obj, sort_keys=True, indent=indent)
    response.compose(code="200", reason="Ok", body=body, mimetype=mimetype)
    stream.send_response(request, response)
