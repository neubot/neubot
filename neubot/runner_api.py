# neubot/runner_api.py

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

''' Server side runner API '''

import cgi

from neubot.config import ConfigError
from neubot.defer import Deferred
from neubot.http.message import Message
from neubot.log import STREAMING_LOG
from neubot.runner_core import RUNNER_CORE
from neubot.state import STATE

from neubot import utils

def runner_api_done(state):
    ''' Invoked when the test completes successfully '''
    #
    # State value should be 'idle'.  This is needed otherwise the GUI stays
    # on collect after a test is run on demand.
    #
    STATE.update(state)

def runner_api(stream, request, query):

    ''' Implements /api/runner '''

    response = Message()

    #
    # DO NOT allow to start a test when another test is in
    # progress because I have noticed that is confusing both
    # from
    # command line and WUI.
    #
    if RUNNER_CORE.test_is_running():
        raise ConfigError('A test is already in progress, try again later')

    #
    # If there is not a query string this API is just
    # a no-operation and returns an empty JSON body to
    # keep happy the AJAX code.
    #
    if not query:
        response.compose(code='200', reason='Ok', body='{}',
                         mimetype='application/json')
        stream.send_response(request, response)
        return

    options = cgi.parse_qs(query)

    #
    # If the query does not contain the name of the
    # test, this is an error and we must notify that
    # to the caller.  Raise ConfigError, which will
    # be automatically transformed into a 500 message
    # with the proper body and reason.
    #
    if not 'test' in options:
        raise ConfigError('Missing "test" option in query string')

    test = options['test'][0]

    #
    # Simple case: the caller does not want to follow the
    # test via log streaming.  We can immediately start
    # the test using the runner and, if everything is OK,
    # we can send a succesful response, with an empty JSON
    # body to keep happy the AJAX code.
    #
    if not 'streaming' in options or not utils.intify(options['streaming'][0]):
        deferred = Deferred()
        deferred.add_callback(runner_api_done)
        RUNNER_CORE.run(test, deferred, True, 'idle')
        response.compose(code='200', reason='Ok', body='{}',
                         mimetype='application/json')
        stream.send_response(request, response)
        return

    #
    # More interesting case: the caller wants to see the log
    # messages during the test via the log streaming API.
    # We prepare a succesful response terminated by EOF and
    # then arrange things so that every new log message will
    # be copied to the HTTP response.
    # Then we kick off the runner, and note that we do that
    # AFTER we setup the response for eventual runner errors
    # to be copied to the HTTP response.
    # The runner core will automatically close all attached
    # streams at the end of the test.
    #
    response.compose(code='200', reason='Ok',
      up_to_eof=True, mimetype='text/plain')
    stream.send_response(request, response)
    STREAMING_LOG.start_streaming(stream)
    deferred = Deferred()
    deferred.add_callback(runner_api_done)
    RUNNER_CORE.run(test, deferred, True, 'idle')
