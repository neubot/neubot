# neubot/server.py

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

"""
This module implements the command that manages server-side
components, including the rendezvous server and, for each test,
the negotiate server and the test server.
"""

import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.http.message import Message
from neubot.http.server import HTTP_SERVER
from neubot.http.server import ServerHTTP
from neubot.net.poller import POLLER
from neubot.speedtest.negotiate import ServerSpeedtest

from neubot.config import CONFIG
from neubot.log import LOG
from neubot.main import common

from neubot import bittorrent
from neubot import negotiate
from neubot import system

#from neubot import rendezvous          # Not yet
import neubot.rendezvous.server

class ServerSideAPI(ServerHTTP):
    """ Implements server-side API for Nagios plugin """

    def process_request(self, stream, request):
        """ Process HTTP request and return response """

        if request.uri == "/sapi":
            request.uri = "/sapi/"

        if request.uri == "/sapi/":
            response = Message()
            response.compose(code="200", reason="Ok")
        else:
            response = Message()
            response.compose(code="404", reason="Not Found")

        stream.send_response(request, response)

#
# Register default values in the global scope so that
# their variable names are always defined and the rules
# for casting the types apply.
#
CONFIG.register_defaults({
    "server.bittorrent": True,
    "server.daemonize": True,
    "server.negotiate": True,
    "server.rendezvous": False,         # Not needed on the random server
    "server.sapi": True,
    "server.speedtest": True,
})

def main(args):
    """ Starts the server module """

    #
    # Register descriptions in main() only so that
    # we don't advertise the name of knobs that aren't
    # relevant in the current context.
    #
    CONFIG.register_descriptions({
        "server.bittorrent": "Start up BitTorrent test and negotiate server",
        "server.daemonize": "Become a daemon and run in background",
        "server.negotiate": "Turn on negotiation infrastructure",
        "server.rendezvous": "Start up rendezvous server",
        "server.sapi": "Turn on Server-side API",
        "server.speedtest": "Start up Speedtest test and negotiate server",
    })

    common.main("server", "Neubot server-side component", args)
    conf = CONFIG.copy()

    #
    # Configure our global HTTP server and make
    # sure that we don't provide filesystem access
    # even by mistake.
    #
    conf["http.server.rootdir"] = ""
    HTTP_SERVER.configure(conf)

    #
    # New-style modules are started just setting a
    # bunch of conf[] variables and then invoking
    # their run() method in order to kick them off.
    #
    if conf["server.negotiate"]:
        conf["negotiate.listen"] = True
        negotiate.run(POLLER, conf)

    if conf["server.bittorrent"]:
        conf["bittorrent.listen"] = True
        conf["bittorrent.negotiate"] = True
        bittorrent.run(POLLER, conf)

    # Migrating from old style to new style
    if conf["server.rendezvous"]:
        #conf["rendezvous.listen"] = True       # Not yet
        neubot.rendezvous.server.run(POLLER, conf)

    #
    # Old-style modules are less engineered and so
    # they're a bit more painful to start up.  This
    # August maybe I will have time to migrate 'em
    # to run() interface.
    #
    if conf["server.speedtest"]:
        server = ServerSpeedtest(None)
        server.configure(conf)
        HTTP_SERVER.register_child(server, "/speedtest")

    #
    # Historically Neubot runs on port 9773 and
    # 8080 but we would like to switch to port 80
    # in the long term period, because it's rare
    # that they filter it.
    #
    address = "0.0.0.0"
    ports = (80, 8080, 9773)
    for port in ports:
        HTTP_SERVER.listen((address, port))

    #
    # Start server-side API for Nagios plugin
    # to query the state of the server.
    # Do not use the global server but rather
    # a completely different server because
    # we don't want to mix control and testing
    # functionalities.
    #
    if conf["server.sapi"]:
        server = ServerSideAPI(POLLER)
        server.configure(conf)
        server.register_ssl_port(9775)
        server.listen((address, 9775))

    #
    # Go background and drop privileges,
    # then enter into the main loop.
    #
    if conf["server.daemonize"]:
        system.change_dir()
        system.go_background()
        LOG.redirect()

    system.drop_privileges(LOG.error)
    POLLER.loop()

if __name__ == "__main__":
    main(sys.argv)
