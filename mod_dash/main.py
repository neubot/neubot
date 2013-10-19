# mod_dash/main.py

#
# Copyright (c) 2013
#     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#     and Simone Basso <bassosimone@gmail.com>
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

""" The MPEG DASH test main() """

# Adapted from neubot/raw.py

import getopt
import logging
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from mod_dash.client_smpl import DASHClientSmpl
from mod_dash.client_negotiate import DASHNegotiateClient
from mod_dash.client_negotiate import DASH_RATES
from mod_dash.server_glue import DASHServerGlue
from mod_dash.server_negotiate import DASHNegotiateServer
from mod_dash.server_smpl import DASHServerSmpl

from neubot.http.server import ServerHTTP
from neubot.negotiate.server import NegotiateServer

from neubot.backend import BACKEND
from neubot.config import CONFIG
from neubot.poller import POLLER

from neubot import log
from neubot import runner_clnt

USAGE = """\
usage: neubot dash [-6flnv] [-A address] [-b backend] [-d datadir] [-p port]"""

def main(args):
    """ Main function """
    try:
        options, arguments = getopt.getopt(args[1:], "6A:b:d:flnp:v")
    except getopt.error:
        sys.exit(USAGE)
    if arguments:
        sys.exit(USAGE)

    prefer_ipv6 = 0
    address = "127.0.0.1"
    backend = "volatile"
    datadir = None  # means: pick the default
    force = 0
    listen = 0
    negotiate = 1
    port = 80
    noisy = 0
    for name, value in options:
        if name == "-6":
            prefer_ipv6 = 1
        elif name == "-A":
            address = value
        elif name == "-b":
            backend = value
        elif name == "-d":
            datadir = value
        elif name == "-f":
            force = 1
        elif name == "-l":
            listen = 1
        elif name == "-n":
            negotiate = 0
        elif name == "-p":
            port = int(value)
        elif name == "-v":
            noisy = 1

    if noisy:
        log.set_verbose()

    conf = CONFIG.copy()

    BACKEND.use_backend(backend)
    BACKEND.datadir_init(None, datadir)

    if listen:
        if not negotiate:
            server = DASHServerSmpl(POLLER)
            server.configure(conf)
            server.listen((address, port))

        else:
            # Code adapted from neubot/server.py

            conf["http.server.rootdir"] = ""
            server = ServerHTTP(POLLER)
            server.configure(conf)
            server.listen((address, port))

            negotiate_server = NegotiateServer(POLLER)
            negotiate_server.configure(conf)
            server.register_child(negotiate_server, "/negotiate")
            server.register_child(negotiate_server, "/collect")

            dash_negotiate_server = DASHNegotiateServer()
            negotiate_server.register_module("dash", dash_negotiate_server)

            dash_server = DASHServerGlue(POLLER, dash_negotiate_server)
            dash_server.configure(conf)
            server.register_child(dash_server, "/dash")

    elif not force:
        result = runner_clnt.runner_client(CONFIG["agent.api.address"],
          CONFIG["agent.api.port"], CONFIG["verbose"], "dash")
        if result:
            sys.exit(0)
        logging.warning("dash: failed to contact Neubot; is Neubot running?")
        sys.exit(1)

    else:
        if negotiate:
            client = DASHNegotiateClient(POLLER)
        else:
            client = DASHClientSmpl(POLLER, None, DASH_RATES)
        client.configure(conf)
        client.connect((address, port))

    POLLER.loop()

if __name__ == "__main__":
    main(sys.argv)
