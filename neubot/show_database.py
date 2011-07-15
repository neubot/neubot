# neubot/show_database.py

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
# Simple command that pops up the web user interface
# only, just to inspect the target database.  Written
# because I was getting sick of specifying tons of
# command line options just to do that.
#

import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.api.server import ServerAPI
from neubot.http.server import HTTP_SERVER
from neubot.net.poller import POLLER

from neubot.config import CONFIG
from neubot.main import common
from neubot.main import browser
from neubot.rootdir import WWW

def main(args):
    common.main("show_database", "Show a database in the Web GUI", args)

    HTTP_SERVER.configure({
                           "http.server.rootdir": WWW,
                           "http.server.ssi": True,
                           "http.server.bind_or_die": True
                          })

    HTTP_SERVER.register_child(ServerAPI(POLLER), "/api")
    HTTP_SERVER.listen(("127.0.0.1", 8080))

    browser.open_patient("127.0.0.1", "8080", True)

    POLLER.loop()

if __name__ == "__main__":
    main(sys.argv)
