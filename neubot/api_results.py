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
import os

from neubot.compat import json
from neubot.database import table_bittorrent
from neubot.database import table_speedtest
from neubot.http.message import Message
from neubot.utils_api import NotImplementedTest

from neubot import utils_sysdirs
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

DESCRIPTION = {}

PLOT_TITLES = {
    'bittorrent': (
        'Download and upload speed',
        'Connect time',
    ),
    'speedtest': (
        'Download and upload speed',
        'Connect time and latency',
    ),
}

TITLE = {
    'bittorrent': 'Your recent BitTorrent results',
    'speedtest': 'Your recent Speedtest results'
}

def __load_descriptions():
    ''' Load tests descriptions '''
    for test in AVAILABLE_TESTS:
        path = os.sep.join([utils_sysdirs.WWWDIR, 'descr', test + '.html'])
        filep = open(path, 'r')
        DESCRIPTION[test] = filep.read()
        filep.close()

def api_results(stream, request, query):
    ''' Populate results.html page '''

    test = 'speedtest'

    dictionary = cgi.parse_qs(query)
    if 'test' in dictionary:
        test = str(dictionary['test'][0])

    if not test in AVAILABLE_TESTS:
        raise NotImplementedTest('Test not implemented')

    if not DESCRIPTION:
        __load_descriptions()

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
