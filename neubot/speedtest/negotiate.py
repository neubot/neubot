# neubot/speedtest/negotiate.py

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

import StringIO

from neubot.config import CONFIG
from neubot.database import DATABASE
from neubot.database import table_speedtest
from neubot.http.message import Message
from neubot.http.server import ServerHTTP
from neubot.log import LOG
from neubot.net.poller import POLLER
from neubot.notify import NOTIFIER
from neubot.speedtest import compat
from neubot.speedtest.server import ServerTest
from neubot.speedtest.session import TRACKER

from neubot import boot
from neubot import marshal
from neubot import privacy
from neubot import system
from neubot import utils

RENEGOTIATE = "renegotiate"

#
# The current implementation wraps the TestServer and this
# is fine.  But it will be more scalable and clean to share
# the TRACKER between the TestServer and the Negotiator,
# and the use a common ServerHTTP for both.
#
class ServerSpeedtest(ServerHTTP):
    def __init__(self, poller):
        ServerHTTP.__init__(self, poller)
        self.begin_test = 0
        POLLER.sched(3, self._speedtest_check_timeout)
        self.test_server = ServerTest(poller)

    def configure(self, conf, measurer=None):
        conf["http.server.rootdir"] = ""
        ServerHTTP.configure(self, conf, measurer)

    def got_request_headers(self, stream, request):
        ret = True
        TRACKER.register_connection(stream, request["authorization"])

        if request.uri == "/speedtest/upload":
            request.body.write = lambda octets: None

        only_auth = self.conf.get("speedtest.negotiate.auth_only", False)
        if (only_auth and request.uri != "/speedtest/negotiate" and
          not TRACKER.session_active(request["authorization"])):
            LOG.warning("* Connection %s: Forbidden" % stream.logname)
            ret = False

        return ret

    def process_request(self, stream, request):
        if request.uri == "/speedtest/negotiate":
            self.do_negotiate(stream, request)
        elif request.uri == "/speedtest/collect":
            self.do_collect(stream, request)
        else:
            self.test_server.process_request(stream, request)

    #
    # A client is allowed to access restricted URIs if: (i) either
    # only_auth is False, (ii) or the authorization token is valid.
    # Here we decide how to give clients authorization tokens.
    # We start with a very simple (to implement) rule.  We give the
    # client a token and we remove the token after 30+ seconds, or
    # when the authorized client uploads the results.
    # Wish list:
    # - Avoid client synchronization
    #

    def _do_renegotiate(self, event, atuple):
        stream, request = atuple
        self.do_negotiate(stream, request, True)

    def _speedtest_check_timeout(self, *args, **kwargs):
        POLLER.sched(3, self._speedtest_check_timeout)
        if TRACKER.session_prune():
            NOTIFIER.publish(RENEGOTIATE)

    def _speedtest_complete(self, request):
        TRACKER.session_delete(request["authorization"])
        NOTIFIER.publish(RENEGOTIATE)

    def do_negotiate(self, stream, request, nodelay=False):
        session = TRACKER.session_negotiate(request["authorization"])
        if not request["authorization"]:
            request["authorization"] = session.identifier

        #
        # XXX make sure we track ALSO the first connection of the
        # session (which is assigned an identifier in session_negotiate)
        # or, should this connection fail, we would not be able to
        # propagate quickly this information because unregister_connection
        # would not find an entry in self.connections{}.
        #
        if session.negotiations == 1:
            TRACKER.register_connection(stream, request["authorization"])
            nodelay = True

        if not session.active:
            if not nodelay:
                NOTIFIER.subscribe(RENEGOTIATE, self._do_renegotiate,
                          (stream, request), True)
                return

        m1 = compat.SpeedtestNegotiate_Response()
        m1.authorization = session.identifier
        m1.unchoked = session.active
        m1.queuePos = session.queuepos
        m1.publicAddress = stream.peername[0]
        s = marshal.marshal_object(m1, "text/xml")

        stringio = StringIO.StringIO(s)
        response = Message()
        response.compose(code="200", reason="Ok",
         body=stringio, mimetype="application/xml")
        stream.send_response(request, response)

    def do_collect(self, stream, request):
        self._speedtest_complete(request)

        s = request.body.read()
        m = marshal.unmarshal_object(s, "text/xml", compat.SpeedtestCollect)

        if privacy.collect_allowed(m):
            table_speedtest.insertxxx(DATABASE.connection(), m)

        response = Message()
        response.compose(code="200", reason="Ok")
        stream.send_response(request, response)

    def connection_lost(self, stream):
        TRACKER.unregister_connection(stream)
        NOTIFIER.publish(RENEGOTIATE)

def main(args):

    CONFIG.register_defaults({
        "speedtest.negotiate.address": "0.0.0.0",
        "speedtest.negotiate.auth_only": True,
        "speedtest.negotiate.daemonize": True,
        "speedtest.negotiate.port": "80",
    })
    CONFIG.register_descriptions({
        "speedtest.negotiate.address": "Address to listen to",
        "speedtest.negotiate.auth_only": "Enable doing tests for authorized clients only",
        "speedtest.negotiate.daemonize": "Enable going in background",
        "speedtest.negotiate.port": "Port to listen to",
    })

    boot.common("speedtest.negotiate", "Speedtest negotiation server", args)

    conf = CONFIG.copy()

    server = ServerSpeedtest(POLLER)
    server.configure(conf)
    server.listen((conf["speedtest.negotiate.address"],
                  conf["speedtest.negotiate.port"]))

    if conf["speedtest.negotiate.daemonize"]:
        system.change_dir()
        system.go_background()
        LOG.redirect()

    system.drop_privileges()
    POLLER.loop()
