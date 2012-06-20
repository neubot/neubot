# neubot/api_results.py

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

''' API to populate results.html page '''

import cgi

from neubot.compat import json
from neubot.database import table_bittorrent
from neubot.database import table_speedtest
from neubot.http.message import Message
from neubot.utils_api import NotImplementedTest

from neubot import utils

AVAILABLE_TESTS = {
    'bittorrent': 'BitTorrent',
    'speedtest': 'Speedtest'
}

AXIS_LABELS = {
    'bittorrent': [
        ['Date', 'Goodput (Mbit/s)'],
        ['Date', 'Delay (ms)']
    ],
    'speedtest': [
        ['Date', 'Goodput (Mbit/s)'],
        ['Date', 'Delay (ms)']
    ]
}

DATASETS = {
    'bittorrent': [
        [{'download_speed': 'Dload', 'upload_speed': 'Upload'}],
        [{'connect_time': 'Connect time'}]
    ],
    'speedtest': [
        [{'download_speed': 'Dload', 'upload_speed': 'Upload'}],
        [{'connect_time': 'Connect time', 'latency': 'Appl. latency'}]
    ]
}

TABLE_FIELDS = {
    'bittorrent': table_bittorrent.PRETTY_TEMPLATE,
    'speedtest': table_speedtest.PRETTY_TEMPLATE,
}

TABLE_TYPES = {
    'bittorrent': table_bittorrent.JS_TYPES,
    'speedtest': table_speedtest.JS_TYPES,
}

DESCRIPTION = {
    'bittorrent': '''\
          <p class="i18n i18n_bittorrent_explanation">
           This tests downloads and uploads a given number of bytes from
           a remote server using the BitTorrent protocol.  It reports the
           average download and upload speed measured during the test as
           well as the time required to connect to the remote server,
           which approximates the round-trip time latency.
          </p>

          <p class="i18n i18n_bittorrent_explanation_2">
           Please, note that this test is quite different from the speedtest
           one, so there are cases where the comparison between the two is not
           feasible.  We're working to deploy an HTTP test that mimics the
           behavior of this one, so that it's always possible to compare them.
	  </p>
''',
    'speedtest': '''\
          <p class="i18n i18n_speedtest_explanation_1">
           Speedtest is a test that sheds some light on the quality
           of your broadband connection, by downloading/uploading random data
           to/from a remote server, and reporting the average speeds.  The
           test also yields an over-estimate of the round-trip latency between
           you and such remote server.  For more information, see the
<a href="http://www.neubot.org/faq#what-does-speedtest-test-measures">FAQ</a>.
          </p>

          <p class="i18n i18n_speedtest_explanation_2">
           To put the results of this test in the context of the
           average broadband speed available in your country you
           might want to check the statistics available at the <a
           href="http://www.oecd.org/sti/ict/broadband">OECD Broadband
           Portal</a>.  In particular, it might be interesting to read <a
           href="http://www.oecd.org/dataoecd/10/53/39575086.xls">"Average
           advertised download speeds, by country"</a> (in XLS format).
          </p>
'''
}

TITLE = {
    'bittorrent': 'Your recent BitTorrent results',
    'speedtest': 'Your recent Speedtest results'
}

def api_results(stream, request, query):
    ''' Populate results.html page '''

    test = 'speedtest'

    dictionary = cgi.parse_qs(query)
    if 'test' in dictionary:
        test = str(dictionary['test'][0])

    if not test in AVAILABLE_TESTS:
        raise NotImplementedTest('Test not implemented')

    response_body = {
        'available_tests': AVAILABLE_TESTS,
        'selected_test': test,
        'axis_labels': AXIS_LABELS[test],
        'datasets': DATASETS[test],
        'table_fields': TABLE_FIELDS[test],
        'description': DESCRIPTION[test],
        'title': TITLE[test],
        'table_types': TABLE_TYPES[test]
    }

    # Note: DO NOT sort keys here: order must be preserved
    indent, mimetype = None, 'application/json'
    if 'debug' in dictionary and utils.intify(dictionary['debug'][0]):
        indent, mimetype = 4, 'text/plain'

    response = Message()
    body = json.dumps(response_body, indent=indent)
    response.compose(code='200', reason='Ok', body=body, mimetype=mimetype)
    stream.send_response(request, response)
