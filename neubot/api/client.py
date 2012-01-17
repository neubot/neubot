# neubot/api/client.py

#
# Copyright (c) 2011 Simone Basso <bassosimone@gmail.com>,
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

''' Simple API client '''

import asyncore
import getopt
import logging
import sys
import time

if __name__ == '__main__':
    sys.path.insert(0, '.')

if sys.version_info[0] == 3:
    import http.client as lib_http
else:
    import httplib as lib_http

from neubot.compat import json

def main(args):

    ''' Monitor Neubot state via command line '''

    try:
        options, arguments = getopt.getopt(args[1:], 'D:v')
    except getopt.error:
        sys.exit('Usage: neubot api.client [-v] [-D property=value]')
    if arguments:
        sys.exit('Usage: neubot api.client [-v] [-D property=value]')

    address, port, verbosity = '127.0.0.1', '9774', 0
    for name, value in options:
        if name == '-D':
            name, value = value.split('=', 1)
            if name == 'address':
                address = value
            elif name == 'port':
                port = value
        elif name == '-v':
            verbosity += 1

    timestamp = 0
    while True:
        try:

            connection = lib_http.HTTPConnection(address, port)
            connection.set_debuglevel(verbosity)
            connection.request('GET', '/api/state?t=%d' % timestamp)

            response = connection.getresponse()
            if response.status != 200:
                raise RuntimeError('Bad HTTP status: %d' % response.status)

            if response.getheader("content-type") != "application/json":
                raise RuntimeError("Unexpected contenty type")

            octets = response.read()
            dictionary = json.loads(octets)

            logging.info("APIStateTracker: received JSON: %s",
                json.dumps(dictionary, ensure_ascii=True))

            if not "events" in dictionary:
                continue
            if not "current" in dictionary:
                raise RuntimeError("Incomplete dictionary")

            timestamp = max(0, int(dictionary["t"]))
            json.dumps(dictionary, sys.stdout)

        except KeyboardInterrupt:
            break
        except:
            error = asyncore.compact_traceback()
            logging.error('Exception: %s', str(error))
            time.sleep(5)

if __name__ == "__main__":
    main(sys.argv)
