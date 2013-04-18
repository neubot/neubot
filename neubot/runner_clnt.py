# neubot/runner_clnt.py

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

''' Generic runner client '''

#
# A module, such as BitTorrent, that wants to run a test in
# the context of the Neubot daemon just needs to call the
# runner_client() function, implemented in this file, passing
# it all the needed parameters.
#

import httplib
import getopt
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot import utils_version

def runner_client(address, port, verbosity, test):
    ''' Run the specified test in the context of the Neubot
        daemon and shows log messages while the test is
        in progress '''

    # Just a wrapper function

    sys.stderr.write('INFO: Asking Neubot to run the test...\n')

    hint = {}
    try:
        __runner_client(address, port, verbosity, test, hint)
    except (KeyboardInterrupt, SystemExit):
        pass
    except:
        error = sys.exc_info()[1]
        sys.stderr.write('ERROR: cannot contact Neubot: %s\n' % str(error))

    return not hint['run_locally']

def __runner_client(address, port, verbosity, test, hint):
    ''' Run the specified test in the context of the Neubot
        daemon and shows log messages while the test is
        in progress '''

    #
    # FIXME When multiple addresses are specified, just
    # consider the first one.
    #
    if ' ' in address:
        address = address.split()[0]

    #
    # Before we make the request, make sure we're really
    # talking with the Neubot and otherwise suggest the
    # caller to try to run the test directly and non into
    # the context of the local daemon.
    #
    hint['run_locally'] = True

    connection = httplib.HTTPConnection(address, port)
    connection.set_debuglevel(verbosity)

    connection.request('GET', '/api/version')
    response = connection.getresponse()
    if response.status != 200:
        raise RuntimeError('Not speaking with a Neubot daemon')
    body = response.read()
    if body != utils_version.CANONICAL_VERSION:
        raise RuntimeError('Bad Neubot daemon version')

    #
    # OK we're talking to Neubot and it's the same version
    # as us, which means that we must not hint the caller
    # to run the test directly.  From now on, if something
    # fails it's because we violated /api/runner API or
    # the local daemon is busy -- in both cases, running
    # the test directly is offensive.
    #
    sys.stdout.write('INFO The local daemon will run the test for us\n')
    hint['run_locally'] = False

    #
    # Ask the local Neubot daemon to run a test for us
    # using /api/runner API.
    # We use the streaming feature the get logs copied to
    # the response during the test.
    # We must use response.fp.readline() because the
    # http response object does not implement directly
    # such interface.
    #
    connection.request('GET', '/api/runner?test=%s&streaming=1' % test)

    response = connection.getresponse()
    if response.status != 200:
        raise RuntimeError('Neubot daemon: %s' % response.reason)

    sys.stdout.write('INFO === BEGIN local daemon log ===\n')
    while True:
        line = response.fp.readline()
        if not line:
            break
        if line.startswith('ACCESS'):
            continue
        if line.startswith('DEBUG') and not verbosity:
            continue
        sys.stdout.write(line)
    sys.stdout.write('INFO === END local daemon log ===\n')

def main(args):
    ''' Test main for the runner client '''

    # Adapted from neubot/api/client.py

    try:
        options, arguments = getopt.getopt(args[1:], 'D:v')
    except getopt.error:
        sys.exit('Usage: neubot runner_clnt [-v] [-D property=value] test')
    if len(arguments) != 1:
        sys.exit('Usage: neubot runner_clnt [-v] [-D property=value] test')

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

    test = arguments[0]
    runner_client(address, port, verbosity, test)

if __name__ == '__main__':
    main(sys.argv)
