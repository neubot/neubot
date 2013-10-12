# mod_dash/neubot_module.py

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

""" The entry point of the DASH module """

import logging

from mod_dash.client_negotiate import DASHNegotiateClient
from mod_dash.server_negotiate import DASHNegotiateServer
from mod_dash.server_glue import DASHServerGlue

def _run_test(message):
    """ Run the DASH test """
    client = DASHNegotiateClient(message["poller"])
    client.configure(message["conf"])
    client.connect((message["address"], message["port"]))

def mod_load(context, message):
    """ Invoked when the module loads """
    logging.debug("dash: init for context '%s'... in progress", context)

    if context == "server":

        # Adapted from mod_dash/main.py

        negotiate_server = message["negotiate_server"]
        http_server = message["http_server"]

        logging.debug("dash: register negotiate server module... in progress")

        dash_negotiate_server = DASHNegotiateServer()
        negotiate_server.register_module("dash", dash_negotiate_server)

        logging.debug("dash: register negotiate server module... complete")
        logging.debug("dash: register HTTP server child... in progress")

        dash_server = DASHServerGlue(http_server.poller, dash_negotiate_server)
        dash_server.configure(http_server.conf.copy())
        http_server.register_child(dash_server, "/dash")

        logging.debug("dash: register HTTP server child... complete")

    elif context == "register_test":
        message["dash"] = {}
        message["dash"]["discover_method"] = "mlab-ns"
        message["dash"]["discover_policy"] = "random"
        message["dash"]["test_func"] = _run_test

    elif context == "load_subcommand":
        message["dash"] = "mod_dash.main"

    else:
        logging.warning("dash: unknown context: %s", context)

    logging.debug("dash: init for context '%s'... complete", context)
