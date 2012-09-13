# neubot/utils_ctl.py

#
# Copyright (c) 2011 Marco Scopesi <marco.scopesi@gmail.com>,
#  Politecnico di Torino
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

''' Helpers to control Neubot daemon '''

import errno
import httplib
import logging
import socket
import sys
import time

def is_running(address, port, verbose=0, quick=0):

    ''' Returns True if Neubot is running '''

    # Adapted from neubot/viewer/unix.py

    #
    # When there is a huge database upgrade Neubot may take
    # time to start.  For this reason here we retry and wait
    # for a number of seconds before giving up.
    #

    logging.debug('checking whether neubot daemon is running...')

    for _ in range(15):
        running = False

        try:
            connection = httplib.HTTPConnection(address, port)
            connection.set_debuglevel(verbose)
            connection.request('GET', '/api/version')
            response = connection.getresponse()

            response.read()
            connection.close()

            if response.status == 200:
                running = True

        except (SystemExit, KeyboardInterrupt):
            raise
        except socket.error:
            #
            # This is a really common error, so it make sense to spit
            # out an explanatory message rather than just a trace.
            #
            # XXX Note that socket.error is either a string or a
            # (errno, strerror) tuple.  In both cases, taking the
            # first element is valid, i.e. is not going to raise
            # exceptions.
            #
            if sys.exc_info()[1][0] == errno.ECONNREFUSED:
                logging.warning('cannot contact neubot daemon: %s',
                                'connection refused')
            else:
                logging.warning('cannot contact neubot daemon', exc_info=1)
        except:
            logging.warning('cannot contact neubot daemon', exc_info=1)

        if running:
            logging.debug('checking whether neubot daemon is running... YES')
            return True

        if quick:
            break

        logging.debug('daemon not running... retrying in one second...')
        time.sleep(1)

    logging.debug('checking whether neubot daemon is running... NO')
    return False

def stop(address, port, verbose=0):
    ''' Stop running neubot instance '''

    # Adapted from neubot/main/__init__.py

    try:

        connection = httplib.HTTPConnection(address, port)
        connection.set_debuglevel(verbose)
        connection.request('POST', '/api/exit')

        #
        # New /api/exit does not send any response, therefore the piece
        # of code below is going to fail.  Anyway, it's not a big deal
        # because the whole function is wrapped by a blanket try..except.
        #
        response = connection.getresponse()
        response.read()

        connection.close()

    except (SystemExit, KeyboardInterrupt):
        raise
    except:
        pass
