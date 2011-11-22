# neubot/rendezvous/server.py

#
# Copyright (c) 2010-2011 Simone Basso <bassosimone@gmail.com>,
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

import StringIO
import random
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.config import CONFIG
from neubot.database import DATABASE
from neubot.database import table_geoloc
from neubot.http.message import Message
from neubot.http.server import HTTP_SERVER
from neubot.http.server import ServerHTTP
from neubot.log import LOG
from neubot.net.poller import POLLER
from neubot.rendezvous.geoip_wrapper import Geolocator
from neubot.rendezvous import compat

from neubot.main import common
from neubot import marshal
from neubot import system
from neubot import utils

from neubot.utils.version import LibVersion

GEOLOCATOR = Geolocator()

class ServerRendezvous(ServerHTTP):

    def configure(self, conf):
        conf["http.server.rootdir"] = ""
        ServerHTTP.configure(self, conf)

    def process_request(self, stream, request):
        m = marshal.unmarshal_object(request.body.read(),
          "application/xml", compat.RendezvousRequest)

        m1 = compat.RendezvousResponse()

        version = self.conf["rendezvous.server.update_version"]

        #
        # Don't offer a release candidate update if the user is not
        # running a release candidate as well and viceversa.
        #
        if (("-rc" in version and "-rc" in m.version) or
          (not "-rc" in version and not "-rc" in m.version)):
            if m.version and LibVersion.compare(version, m.version) > 0:
                m1.update["uri"] = self.conf["rendezvous.server.update_uri"]
                m1.update["version"] = version

        #
        # Select test server address.
        # The default test server is the master server itself.
        # If we know the country, lookup the list of servers for
        # that country in the database.
        # We only redirect to other servers clients that have
        # agreed to give us the permission to share, in order
        # to be compliant with M-Lab policy.
        # If there are no servers for that country, register
        # the master server for the country so that we can notice
        # we have new users and can take the proper steps to
        # deploy nearby servers.
        #
        server = self.conf.get("rendezvous.server.default",
                               "master.neubot.org")
        LOG.debug("* default test server: %s" % server)
        if m.privacy_informed != 0 and m.privacy_can_collect != 0 \
                and m.privacy_can_share != 0:
            agent_address = stream.peername[0]
            country = GEOLOCATOR.lookup_country(agent_address)
            if country:
                servers = table_geoloc.lookup_servers(DATABASE.connection(),
                                                      country)
                if not servers:
                    LOG.info("* learning new country: %s" % country)
                    table_geoloc.insert_server(DATABASE.connection(),
                                               country, server)
                    servers = [server]
                server = random.choice(servers)
                LOG.debug("* selected test server: %s" % server)

        if "speedtest" in m.accept:
            m1.available["speedtest"] = [ "http://%s/speedtest" % server ]

        if "bittorrent" in m.accept:
            m1.available["bittorrent"] = [ "http://%s/" % server ]

        #
        # Neubot <=0.3.7 expects to receive an XML document while
        # newer Neubots want a JSON.  I hope old clients will upgrade
        # pretty soon.
        #
        if m.version and LibVersion.compare(m.version, "0.3.7") >= 0:
            s = marshal.marshal_object(m1, "application/json")
            mimetype = "application/json"
        else:
            s = compat.adhoc_marshaller(m1)
            mimetype = "text/xml"

        stringio = StringIO.StringIO()
        stringio.write(s)
        stringio.seek(0)

        response = Message()
        response.compose(code="200", reason="Ok",
          mimetype=mimetype, body=stringio)
        stream.send_response(request, response)

CONFIG.register_defaults({
    "rendezvous.server.address": "0.0.0.0",
    "rendezvous.server.daemonize": True,
    "rendezvous.server.ports": "9773,8080",
    "rendezvous.server.update_uri": "http://www.neubot.org/download",
    "rendezvous.server.update_version": common.VERSION,
    "rendezvous.geoip_wrapper.country_database": "/usr/local/share/GeoIP/GeoIP.dat",
    "rendezvous.server.default": "master.neubot.org",
})

def run(poller, conf):
    """ Load MaxMind database and register our child server """

    GEOLOCATOR.open_or_die()
    LOG.info("This product includes GeoLite data created by MaxMind, "
             "available from <http://www.maxmind.com/>.")

    server = ServerRendezvous(None)
    server.configure(conf)
    HTTP_SERVER.register_child(server, "/rendezvous")

def main(args):

    CONFIG.register_descriptions({
        "rendezvous.server.address": "Set rendezvous server address",
        "rendezvous.server.daemonize": "Enable daemon behavior",
        "rendezvous.server.ports": "List of rendezvous server ports",
        "rendezvous.server.update_uri": "Where to download updates from",
        "rendezvous.server.update_version": "Update Neubot version number",
        "rendezvous.geoip_wrapper.country_database": "Path of the GeoIP country database",
        "rendezvous.server.default": "Default test server to use",
    })

    common.main("rendezvous.server", "Rendezvous server", args)
    conf = CONFIG.copy()

    HTTP_SERVER.configure(conf)
    for port in conf["rendezvous.server.ports"].split(","):
        HTTP_SERVER.listen((conf["rendezvous.server.address"], int(port)))

    # Really start this module
    run(POLLER, conf)

    if conf["rendezvous.server.daemonize"]:
        system.change_dir()
        system.go_background()
        LOG.redirect()

    system.drop_privileges(LOG.error)
    POLLER.loop()

if __name__ == "__main__":
    main(sys.argv)
