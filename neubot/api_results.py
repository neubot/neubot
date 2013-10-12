# neubot/api_results.py

#
# Copyright (c) 2012-2013
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

''' API to populate results.html page '''

import cgi
import os

from neubot.compat import json
from neubot.config import CONFIG
from neubot.http.message import Message
from neubot.utils_api import NotImplementedTest

from neubot import utils_hier
from neubot import utils_path
from neubot import utils

# Directory that contains the description of each test, which consists of
# two files per test: a JSON file and an HTML file.
TESTDIR = utils_path.join(utils_hier.WWWDIR, 'test')

# Config variables to be copied to output: they allow ordinary users to
# configure the appearance of results.html.
COPY_CONFIG_VARIABLES = (
    'www_no_description',
    'www_no_legend',
    'www_no_plot',
    'www_no_split_by_ip',
    'www_no_table',
    'www_no_title',
)

def api_results(stream, request, query):
    ''' Populates www/results.html page '''

    dictionary = cgi.parse_qs(query)
    test = CONFIG['www_default_test_to_show']
    if 'test' in dictionary:
        test = str(dictionary['test'][0])

    # Read the directory each time, so you don't need to restart the daemon
    # after you have changed the description of a test.
    available_tests = {}
    for filename in os.listdir(TESTDIR):
        if filename.endswith('.json'):
            index = filename.rfind('.json')
            if index == -1:
                raise RuntimeError('api_results: internal error')
            name = filename[:index]
            available_tests[name] = filename
    if not test in available_tests:
        raise NotImplementedTest('Test not implemented')

    # Allow power users to customize results.html heavily, by creating JSON
    # descriptions with local modifications.
    filepath = utils_path.append(TESTDIR, available_tests[test], False)
    if not filepath:
        raise RuntimeError("api_results: append() path failed")
    localfilepath = filepath + '.local'
    if os.path.isfile(localfilepath):
        filep = open(localfilepath, 'rb')
    else:
        filep = open(filepath, 'rb')
    response_body = json.loads(filep.read())
    filep.close()

    # Add extra information needed to populate results.html selection that
    # allows to select which test results must be shown.
    response_body['available_tests'] = available_tests.keys()
    response_body['selected_test'] = test

    descrpath = filepath.replace('.json', '.html')
    if os.path.isfile(descrpath):
        filep = open(descrpath, 'rb')
        response_body['description'] = filep.read()
        filep.close()

    # Provide the web user interface some settings it needs, but only if they
    # were not already provided by the `.local` file.
    for variable in COPY_CONFIG_VARIABLES:
        if not variable in response_body:
            response_body[variable] = CONFIG[variable]

    # Note: DO NOT sort keys here: order MUST be preserved
    indent, mimetype = None, 'application/json'
    if 'debug' in dictionary and utils.intify(dictionary['debug'][0]):
        indent, mimetype = 4, 'text/plain'

    response = Message()
    body = json.dumps(response_body, indent=indent)
    response.compose(code='200', reason='Ok', body=body, mimetype=mimetype)
    stream.send_response(request, response)
