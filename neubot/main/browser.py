# neubot/main/browser.py

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

'''
 This file contains the code needed to open the web browser
 and point it to the Neubot web user interface.  The code is
 patient, meaning that it wait for Neubot to start up and
 gives up only after a reasonable number of seconds.
'''

import threading
import webbrowser
import sys
import time

if sys.version_info[0] == 3:
    import http.client as lib_http
else:
    import httplib as lib_http

from neubot import utils_net

def open_patient(address, port, newthread=False):

    '''
     When the migration takes too much time, the agent is stuck
     in DATABASE.connect() and the web user interface is not ready
     because we migrate the database and _then_ we bind the local
     address and port.  This is a wise thing to do because it's
     dangerous to split the migration in small pieces.
     The problem is that the user is likely to be scared if the
     connection fails.  We don't want that, so we ensure that
     the web user interface is ready before we start the web
     browser.
     The capability to open the browser using a daemon thread
     is needed under windows where the main process is not going
     to fork.
    '''

    if not newthread:

        sys.stderr.write("* Waiting for the web gui to become ready...")
        sys.stderr.flush()

        count = 0
        running = False
        while True:
            try:

                connection = lib_http.HTTPConnection(address, port)
                connection.request("GET", "/api/version")
                response = connection.getresponse()
                if response.status == 200:
                    running = True
                else:
                    sys.stderr.write("Error: %d\n" % response.status)
                    sys.exit(1)
                response.read()
                connection.close()

            except (SystemExit, KeyboardInterrupt):
                raise
            except:
                pass

            if running:
                sys.stderr.write("ok\n")
                break
            if count >= 15:
                sys.stderr.write("timeout\n")
                sys.exit(1)

            sys.stderr.write(".")
            sys.stderr.flush()
            time.sleep(1)
            count = count + 1

        sys.stderr.write("* Opening Neubot web gui\n")
        webbrowser.open("http://%s/" % utils_net.format_epnt((address, port)))

    else:
        sys.stderr.write("* Starting Neubot web gui daemon thread\n")
        func = lambda: open_patient(address, port)
        thread = threading.Thread(target=func)
        thread.daemon = True
        thread.start()

if __name__ == "__main__":
    open_patient(sys.argv[1], sys.argv[2])
