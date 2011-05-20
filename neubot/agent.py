# neubot/agent.py

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

import random
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.config import CONFIG
from neubot.http.server import ServerHTTP
from neubot.api.server import ServerAPI
from neubot.rendezvous.client import ClientRendezvous
from neubot.net.poller import POLLER
from neubot.rootdir import WWW
from neubot.log import LOG
from neubot import system
from neubot import boot

CONFIG.register_defaults({
    "agent.api": True,
    "agent.api.address": "127.0.0.1",
    "agent.api.port": 9774,
    "agent.daemonize": True,
    "agent.interval": 0,
    "agent.master": "master.neubot.org",
    "agent.rendezvous": True,
})
CONFIG.register_descriptions({
    "agent.api": "Enable API server",
    "agent.api.address": "Set API server address",
    "agent.api.port": "Set API server port",
    "agent.daemonize": "Enable daemon behavior",
    "agent.interval": "Set rendezvous interval (0 = random)",
    "agent.master": "Set master server address",
    "agent.rendezvous": "Enable rendezvous client",
})

def main(args):
    boot.common("agent", "Run in background, periodically run tests", args)

    conf = CONFIG.copy()

    if not conf["agent.interval"]:
        conf["agent.interval"] = 1380 + random.randrange(0, 240)

    uri = "http://%s:9773/rendezvous" % conf["agent.master"]

    if conf["agent.api"]:
        server = ServerHTTP(POLLER)
        LOG.debug("* API server root directory: %s" % WWW)
        server.configure({"http.server.rootdir": WWW, "http.server.ssi": True,
          "http.server.bind_or_die": True})
        server.register_child(ServerAPI(POLLER), "/api")
        server.listen((conf["agent.api.address"],
                       conf["agent.api.port"]))

    if conf["agent.daemonize"]:
        system.change_dir()
        system.go_background()
        system.write_pidfile()
        LOG.redirect()

    system.drop_privileges()

    if conf["agent.rendezvous"]:
        client = ClientRendezvous(POLLER)
        conf["rendezvous.client.uri"] = uri
        conf["rendezvous.client.interval"] = conf["agent.interval"]
        client.configure(conf)
        client.connect_uri()

    POLLER.loop()

if __name__ == "__main__":
    main(sys.argv)
