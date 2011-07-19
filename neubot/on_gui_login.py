# neubot/on_gui_login.py

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

#
# Quick and dirty script to notify users that we
# have updates available whenever they log in into
# windows or gnome.
# Of course this can be done better but given the
# urgence of notifying updates it is much better
# than nothing.
#

import httplib
import getopt
import random
import sys
import time

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.compat import json
from neubot.gui.infobox import InfoBox
from neubot.log import LOG

if sys.platform == "win32":
    from neubot.system import _proc_win32

#
# This is invoked when the user logs in the GUI
# environment, while realmain() is invoked by
# command line.
#
def main(args):
    LOG.redirect()

    #
    # XXX With Windows we need to kill on_gui_login before
    # updating because otherwise the various DLLs are locked
    # and the procedure fails.  This piece of code ASSUMES
    # that we have already killed the Neubot Agent so we can
    # safely kill all the remaining neubotw.exe instances
    # using brute force.
    #
    if sys.platform == "win32":
        options, arguments = getopt.getopt(args[1:], "k")
        for name, value in options:
            if name == "-k":
                _proc_win32._kill_process("neubotw.exe")
                sys.exit(0)

    # Give daemon some time to breathe first
    time.sleep(30)
    realmain(args, lambda: random.randrange(300, 1500))

def realmain(args, get_sleep_interval):
    while True:
        _loop_once(args)

        #
        # FIXME I would like the process to run for a long
        # time and keep spamming the user.  Unfortunately
        # under Windows it's not a good idea to exit the Tk
        # mainloop() because we do not receive events and
        # so Windows does not shutdown cleanly.  The simplest
        # fix is as follows: just run once and then exit.
        #
        break

        time.sleep(get_sleep_interval())

def _loop_once(args):
    message = ""

    # Check for updates
    try:
        connection = httplib.HTTPConnection("127.0.0.1", "9774")
        connection.request("GET", "/api/state")

        response = connection.getresponse()
        if response.status != 200:
            raise RuntimeError("Unexpected response")

        body = response.read()
        dictionary = json.loads(body)

        update = dictionary["events"]["update"]
        tpl = update["version"], update["uri"]
        message += "New version %s available at <%s> " % tpl
    except:
        LOG.exception()

    # Check whether we need to update privacy settings
    try:
        connection = httplib.HTTPConnection("127.0.0.1", "9774")
        connection.request("GET", "/api/config")

        response = connection.getresponse()
        if response.status != 200:
            raise RuntimeError("Unexpected response")

        body = response.read()
        dictionary = json.loads(body)

        if (not "privacy.informed" in dictionary or not
          dictionary["privacy.informed"]):
            uri = "http://127.0.0.1:9774/privacy.html"
            message += " Please update your privacy settings at <%s>" % uri
    except:
        LOG.exception()

    # Spam the user
    if message:
        InfoBox(message)

if __name__ == "__main__":
    realmain(sys.argv, lambda: 5)
