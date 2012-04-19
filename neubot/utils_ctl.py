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

import httplib
import time

def is_running(address, port):

    ''' Returns True if Neubot is running '''

    # Adapted from neubot/viewer/unix.py

    #
    # When there is a huge database upgrade Neubot may take
    # time to start.  For this reason here we retry and wait
    # for a number of seconds before giving up.
    #

    for _ in range(15):
        running = False

        try:

            connection = httplib.HTTPConnection(address, port)
            connection.request('GET', '/api/version')
            response = connection.getresponse()
            if response.status == 200:
                running = True

            response.read()
            connection.close()

        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            pass

        if running:
            return True

        time.sleep(1)

    return False

def stop(address, port):
    ''' Stop running neubot instance '''

    # Adapted from neubot/main/__init__.py

    try:

        connection = httplib.HTTPConnection(address, port)
        connection.request('POST', '/api/exit')

        # New /api/exit does not send any response
        #response = connection.getresponse()
        #response.read()

        connection.close()
        return True

    except (SystemExit, KeyboardInterrupt):
        raise
    except:
        return False
