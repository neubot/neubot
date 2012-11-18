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
from neubot.database import table_raw
from neubot.database import table_speedtest
from neubot.http.message import Message
from neubot.utils_api import NotImplementedTest

from neubot import utils

AVAILABLE_TESTS = {
    'bittorrent': 'BitTorrent',
    'speedtest': 'Speedtest',
    'raw': 'Raw',
}

AXIS_LABELS = {
    'bittorrent': [
        ['Date', 'Goodput (Mbit/s)'],
        ['Date', 'Delay (ms)']
    ],
    'speedtest': [
        ['Date', 'Goodput (Mbit/s)'],
        ['Date', 'Delay (ms)']
    ],
    'raw': [
        ['Date', 'Goodput (Mbit/s)'],
        ['Date', 'Delay (ms)']
    ],
}

DATASETS = {
    'bittorrent': [
        [{'download_speed': 'Dload', 'upload_speed': 'Upload'}],
        [{'connect_time': 'Connect time'}]
    ],
    'speedtest': [
        [{'download_speed': 'Dload', 'upload_speed': 'Upload'}],
        [{'connect_time': 'Connect time', 'latency': 'Appl. latency'}]
    ],
    'raw': [
        [{'download_speed': 'Dload'}],
        [{'connect_time': 'Connect time', 'latency': 'Appl. latency'}]
    ]
}

TABLE_FIELDS = {
    'bittorrent': table_bittorrent.PRETTY_TEMPLATE,
    'speedtest': table_speedtest.PRETTY_TEMPLATE,
    'raw': table_raw.PRETTY_TEMPLATE,
}

TABLE_TYPES = {
    'bittorrent': table_bittorrent.JS_TYPES,
    'speedtest': table_speedtest.JS_TYPES,
    'raw': table_raw.JS_TYPES,
}

DESCRIPTION = {
    'bittorrent': '''\
<div>
          <p class="i18n i18n_results_bittorrent_explanation">
           This tests downloads and uploads a given number of bytes from
           a remote server using the BitTorrent protocol.  It reports the
           average download and upload speed measured during the test as
           well as the time required to connect to the remote server,
           which approximates the round-trip time latency.  To better
           understand what the test measures, please see the relevant
<a href="http://www.neubot.org/faq#what-does-measuring-goodput-mean">FAQ
           entry</a>.
          </p>

          <p class="i18n i18n_results_bittorrent_explanation_2">
           Please, note that this test is quite different from the speedtest
           one, so there are cases where the comparison between the two is not
           feasible.  We're working to deploy an HTTP test that mimics the
           behavior of this one, so that it's always possible to compare them.
          </p>
</div>''',
    'speedtest': '''\
<div>
          <p class="i18n i18n_results_speedtest_explanation_1">
           Speedtest is a test that sheds some light on the quality
           of your broadband connection, by downloading/uploading random data
           to/from a remote server, and reporting the average speeds.  The
           test also yields an over-estimate of the round-trip latency between
           you and such remote server.  To better understand what the test
           measures, please see the relevant
<a href="http://www.neubot.org/faq#what-does-measuring-goodput-mean">FAQ
           entry</a>.
          </p>

          <p class="i18n i18n_results_speedtest_explanation_2">
           Neubot results are correlated with the quality of your
           broadband connection (and with other confounding factors,
           as explained in the
<a href="http://www.neubot.org/faq#what-does-measuring-goodput-mean">FAQ</a>).
           So, to put them in the context of the
           average broadband speed available in your country you
           might want to check the statistics available at the <a
           href="http://www.oecd.org/sti/ict/broadband">OECD Broadband
           Portal</a>.  In particular, it might be interesting to read <a
           href="http://www.oecd.org/dataoecd/10/53/39575086.xls">"Average
           advertised download speeds, by country"</a> (in XLS format).
          </p>
</div>''',
    'raw': '''
<div>
    <p>The `raw` test is a test that characterizes your Internet connection
       by estimating round-trip latency at application level and by measuring
       the download goodput.  Instead of targeting a single Neubot server,
       this test selects a random server each time (so the goodput is expected
       to oscillate with the round-trip latency).  The test does not emulate
       any protocol, and just sends random data, but takes download goodput
       snapshots during the test, as well as process load information and TCP
       statistics.  The plan is to use this test's results to study certain
       TCP properties that may lead to a better understanding of network
       neutrality.  For sure, we aim to backport innovations introduced by
       this test to the other transmission tests.</p>

    <p>Please, note that the web user interface is unfortunately not yet ready
       to show goodput and TCP snapshots collected by this test.  We decided
       to deploy the test core in this release, even if the web interface
       integration was not finished, to start studying this test results, in
       order to identify the best parameters to show.</p>
</div>''',
}

PLOT_TITLES = {
    'bittorrent': (
        'Download and upload speed',
        'Connect time',
    ),
    'speedtest': (
        'Download and upload speed',
        'Connect time and latency',
    ),
    'raw': (
        'Download speed',
        'Connect time and latency',
    ),
}

TITLE = {
    'bittorrent': 'Your recent BitTorrent results',
    'speedtest': 'Your recent Speedtest results',
    'raw': 'Your recent raw test results',
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
        'plot_titles': PLOT_TITLES[test],
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
