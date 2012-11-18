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

''' Rendezvous server '''

import random
import sys
import logging

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.config import CONFIG
from neubot.database import DATABASE
from neubot.database import table_geoloc
from neubot.http.message import Message
from neubot.http.server import HTTP_SERVER
from neubot.http.server import ServerHTTP
from neubot.net.poller import POLLER
from neubot.rendezvous.geoip_wrapper import Geolocator
from neubot.rendezvous import compat

from neubot.main import common
from neubot import marshal
from neubot import privacy

from neubot import utils_version

GEOLOCATOR = Geolocator()

class ServerRendezvous(ServerHTTP):

    ''' Rendezvous server '''

    def configure(self, conf):
        ''' Configure rendezvous server '''

        #
        # Ensure that the rootdir is empty, but do that on
        # a copy of the original settings, just in case any
        # other module needs the original setting.
        #
        conf = conf.copy()
        conf["http.server.rootdir"] = ""

        ServerHTTP.configure(self, conf)

    def process_request(self, stream, request):
        ''' Process rendezvous request '''

        if request['content-type'] == 'application/json':
            ibody = marshal.unmarshal_object(request.body.read(),
              'application/json', compat.RendezvousRequest)
        else:
            ibody = marshal.unmarshal_object(request.body.read(),
              "application/xml", compat.RendezvousRequest)

        obody = compat.RendezvousResponse()

        #
        # If we don't say anything the rendezvous server is not
        # going to prompt for updates.  We need to specify the
        # updated version number explicitly when we start it up.
        # This should guarantee that we do not advertise -rc
        # releases and other weird things.
        #
        version = self.conf["rendezvous.server.update_version"]
        if version and ibody.version:
            diff = utils_version.compare(version, ibody.version)
            logging.debug('rendezvous: version=%s ibody.version=%s diff=%f', 
                      version, ibody.version, diff)
            if diff > 0:
                obody.update["uri"] = 'http://neubot.org/'
                obody.update["version"] = version

        #
        # Select test server address.
        # The default test server is the master server itself.
        # If we know the country, lookup the list of servers for
        # that country in the database.
        # We only redirect to other servers clients that have
        # agreed to give us the permission to publish, in order
        # to be compliant with M-Lab policy.
        # If there are no servers for that country, register
        # the master server for the country so that we can notice
        # we have new users and can take the proper steps to
        # deploy nearby servers.
        #
        server = self.conf.get("rendezvous.server.default",
                               "master.neubot.org")
        logging.debug("* default test server: %s", server)

        #
        # Backward compatibility: the variable name changed from
        # can_share to can_publish after Neubot 0.4.5
        #
        request_body = ibody.__dict__.copy()
        if 'privacy_can_share' in request_body:
            request_body['privacy_can_publish'] = request_body[
              'privacy_can_share']
            del request_body['privacy_can_share']

        # Redirect IFF have ALL privacy permissions
        if privacy.count_valid(request_body, 'privacy_') == 3:
            agent_address = stream.peername[0]
            country = GEOLOCATOR.lookup_country(agent_address)
            if country:
                servers = table_geoloc.lookup_servers(DATABASE.connection(),
                                                      country)
                if not servers:
                    logging.info("* learning new country: %s", country)
                    table_geoloc.insert_server(DATABASE.connection(),
                                               country, server)
                    servers = [server]
                server = random.choice(servers)
                logging.info("rendezvous_server: %s[%s] -> %s", agent_address,
                         country, server)

        else:
            logging.warning('rendezvous_server: cannot redirect to M-Lab: %s',
                        request_body)

        #
        # We require at least informed and can_collect since 0.4.4
        # (released 25 October 2011), so stop clients with empty
        # privacy settings, who were still using master.
        #
        if privacy.collect_allowed(request_body):
            #
            # Note: Here we will have problems if we store unquoted
            # IPv6 addresses into the database.  Because the resulting
            # URI won't be valid.
            #
            if "speedtest" in ibody.accept:
                obody.available["speedtest"] = [
                    "http://%s/speedtest" % server ]
            if "bittorrent" in ibody.accept:
                obody.available["bittorrent"] = [
                    "http://%s/" % server ]

        #
        # Neubot <=0.3.7 expects to receive an XML document while
        # newer Neubots want a JSON.  I hope old clients will upgrade
        # pretty soon.
        #
        if ibody.version and utils_version.compare(ibody.version, "0.3.7") >= 0:
            body = marshal.marshal_object(obody, "application/json")
            mimetype = "application/json"
        else:
            body = compat.adhoc_marshaller(obody)
            mimetype = "text/xml"

        response = Message()
        response.compose(code="200", reason="Ok",
          mimetype=mimetype, body=body)
        stream.send_response(request, response)

CONFIG.register_defaults({
    "rendezvous.server.address": "",
    "rendezvous.server.ports": "9773,8080",
    "rendezvous.server.update_version": "0.4.15.6",
    "rendezvous.geoip_wrapper.country_database":                        \
        "/usr/local/share/GeoIP/GeoIP.dat",
    "rendezvous.server.default": "master.neubot.org",
})

def run():
    """ Load MaxMind database and register our child server """

    GEOLOCATOR.open_or_die()
    logging.info("This product includes GeoLite data created by MaxMind, "
                 "available from <http://www.maxmind.com/>.")

    server = ServerRendezvous(None)
    server.configure(CONFIG)
    HTTP_SERVER.register_child(server, "/rendezvous")

def main(args):
    ''' Main function '''

    CONFIG.register_descriptions({
        "rendezvous.server.address": "Set rendezvous server address",
        "rendezvous.server.ports": "List of rendezvous server ports",
        "rendezvous.server.update_version": "Update Neubot version number",
        "rendezvous.geoip_wrapper.country_database":                    \
          "Path of the GeoIP country database",
        "rendezvous.server.default": "Default test server to use",
    })

    common.main("rendezvous.server", "Rendezvous server", args)
    conf = CONFIG.copy()

    HTTP_SERVER.configure(conf)
    for port in conf["rendezvous.server.ports"].split(","):
        HTTP_SERVER.listen((conf["rendezvous.server.address"], int(port)))

    # Really start this module
    run()

    POLLER.loop()

if __name__ == "__main__":
    main(sys.argv)
