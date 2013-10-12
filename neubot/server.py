# neubot/server.py

#
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

"""
This module implements the command that manages server-side
components, including the rendezvous server and, for each test,
the negotiate server and the test server.
"""

import gc
import getopt
import sys
import logging
import signal

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.http.message import Message
from neubot.http.server import HTTP_SERVER
from neubot.http.server import ServerHTTP
from neubot.net.poller import POLLER

from neubot.negotiate.server import NEGOTIATE_SERVER
from neubot.negotiate.server_speedtest import NEGOTIATE_SERVER_SPEEDTEST
from neubot.negotiate.server_bittorrent import NEGOTIATE_SERVER_BITTORRENT
from neubot.notify import NOTIFIER

from neubot.compat import json
from neubot.database import DATABASE
from neubot.debug import objgraph
from neubot.config import CONFIG
from neubot.backend import BACKEND
from neubot.log import LOG
from neubot.raw_srvr_glue import RAW_SERVER_EX

from neubot import bittorrent
from neubot import negotiate
from neubot import system
from neubot import utils_modules
from neubot import utils_posix

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
                    'POLLER.readset': len(POLLER.readset),
                    'POLLER.writeset': len(POLLER.writeset),
                    'LOG._queue': len(LOG._queue),
                    'CONFIG.conf': len(CONFIG.conf),
                    'NOTIFIER._timestamps': len(NOTIFIER._timestamps),
                    'NOTIFIER._subscribers': len(NOTIFIER._subscribers),
                    'NOTIFIER._tofire': len(NOTIFIER._tofire),
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

SETTINGS = {
    "server.bittorrent": True,
    "server.daemonize": True,
    "server.datadir": '',
    'server.debug': False,
    "server.negotiate": True,
    "server.raw": True,
    "server.rendezvous": False,         # Not needed on the random server
    "server.sapi": True,
    "server.speedtest": True,
}

USAGE = '''\
usage: neubot server [-dv] [-A address] [-b backend] [-D macro=value]

valid backends:
  mlab   Saves results as compressed json files (this is the default)
  neubot Saves results in sqlite3 database
  null   Do not save results but pretend to do so

valid defines:
  server.bittorrent Set to nonzero to enable BitTorrent server (default: 1)
  server.daemonize  Set to nonzero to run in the background (default: 1)
  server.datadir    Set data directory (default: LOCALSTATEDIR/neubot)
  server.debug      Set to nonzero to enable debug API (default: 0)
  server.negotiate  Set to nonzero to enable negotiate server (default: 1)
  server.raw        Set to nonzero to enable RAW server (default: 1)
  server.rendezvous Set to nonzero to enable rendezvous server (default: 0)
  server.sapi       Set to nonzero to enable nagios API (default: 1)
  server.speedtest  Set to nonzero to enable speedtest server (default: 1)'''

VALID_MACROS = ('server.bittorrent', 'server.daemonize', 'server.datadir',
                'server.debug', 'server.negotiate', 'server.raw',
                'server.rendezvous', 'server.sapi', 'server.speedtest')

def main(args):
    """ Starts the server module """

    if not system.has_enough_privs():
        sys.exit('FATAL: you must be root')

    try:
        options, arguments = getopt.getopt(args[1:], 'A:b:D:dv')
    except getopt.error:
        sys.exit(USAGE)
    if arguments:
        sys.exit(USAGE)

    address = ':: 0.0.0.0'
    backend = 'mlab'
    for name, value in options:
        if name == '-A':
            address = value
        elif name == '-b':
            backend = value
        elif name == '-D':
            name, value = value.split('=', 1)
            if name not in VALID_MACROS:
                sys.exit(USAGE)
            if name != 'server.datadir':  # XXX
                value = int(value)
            SETTINGS[name] = value
        elif name == '-d':
            SETTINGS['server.daemonize'] = 0
        elif name == '-v':
            CONFIG['verbose'] = 1

    logging.debug('server: using backend: %s... in progress', backend)
    if backend == 'mlab':
        BACKEND.datadir_init(None, SETTINGS['server.datadir'])
        BACKEND.use_backend('mlab')
    elif backend == 'neubot':
        DATABASE.connect()
        BACKEND.use_backend('neubot')
    elif backend == 'volatile':
        BACKEND.use_backend('volatile')
    else:
        BACKEND.use_backend('null')
    logging.debug('server: using backend: %s... complete', backend)

    for name, value in SETTINGS.items():
        CONFIG[name] = value

    conf = CONFIG.copy()

    #
    # Configure our global HTTP server and make
    # sure that we don't provide filesystem access
    # even by mistake.
    #
    conf["http.server.rootdir"] = ""
    HTTP_SERVER.configure(conf)

    #
    # New-new style: don't bother with abstraction and start the fucking
    # server by invoking its listen() method.
    #
    if CONFIG['server.raw']:
        logging.debug('server: starting raw server... in progress')
        RAW_SERVER_EX.listen((address, 12345),
          CONFIG['prefer_ipv6'], 0, '')
        logging.debug('server: starting raw server... complete')

    #
    # New-style modules are started just setting a
    # bunch of conf[] variables and then invoking
    # their run() method in order to kick them off.
    # This is now depricated in favor of the new-
    # new style described above.
    #

    if conf["server.negotiate"]:
        negotiate.run(POLLER, conf)

    if conf["server.bittorrent"]:
        conf["bittorrent.address"] = address
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
        neubot.rendezvous.server.run()

    #
    # Historically Neubot runs on port 9773 and
    # 8080 but we would like to switch to port 80
    # in the long term period, because it's rare
    # that they filter it.
    # OTOH it looks like it's not possible to
    # do that easily w/ M-Lab because the port
    # is already taken.
    #
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
        logging.info('server: Starting debug server at {127.0.0.1,::1}:9774')
        server = DebugAPI(POLLER)
        server.configure(conf)
        server.listen(('127.0.0.1 ::1', 9774))

    # Probe existing modules and ask them to attach to us
    utils_modules.modprobe(None, "server", {
        "http_server": HTTP_SERVER,
        "negotiate_server": NEGOTIATE_SERVER,
    })

    #
    # Go background and drop privileges,
    # then enter into the main loop.
    #
    if conf["server.daemonize"]:
        LOG.redirect()
        system.go_background()

    sigterm_handler = lambda signo, frame: POLLER.break_loop()
    signal.signal(signal.SIGTERM, sigterm_handler)

    logging.info('Neubot server -- starting up')
    system.drop_privileges()
    POLLER.loop()

    logging.info('Neubot server -- shutting down')
    utils_posix.remove_pidfile('/var/run/neubot.pid')

if __name__ == "__main__":
    main(sys.argv)
