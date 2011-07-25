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

#
# This file contains the external entry points to
# the bittorrent module, that tries to emulate the
# behavior of a bittorrent peer.
#

import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.bittorrent.client import BitTorrentClient
from neubot.bittorrent.peer import PeerNeubot
from neubot.bittorrent.server import ServerPeer
from neubot.http.server import HTTP_SERVER
from neubot.net.poller import POLLER

from neubot.bittorrent import config
from neubot.config import CONFIG
from neubot.log import LOG
from neubot.notify import NOTIFIER
from neubot.main import common

from neubot import system

#
# This function is invoked when Neubot is already
# running and you want to leverage some functionalities
# of this module.
#
def run(poller, conf):

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
            LOG.oops("The 'testdone' event is not subscribed")

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

#
# This function is invoked when the user wants
# to run precisely this module.
#
def main(args):

    config.register_descriptions()
    common.main("bittorrent", "Neubot BitTorrent module", args)
    conf = CONFIG.copy()
    config.finalize_conf(conf)

    if conf["bittorrent.listen"]:

        if conf["bittorrent.daemonize"]:
            system.change_dir()
            system.go_background()
            LOG.redirect()

        system.drop_privileges(LOG.error)

        #
        # If we need to negotiate and we're runing
        # standalone we also need to bring up the
        # global HTTP server.
        #
        if conf["bittorrent.negotiate"]:
            HTTP_SERVER.configure(conf)
            HTTP_SERVER.listen((conf["bittorrent.address"],
                               conf["bittorrent.negotiate.port"]))

    else:
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
