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

import gc
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.http.message import Message
from neubot.http.server import HTTP_SERVER
from neubot.http.server import ServerHTTP
from neubot.net.poller import POLLER

from neubot.negotiate.server import NEGOTIATE_SERVER
from neubot.negotiate.server_speedtest import NEGOTIATE_SERVER_SPEEDTEST
from neubot.negotiate.server_bittorrent import NEGOTIATE_SERVER_BITTORRENT
from neubot.net.dns import DNS_CACHE
from neubot.notify import NOTIFIER
from neubot.state import STATE

from neubot.compat import json
from neubot.debug import objgraph
from neubot.config import CONFIG
from neubot.log import LOG
from neubot.main import common

from neubot import bittorrent
from neubot import negotiate
from neubot import system

#from neubot import rendezvous          # Not yet
import neubot.rendezvous.server

#from neubot import speedtest           # Not yet
import neubot.speedtest.wrapper

class DebugAPI(ServerHTTP):
    ''' Implements the debugging API '''

    def process_request(self, stream, request):
        ''' Process HTTP request and return response '''

        response = Message()

        if request.uri == '/debugmem/collect':
            body = gc.collect(2)

        elif request.uri == '/debugmem/count':
            counts = gc.get_count()
            body = {
                    'len_gc_objects': len(gc.get_objects()),
                    'len_gc_garbage': len(gc.garbage),
                    'gc_count0': counts[0],
                    'gc_count1': counts[1],
                    'gc_count2': counts[2],

                    # Add the length of the most relevant globals
                    'NEGOTIATE_SERVER.queue': len(NEGOTIATE_SERVER.queue),
                    'NEGOTIATE_SERVER.known': len(NEGOTIATE_SERVER.known),
                    'NEGOTIATE_SERVER_BITTORRENT.peers': \
                        len(NEGOTIATE_SERVER_BITTORRENT.peers),
                    'NEGOTIATE_SERVER_SPEEDTEST.clients': \
                        len(NEGOTIATE_SERVER_SPEEDTEST.clients),
                    'DNS_CACHE': len(DNS_CACHE),
                    'POLLER.tasks': len(POLLER.tasks),
                    'POLLER.pending': len(POLLER.pending),
                    'POLLER.readset': len(POLLER.readset),
                    'POLLER.writeset': len(POLLER.writeset),
                    'LOG._queue': len(LOG._queue),
                    'CONFIG.conf': len(CONFIG.conf),
                    'NOTIFIER._timestamps': len(NOTIFIER._timestamps),
                    'NOTIFIER._subscribers': len(NOTIFIER._subscribers),
                    'NOTIFIER._tofire': len(NOTIFIER._tofire),
                    'STATE._events': len(STATE._events),
                   }

        elif request.uri == '/debugmem/garbage':
            body = [str(obj) for obj in gc.garbage]

        elif request.uri == '/debugmem/saveall':
            enable = json.load(request.body)
            flags = gc.get_debug()
            if enable:
                flags |= gc.DEBUG_SAVEALL
            else:
                flags &= ~gc.DEBUG_SAVEALL
            gc.set_debug(flags)
            body = enable

        elif request.uri.startswith('/debugmem/types'):
            if request.uri.startswith('/debugmem/types/'):
                typename = request.uri.replace('/debugmem/types/', '')
                objects = objgraph.by_type(typename)
                body = [str(obj) for obj in objects]
            else:
                body = objgraph.typestats()

        else:
            body = None

        if body is not None:
            body = json.dumps(body, indent=4, sort_keys=True)
            response.compose(code="200", reason="Ok", body=body,
                             mimetype="application/json")
        else:
            response.compose(code="404", reason="Not Found")

        stream.send_response(request, response)

class ServerSideAPI(ServerHTTP):
    """ Implements server-side API for Nagios plugin """

    def process_request(self, stream, request):
        """ Process HTTP request and return response """

        if request.uri == "/sapi":
            request.uri = "/sapi/"

        response = Message()

        if request.uri == "/sapi/":
            body = '["/sapi/", "/sapi/state"]'
            response.compose(code="200", reason="Ok", body=body,
                             mimetype="application/json")
        elif request.uri == "/sapi/state":
            body = '{"queue_len_cur": %d}' % len(NEGOTIATE_SERVER.queue)
            response.compose(code="200", reason="Ok", body=body,
                             mimetype="application/json")
        else:
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
    'server.debug': False,
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
        'server.debug': 'Run the localhost-only debug server',
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
        negotiate.run(POLLER, conf)

    if conf["server.bittorrent"]:
        conf["bittorrent.listen"] = True
        conf["bittorrent.negotiate"] = True
        bittorrent.run(POLLER, conf)

    if conf['server.speedtest']:
        #conf['speedtest.listen'] = 1           # Not yet
        #conf['speedtest.negotiate'] = 1        # Not yet
        neubot.speedtest.wrapper.run(POLLER, conf)

    # Migrating from old style to new style
    if conf["server.rendezvous"]:
        #conf["rendezvous.listen"] = True       # Not yet
        neubot.rendezvous.server.run(POLLER, conf)

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
    # functionalities.
    #
    if conf["server.sapi"]:
        server = ServerSideAPI(POLLER)
        server.configure(conf)
        HTTP_SERVER.register_child(server, "/sapi")

    #
    # Create localhost-only debug server
    #
    if CONFIG['server.debug']:
        LOG.info('server: Starting debug server at 127.0.0.1:9774')
        server = DebugAPI(POLLER)
        server.configure(conf)
        server.listen(('127.0.0.1', 9774))

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
