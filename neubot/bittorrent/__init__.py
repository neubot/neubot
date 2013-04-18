# neubot/bittorrent/__init__.py

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
 This file contains the external entry points to
 the bittorrent module, that tries to emulate the
 behavior of a bittorrent peer.
'''

import getopt
import logging
import os
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.bittorrent.client import BitTorrentClient
from neubot.bittorrent.peer import PeerNeubot
from neubot.bittorrent.server import ServerPeer
from neubot.http.server import HTTP_SERVER
from neubot.net.poller import POLLER

from neubot.backend import BACKEND
from neubot.bittorrent import config
from neubot.config import CONFIG
from neubot.database import DATABASE
from neubot.notify import NOTIFIER

from neubot import log
from neubot import negotiate
from neubot import privacy
from neubot import runner_clnt
from neubot import utils

def run(poller, conf):
    '''
     This function is invoked when Neubot is already
     running and you want to leverage some functionalities
     of this module.
    '''

    # Make sure the conf makes sense before we go
    config.finalize_conf(conf)

    if conf["bittorrent.listen"]:
        if conf["bittorrent.negotiate"]:

            #
            # We assume that the caller has already started
            # the HTTP server and that it contains our negotiator
            # so here we just bring up the test server.
            #
            server = ServerPeer(poller)
            server.configure(conf)
            server.listen((conf["bittorrent.address"],
                           conf["bittorrent.port"]))

        else:
            server = PeerNeubot(poller)
            server.configure(conf)
            server.listen((conf["bittorrent.address"],
                           conf["bittorrent.port"]))

    else:

        #
        # Make sure there is someone ready to receive the
        # "testdone" event.  If there is noone it is a bug
        # none times out of ten.
        #
        if not NOTIFIER.is_subscribed("testdone"):
            log.oops("The 'testdone' event is not subscribed")

        if conf["bittorrent.negotiate"]:
            client = BitTorrentClient(poller)
            client.configure(conf)

            #
            # The rendezvous client uses this hidden variable
            # to pass us the URI to connect() to (the rendezvous
            # returns an URI, not address and port).
            #
            uri = None
            if "bittorrent._uri" in conf:
                uri = conf["bittorrent._uri"]

            client.connect_uri(uri)

        else:
            client = PeerNeubot(poller)
            client.configure(conf)
            client.connect((conf["bittorrent.address"],
                           conf["bittorrent.port"]))

def main(args):
    '''
     This function is invoked when the user wants
     to run precisely this module.
    '''

    try:
        options, arguments = getopt.getopt(args[1:], '6A:fp:v')
    except getopt.error:
        sys.exit('usage: neubot bittorrent [-6fv] [-A address] [-p port]')
    if arguments:
        sys.exit('usage: neubot bittorrent [-6fv] [-A address] [-p port]')

    prefer_ipv6 = 0
    address = 'master.neubot.org'
    force = 0
    port = 6881
    noisy = 0
    for name, value in options:
        if name == '-6':
            prefer_ipv6 = 1
        elif name == '-A':
            address = value
        elif name == '-f':
            force = 1
        elif name == '-p':
            port = int(value)
        elif name == '-v':
            noisy = 1

    if os.path.isfile(DATABASE.path):
        DATABASE.connect()
        CONFIG.merge_database(DATABASE.connection())
    else:
        logging.warning('bittorrent: database file is missing: %s',
                        DATABASE.path)
        BACKEND.use_backend('null')
    if noisy:
        log.set_verbose()

    config.register_descriptions()  # Needed?
    conf = CONFIG.copy()
    config.finalize_conf(conf)

    conf['bittorrent.address'] = address
    conf['bittorrent.port'] = port
    conf['prefer_ipv6'] = prefer_ipv6

    if not force:
        if runner_clnt.runner_client(conf["agent.api.address"],
                                     conf["agent.api.port"],
                                     CONFIG['verbose'],
                                     "bittorrent"):
            sys.exit(0)
        logging.warning(
          'bittorrent: failed to contact Neubot; is Neubot running?')
        sys.exit(1)

    logging.info('bittorrent: run the test in the local process context...')

    #
    # When we're connecting to a remote host to perform a test
    # we want Neubot to quit at the end of the test.  When this
    # happens the test code publishes the "testdone" event, so
    # here we prepare to intercept the event and break our main
    # loop.
    #
    NOTIFIER.subscribe("testdone", lambda event, ctx: POLLER.break_loop())
    run(POLLER, conf)
    POLLER.loop()

if __name__ == "__main__":
    main(sys.argv)
