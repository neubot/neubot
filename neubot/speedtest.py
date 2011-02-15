# neubot/speedtest.py

#
# Copyright (c) 2010 Simone Basso <bassosimone@gmail.com>,
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

if __name__ == "__main__":
    from sys import path
    path.insert(0, ".")

from StringIO import StringIO
from neubot.database import database
from neubot.http.messages import Message
from neubot.utils import unit_formatter
from neubot.http.messages import compose
from neubot.http.clients import Client
from neubot.http.clients import ClientController
from neubot.net.poller import POLLER
from neubot.times import timestamp
from sys import stdout
from sys import argv
from neubot.log import LOG
from neubot import version
from getopt import GetoptError
from neubot.state import STATE
from getopt import getopt
from sys import stderr
from sys import exit

from neubot import pathnames
from collections import deque
from neubot.times import ticks
from neubot.notify import publish
from neubot.notify import subscribe
from neubot.notify import RENEGOTIATE
from neubot.utils import time_formatter
from ConfigParser import SafeConfigParser
from neubot.http.servers import Connection
from xml.etree.ElementTree import ElementTree
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement
from neubot.http.utils import nextstate
from neubot.http.utils import parse_range
from neubot.http.handlers import ERROR
from neubot.http.servers import Server
from neubot.utils import file_length
from neubot.utils import become_daemon
from time import time
from uuid import UUID
from uuid import uuid4

def XML_get_scalar(tree, name):
    elements = tree.findall(name)
    if len(elements) > 1:
        raise ValueError("More than one '%s' element" % name)
    if len(elements) == 0:
        return ""
    element = elements[0]
    return element.text

def XML_get_vector(tree, name):
    vector = []
    elements = tree.findall(name)
    for element in elements:
        vector.append(element.text)
    return vector

#
# <SpeedtestCollect>
#     <client>af5659e0-b2bd-4a4b-8062-e8437150f2c9</client>
#     <timestamp>1283790303</timestamp>
#     <internalAddress>192.168.0.3</internalAddress>
#     <realAddress>130.192.47.76</realAddress>
#     <remoteAddress>130.192.47.84</remoteAddress>
#     <connectTime>0.9</connectTime>
#     <latency>0.92</latency>
#     <downloadSpeed>23</downloadSpeed>
#     <downloadSpeed>22</downloadSpeed>
#     <uploadSpeed>7.0</uploadSpeed>
#     <uploadSpeed>7.1</uploadSpeed>
# </SpeedtestCollect>
#

class SpeedtestCollect:
    def __init__(self):
        self.client = ""
        self.timestamp = 0
        self.internalAddress = ""
        self.realAddress = ""
        self.remoteAddress = ""
        self.connectTime = []
        self.latency = []
        self.downloadSpeed = []
        self.uploadSpeed = []

    def parse(self, stringio):
        tree = ElementTree()
        try:
            tree.parse(stringio)
        except:
            raise ValueError("Can't parse XML body")
        else:
            self.client = XML_get_scalar(tree, "client")
            self.timestamp = XML_get_scalar(tree, "timestamp")
            self.internalAddress = XML_get_scalar(tree, "internalAddress")
            self.realAddress = XML_get_scalar(tree, "realAddress")
            self.remoteAddress = XML_get_scalar(tree, "remoteAddress")
            self.connectTime = XML_get_vector(tree, "connectTime")
            self.latency = XML_get_vector(tree, "latency")
            self.downloadSpeed = XML_get_vector(tree, "downloadSpeed")
            self.uploadSpeed = XML_get_vector(tree, "uploadSpeed")

#
# Code for speedtest server.  It's composed of two mixins.  The former
# implements the actual tests and the latter implements negotiation, and
# collection.
#

class _TestServerMixin(object):
    def __init__(self, config):
        self.config = config

    def do_latency(self, connection, request):
        response = Message()
        compose(response, code="200", reason="Ok")
        connection.reply(request, response)

    def do_download(self, connection, request):
        response = Message()
        # open
        try:
            body = open(self.config.path, "rb")
        except (IOError, OSError):
            LOG.exception()
            compose(response, code="500", reason="Internal Server Error")
            connection.reply(request, response)
            return
        # range
        if request["range"]:
            total = file_length(body)
            # parse
            try:
                first, last = parse_range(request)
            except ValueError:
                LOG.exception()
                compose(response, code="400", reason="Bad Request")
                connection.reply(request, response)
                return
            # XXX read() assumes there is enough core
            body.seek(first)
            partial = body.read(last - first + 1)
            response["content-range"] = "bytes %d-%d/%d" % (first, last, total)
            body = StringIO(partial)
            code, reason = "206", "Partial Content"
        else:
            code, reason = "200", "Ok"
        compose(response, code=code, reason=reason, body=body,
                mimetype="application/octet-stream")
        connection.reply(request, response)

    def do_upload(self, connection, request):
        response = Message()
        compose(response, code="200", reason="Ok")
        connection.reply(request, response)

RESTRICTED = [
    "/speedtest/latency",
    "/speedtest/download",
    "/speedtest/upload",
    "/speedtest/collect",
]

class SessionState:
    active = False
    timestamp = 0
    identifier = None
    queuepos = 0
    negotiations = 0

class _SessionTrackerMixin(object):
    identifiers = {}
    queue = deque()
    connections = {}

    def __init__(self):
        POLLER.sched(60, self._sample_queue_length)

    def _sample_queue_length(self):
        LOG.info("speedtest queue length: %d\n" % len(self.queue))
        POLLER.sched(60, self._sample_queue_length)

    def session_active(self, request):
        identifier = request["authorization"]
        if identifier in self.identifiers:
            session = self.identifiers[identifier]
            session.timestamp = timestamp()             # XXX
            return session.active
        return False

    def session_prune(self):
        stale = []
        now = timestamp()
        for session in self.queue:
            if now - session.timestamp > 30:
                stale.append(session)
        if not stale:
            return False
        for session in stale:
            self._do_remove(session)
        return True

    def session_delete(self, request):
        identifier = request["authorization"]
        if identifier in self.identifiers:
            session = self.identifiers[identifier]
            self._do_remove(session)

    def session_negotiate(self, request):
        identifier = request["authorization"]
        if not identifier in self.identifiers:
            session = SessionState()
            # XXX collision is not impossible but very unlikely
            session.identifier = str(uuid4())
            request["authorization"] = session.identifier
            session.timestamp = timestamp()
            self._do_add(session)
        else:
            session = self.identifiers[identifier]
        session.negotiations += 1
        return session

    def _do_add(self, session):
        self.identifiers[session.identifier] = session
        session.queuepos = len(self.queue)
        self.queue.append(session)
        self._do_update_queue()

    def _do_remove(self, session):
        del self.identifiers[session.identifier]
        self.queue.remove(session)
        self._do_update_queue()

    def _do_update_queue(self):
        pos = 1
        for session in self.queue:
            if pos <= 3 and not session.active:
                session.active = True
            session.queuepos = pos
            pos = pos + 1

    # connection tracking

    def register_connection(self, connection, request):
        if not connection in self.connections:
            identifier = request["authorization"]
            if identifier in self.identifiers:
                self.connections[connection] = identifier

    def unregister_connection(self, connection):
        if connection in self.connections:
            identifier = self.connections[connection]
            del self.connections[connection]
            if identifier in self.identifiers:
                session = self.identifiers[identifier]
                self._do_remove(session)

class _NegotiateServerMixin(_SessionTrackerMixin):
    def __init__(self, config):
        self.config = config
        self.begin_test = 0
        POLLER.sched(3, self._speedtest_check_timeout)
        _SessionTrackerMixin.__init__(self)

    def check_request_headers(self, connection, request):
        ret = True
        self.register_connection(connection, request)
        if self.config.only_auth and request.uri in RESTRICTED:
            if not self.session_active(request):
                LOG.warning("* Connection %s: Forbidden" % (
                 connection.handler.stream.logname))
                ret = False
        return ret

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
        connection, request = atuple
        if connection.handler:
            self.do_negotiate(connection, request, True)

    def _speedtest_check_timeout(self):
        POLLER.sched(3, self._speedtest_check_timeout)
        if self.session_prune():
            publish(RENEGOTIATE)

    def _speedtest_complete(self, request):
        self.session_delete(request)
        publish(RENEGOTIATE)

    def do_negotiate(self, connection, request, nodelay=False):
        session = self.session_negotiate(request)
        if session.negotiations == 1:
            # XXX make sure we track ALSO the first connection of the
            # session (which is assigned an identifier in session_negotiate)
            # or, should this connection fail, we would not be able to
            # propagate quickly this information because unregister_connection
            # would not find an entry in self.connections{}.
            self.register_connection(connection, request)
            nodelay = True
        if not session.active:
            if not nodelay:
                subscribe(RENEGOTIATE, self._do_renegotiate,
                          (connection, request))
                return
        self._send_negotiate(connection, request, session.identifier,
         session.active, session.queuepos)

    def _send_negotiate(self, connection, request, token, unchoked, queuePos):
        root = Element("SpeedtestNegotiate_Response")
        elem = SubElement(root, "authorization")
        elem.text = token
        elem = SubElement(root, "queueLen")
        elem.text = str(len(self.queue))
        elem = SubElement(root, "queuePos")
        elem.text = str(queuePos)
        elem = SubElement(root, "unchoked")
        elem.text = str(unchoked)
        elem = SubElement(root, "publicAddress")
        elem.text = str(connection.handler.stream.peername[0])          # XXX
        tree = ElementTree(root)
        stringio = StringIO()
        tree.write(stringio, encoding="utf-8")
        stringio.seek(0)
        # HTTP
        response = Message()
        compose(response, code="200", reason="Ok",
         body=stringio, mimetype="application/xml")
        connection.reply(request, response)

    def do_collect(self, connection, request):
        response = Message()
        collect = SpeedtestCollect()
        try:
            collect.parse(request.body)
        except ValueError:
            compose(response, code="500", reason="Internal Server Error")
            connection.reply(request, response)
            return
        if database.dbm:
            request.body.seek(0)
            database.dbm.save_result("speedtest", request.body.read(),
                                     collect.client)
        compose(response, code="200", reason="Ok")
        connection.reply(request, response)
        self._speedtest_complete(request)

    def remove_connection(self, connection):
        self.unregister_connection(connection)
        publish(RENEGOTIATE)

class SpeedtestServer(Server, _TestServerMixin, _NegotiateServerMixin):
    def __init__(self, config):
        Server.__init__(self, address=config.address, port=config.port)
        _TestServerMixin.__init__(self, config)
        _NegotiateServerMixin.__init__(self, config)
        self.table = {}
        self._init_table()

    def _init_table(self):
        self.table["/speedtest/negotiate"] = self.do_negotiate
        self.table["/speedtest/latency"] = self.do_latency
        self.table["/speedtest/download"] = self.do_download
        self.table["/speedtest/upload"] = self.do_upload
        self.table["/speedtest/collect"] = self.do_collect

    def bind_failed(self):
        exit(1)

    def got_request_headers(self, connection, request):
        # XXX cheat with http.Connection: we don't want client disconnection
        self.nleft = 128
        return self.check_request_headers(connection, request)

    def got_request(self, connection, request):
        try:
            self.process_request(connection, request)
        except KeyboardInterrupt:
            raise
        except:
            LOG.exception()
            response = Message()
            compose(response, code="500", reason="Internal Server Error")
            connection.reply(request, response)

    def process_request(self, connection, request):
        try:
            self.table[request.uri](connection, request)
        except KeyError:
            response = Message()
            compose(response, code="404", reason="Not Found")
            connection.reply(request, response)

    def connection_lost(self, connection):
        self.remove_connection(connection)

#
# [speedtest]
# address: 0.0.0.0
# only_auth: False
# path: /nonexistent
# port: 80
#

class SpeedtestConfig(SafeConfigParser):
    def __init__(self):
        SafeConfigParser.__init__(self)
        self.address = "0.0.0.0"
        self.only_auth = False
        self.path = ""
        self.port = "80"

#   def check(self):
#       pass

    def readfp(self, fp, filename=None):
        SafeConfigParser.readfp(self, fp, filename)
        self._do_parse()

    def _do_parse(self):
        if self.has_option("speedtest", "address"):
            self.address = self.get("speedtest", "address")
        if self.has_option("speedtest", "only_auth"):
            self.only_auth = self.getboolean("speedtest", "only_auth")
        if self.has_option("speedtest", "path"):
            self.path = self.get("speedtest", "path")
        if self.has_option("speedtest", "port"):
            self.port = self.get("speedtest", "port")

    def read(self, filenames):
        SafeConfigParser.read(self, filenames)
        self._do_parse()

class SpeedtestModule:
    def __init__(self):
        self.config = SpeedtestConfig()
        self.server = None

    def configure(self, filenames, fakerc):
        self.config.read(filenames)
        self.config.readfp(fakerc)
        # XXX other modules need to read() it too
        fakerc.seek(0)

    def start(self):
        self.server = SpeedtestServer(self.config)
        self.server.listen()

speedtest = SpeedtestModule()

#
# The purpose of this class is that of emulating the behavior of the
# test you can perform at speedtest.net.  As you can see, there is
# much work to do before we achieve our goal, and, in particular, we
# need to: (i) report the aggregate speed of the N connections; and
# (ii) improve our upload strategy.
#

class SpeedtestHelper:
    def __init__(self, parent):
        self.speedtest = parent

    def __del__(self):
        pass

    def start(self):
        pass

    def got_response(self, client, response):
        pass

    def cleanup(self):
        self.speedtest = None

#
# Here we measure the time required to retrieve just the headers of a
# resource, and this is an in some way related to the round-trip-time
# between the client and the server.
#

REPEAT = 10

class Latency(SpeedtestHelper):
    def __init__(self, parent):
        SpeedtestHelper.__init__(self, parent)
        self.connect = []
        self.complete = []
        self.latency = []
        self.repeat = 1

    def __del__(self):
        SpeedtestHelper.__del__(self)

    def start(self):
        LOG.start("* Latency run #%d" % self.repeat)
        for client in self.speedtest.clients:
            self._start_one(client)

    def _start_one(self, client):
        m = Message()
        compose(m, method="HEAD", uri=self.speedtest.uri + "latency")
        if self.speedtest.negotiate.authorization:
            m["authorization"] = self.speedtest.negotiate.authorization
        client.sendrecv(m)

    def got_response(self, client, response):
        if response.code != "200":
            self.speedtest.bad_response(response)
            return
        if client.connecting.diff() > 0:
            self.connect.append(client.connecting.diff())
            client.connecting.start = client.connecting.stop = 0
        latency = client.receiving.stop - client.sending.start
        self.latency.append(latency)
        self.complete.append(client)
        if len(self.complete) == len(self.speedtest.clients):
            self._pass_complete()

    def _pass_complete(self):
        LOG.complete()
        self.repeat = self.repeat + 1
        if self.repeat <= REPEAT:
            del self.complete[:]
            self.start()
            return
        if len(self.latency) > 0:
            latency = sum(self.latency) / len(self.latency)
            del self.latency[:]
            self.latency.append(latency)
            latency = time_formatter(latency)
            STATE.update("speedtest_latency", {"value": latency})
        if len(self.connect) > 0:
            connect = sum(self.connect) / len(self.connect)
            del self.connect[:]
            self.connect.append(connect)
        self.speedtest.complete()

# Measurer object

from neubot.utils import speed_formatter
from neubot.net.streams import Measurer


class SpeedtestMeasurer(Measurer):
    def __init__(self):
        Measurer.__init__(self)
        POLLER.sched(1, self.poll)
        self.created = ticks()
        self.recv = []
        self.send = []

    def poll(self):
        recvavg, sendavg = self.measure()[2:4]
        self.recv.append(recvavg)
        self.send.append(sendavg)
        POLLER.sched(1, self.poll)

    def clear(self):
        del self.recv[:]
        del self.send[:]


MEASURER = SpeedtestMeasurer()


# Here we measure download speed.

MIN_DOWNLOAD = 1<<16
MAX_DOWNLOAD = 1<<26


class Download(SpeedtestHelper):
    def __init__(self, parent):
        SpeedtestHelper.__init__(self, parent)
        self.calibrating = 3
        self.length = MIN_DOWNLOAD
        self.begin = 0
        self.end = 0
        self.complete = []
        self.total = 0
        self.speed = []

    def __del__(self):
        SpeedtestHelper.__del__(self)

    def start(self):

        if self.calibrating:
            LOG.start("* Download: calibrate with %d bytes" % self.length)
            self.begin = ticks()
            client = self.speedtest.clients[0]
            self._start_one(client)
            return

        LOG.start("* Download: measure with %d bytes and %d connections" %
                  (self.length, len(self.speedtest.clients)))
        MEASURER.clear()
        self.begin = ticks()
        for client in self.speedtest.clients:
            MEASURER.register_stream(client.handler.stream)
            self._start_one(client)

    def _start_one(self, client):
        m = Message()
        compose(m, method="GET", uri=self.speedtest.uri + "download")
        m["range"] = "bytes=0-%d" % self.length
        if self.speedtest.negotiate.authorization:
            m["authorization"] = self.speedtest.negotiate.authorization
        client.sendrecv(m)

    def got_response(self, client, response):

        if response.code not in ["200", "206"]:
            self.speedtest.bad_response(response)
            return

        end = ticks()
        elapsed = end - self.begin

        if self.calibrating:
            LOG.complete()
            self.calibrating -= 1

            self.length = int(self.length / elapsed)
            if self.length >= MAX_DOWNLOAD:
                self.length = MAX_DOWNLOAD
                self.calibrating = 0

            if elapsed >= 1:
                self.calibrating = 0

            if self.calibrating == 0:
                self.length = int(7 * self.length / 4)
                if self.length >= MAX_DOWNLOAD:
                    self.length = MAX_DOWNLOAD

            self.start()
            return

        self.total += self.length

        self.complete.append(client)
        if len(self.complete) < len(self.speedtest.clients):
            return

        LOG.complete()
        self.speedtest.upload.body = response.body.read()
        self.end = end
        self._pass_complete()

    def _pass_complete(self):
        LOG.info("* Download speeds: %s" % map(speed_formatter,
                                               MEASURER.recv))
        speed = self.total / (self.end - self.begin)
        self.speed.append(speed)
        speed = unit_formatter(speed * 8, base10=True, unit="bit/s")
        STATE.update("speedtest_download", {"value": speed})
        self.speedtest.complete()


# Here we measure upload speed.

MIN_UPLOAD = 1<<15


class Upload(SpeedtestHelper):
    def __init__(self, parent):
        SpeedtestHelper.__init__(self, parent)
        self.calibrating = 3
        self.length = MIN_UPLOAD
        self.body = "\0" * 1048576
        self.complete = []
        self.begin = 0
        self.end = 0
        self.total = 0
        self.speed = []
        self.clients = []

    def __del__(self):
        SpeedtestHelper.__del__(self)

    def start(self):

        if self.calibrating:
            LOG.start("* Upload: calibrate with %d bytes" % self.length)
            self.begin = ticks()
            client = self.speedtest.clients[0]
            self._start_one(client)
            return

        self.clients = self.speedtest.clients
        if self.length < (1<<19):
            self.clients = self.speedtest.clients[0:2]
        LOG.start("* Upload: measure with %d bytes and %d connections" %
                  (self.length, len(self.clients)))
        MEASURER.clear()
        self.begin = ticks()
        for client in self.clients:
            MEASURER.register_stream(client.handler.stream)
            self._start_one(client)

    def _start_one(self, client):
        m = Message()
        body = StringIO(self.body[:self.length])
        compose(m, method="POST", uri=self.speedtest.uri + "upload",
                body=body, mimetype="application/octet-stream")
        if self.speedtest.negotiate.authorization:
            m["authorization"] = self.speedtest.negotiate.authorization
        client.sendrecv(m)

    def got_response(self, client, response):

        if response.code != "200":
            self.speedtest.bad_response(response)
            return

        end = ticks()
        elapsed = end - self.begin

        if self.calibrating:
            LOG.complete()
            self.calibrating -= 1

            self.length = int(self.length / elapsed)
            if self.length >= len(self.body):
                self.length = len(self.body)
                self.calibrating = 0

            if elapsed >= 1:
                self.calibrating = 0

            if self.calibrating == 0:
                conns = 4
                if self.length < (1<<19):
                    conns = 2
                self.length = int(7 * self.length / conns)
                if self.length >= len(self.body):
                    self.length = len(self.body)

            self.start()
            return

        self.total += self.length

        self.complete.append(client)
        if len(self.complete) < len(self.clients):
            return

        LOG.complete()
        self.end = end
        self._pass_complete()

    def _pass_complete(self):
        LOG.info("* Upload speeds: %s" % map(speed_formatter,
                                             MEASURER.send))
        speed = self.total / (self.end - self.begin)
        self.speed.append(speed)
        speed = unit_formatter(speed * 8, base10=True, unit="bit/s")
        STATE.update("speedtest_upload", {"value": speed})
        self.speedtest.complete()


#
# <SpeedtestNegotiate_Response>
#     <authorization>ac2fcbf3-a1db-4bdb-836d-533c2aee9677</authorization>
#     <publicAddress>130.192.47.84</publicAddress>
#     <unchoked>True</unchoked>
#     <queuePos>7</queuePos>
#     <queueLen>21</queueLen>
# </SpeedtestNegotiate_Response>
#
# Note that the response should contain either an authorization token
# or the current position in the queue.  Also note that parse() should
# raise ValueError if the message is not well-formed, for example b/c
# the authorization is not an UUID.
#

class SpeedtestNegotiate_Response:
    def __init__(self):
        self.authorization = ""
        self.publicAddress = ""
        self.unchoked = False
        self.queuePos = 0
        self.queueLen = 0

    def __del__(self):
        pass

    def parse(self, stringio):
        tree = ElementTree()
        try:
            tree.parse(stringio)
        except:
            raise ValueError("Can't parse XML body")
        else:
            authorization = XML_get_scalar(tree, "authorization")
            if authorization:
                self.authorization = UUID(authorization)
            publicAddress = XML_get_scalar(tree, "publicAddress")
            if publicAddress:
                self.publicAddress = publicAddress
            unchoked = XML_get_scalar(tree, "unchoked")
            if unchoked.lower() == "true":
                self.unchoked = True
            queuePos = XML_get_scalar(tree, "queuePos")
            if queuePos:
                self.queuePos = int(queuePos)
            queueLen = XML_get_scalar(tree, "queueLen")
            if queueLen:
                self.queueLen = int(queueLen)

class Negotiate(SpeedtestHelper):
    def __init__(self, parent):
        SpeedtestHelper.__init__(self, parent)
        self.publicAddress = ""
        self.authorization = ""

    def __del__(self):
        SpeedtestHelper.__del__(self)

    def start(self):
        client = self.speedtest.clients[0]
        LOG.start("* Negotiate permission to take the test")
        m = Message()
        compose(m, method="GET", uri=self.speedtest.uri + "negotiate")
        if self.authorization:
            m["authorization"] = self.authorization
        client.sendrecv(m)

    def got_response(self, client, response):
        if response.code != "200":
            self.speedtest.bad_response(response)
            return
        LOG.complete()
        negotiation = SpeedtestNegotiate_Response()
        try:
            negotiation.parse(response.body)
        except ValueError:
            LOG.error("* Bad response message")
            LOG.exception()
            self.speedtest.bad_response(response)
            return
        self.authorization = str(negotiation.authorization)
        self.publicAddress = negotiation.publicAddress
        if not negotiation.unchoked:
            if negotiation.queuePos and negotiation.queueLen:
                LOG.info("* Waiting in queue: %d/%d" % (negotiation.queuePos,
                                                        negotiation.queueLen))
                STATE.update("negotiate",{"queue_pos": negotiation.queuePos,
                                          "queue_len": negotiation.queueLen})
            self.start()
            return
        LOG.info("* Authorized to take the test!")
        self.speedtest.complete()

class Collect(SpeedtestHelper):
    def __init__(self, parent):
        SpeedtestHelper.__init__(self, parent)

    def __del__(self):
        SpeedtestHelper.__del__(self)

    def start(self):
        client = self.speedtest.clients[0]
        LOG.start("* Collecting results")
        # XML
        root = Element("SpeedtestCollect")
        if database.dbm:
            element = SubElement(root, "client")
            element.text = database.dbm.ident
        timestamp = SubElement(root, "timestamp")
        timestamp.text = str(time())
        internalAddress = SubElement(root, "internalAddress")
        internalAddress.text = client.handler.stream.myname[0]          # XXX
        realAddress = SubElement(root, "realAddress")
        realAddress.text = self.speedtest.negotiate.publicAddress
        remoteAddress = SubElement(root, "remoteAddress")
        remoteAddress.text = client.handler.stream.peername[0]          # XXX
        for t in self.speedtest.latency.connect:
            connectTime = SubElement(root, "connectTime")
            connectTime.text = str(t)
        for t in self.speedtest.latency.latency:
            latency = SubElement(root, "latency")
            latency.text = str(t)
        for s in self.speedtest.download.speed:
            downloadSpeed = SubElement(root, "downloadSpeed")
            downloadSpeed.text = str(s)
        for s in self.speedtest.upload.speed:
            uploadSpeed = SubElement(root, "uploadSpeed")
            uploadSpeed.text = str(s)
        tree = ElementTree(root)
        stringio = StringIO()
        tree.write(stringio, encoding="utf-8")
        stringio.seek(0)
        # DB
        if database.dbm:
            database.dbm.save_result("speedtest", stringio.read(),
                                     database.dbm.ident)
            stringio.seek(0)
        # HTTP
        m = Message()
        compose(m, method="POST", uri=self.speedtest.uri + "collect",
                body=stringio, mimetype="application/xml")
        if self.speedtest.negotiate.authorization:
            m["authorization"] = self.speedtest.negotiate.authorization
        client.sendrecv(m)

    def got_response(self, client, response):
        if response.code != "200":
            self.speedtest.bad_response(response)
            return
        LOG.complete()
        self.speedtest.complete()

#
# We assume that the webserver contains two empty resources,
# named "/latency" and "/upload" and one BIG resource named
# "/download".  The user has the freedom to choose the base
# URI, and so different servers might put these three files
# at diffent places.
#

FLAG_LATENCY = (1<<0)
FLAG_DOWNLOAD = (1<<1)
FLAG_UPLOAD = (1<<2)
FLAG_ALL = FLAG_LATENCY|FLAG_DOWNLOAD|FLAG_UPLOAD

#
# These two flags are set automatically unless we are running
# in debug mode (option -x).  The purpose of the debug mode is
# that of testing the speedtest without having to pass through
# the negotiation and the collect phases.  Of course by default
# we DON'T run in debug mode.
#
FLAG_NEGOTIATE = (1<<3)
FLAG_COLLECT = (1<<4)

#
# Other internal flags
#
FLAG_CLEANUP = (1<<5)
FLAG_SUCCESS = (1<<6)

class SpeedtestClient1(ClientController):
    def __init__(self, uri, nclients, flags, debug=False, parent=None):
        STATE.update("test_name", "speedtest")
        self.negotiate = Negotiate(self)
        self.latency = Latency(self)
        self.download = Download(self)
        self.upload = Upload(self)
        self.collect = Collect(self)
        self.clients = []
        self.uri = uri
        self.flags = flags
        if not debug:
            self.flags |= FLAG_NEGOTIATE|FLAG_COLLECT
        self.parent = parent
        self._start_speedtest(nclients)

    def __del__(self):
        pass

    def _doCleanup(self):
        if self.flags & FLAG_CLEANUP:
            return
        self.flags |= FLAG_CLEANUP
        for client in self.clients:
            if client.handler:
                client.handler.close()
        self.clients = []
        self.negotiate.cleanup()
        self.negotiate = None
        self.latency.cleanup()
        self.latency = None
        self.download.cleanup()
        self.download = None
        self.upload.cleanup()
        self.upload = None
        self.collect.cleanup()
        self.collect = None
        if self.parent:
            self.parent.speedtest_complete()
            self.parent = None

    #
    # We make sure that the URI ends with "/" because below
    # we need to append "latency", "download" and "upload" to
    # it and we don't want the result to contain consecutive
    # slashes.
    #

    def _start_speedtest(self, nclients):
        if self.uri[-1] != "/":
            self.uri = self.uri + "/"
        while nclients > 0:
            self.clients.append(Client(self))
            nclients = nclients - 1
        self._update_speedtest()

    def _update_speedtest(self):
        if self.flags & FLAG_NEGOTIATE:
            STATE.update("negotiate")
            self.negotiate.start()
        elif self.flags & FLAG_LATENCY:
            STATE.update("test", "speedtest_latency")
        elif self.flags & FLAG_DOWNLOAD:
            STATE.update("test", "speedtest_download")
            self.download.start()
        elif self.flags & FLAG_UPLOAD:
            STATE.update("test", "speedtest_upload")
            self.upload.start()
        elif self.flags & FLAG_COLLECT:
            STATE.update("collect")
            self.collect.start()
        else:
            self.flags |= FLAG_SUCCESS
            self._speedtest_complete()

    def _speedtest_complete(self):
        self.speedtest_complete()
        self._doCleanup()

    # override in sub-classes
    def speedtest_complete(self):
        pass

    def complete(self):
        if self.flags & FLAG_NEGOTIATE:
            self.flags &= ~FLAG_NEGOTIATE
        elif self.flags & FLAG_LATENCY:
            self.flags &= ~FLAG_LATENCY
        elif self.flags & FLAG_DOWNLOAD:
            self.flags &= ~FLAG_DOWNLOAD
        elif self.flags & FLAG_UPLOAD:
            self.flags &= ~FLAG_UPLOAD
        elif self.flags & FLAG_COLLECT:
            self.flags &= ~FLAG_COLLECT
        else:
            raise RuntimeError("Bad flags")
        self._update_speedtest()

    def bad_response(self, response):
        LOG.error("* Bad response: aborting speedtest")
        self._doCleanup()

    #
    # Here we manage callbacks from clients.
    # The management of connection_failed() and connection_lost()
    # is quite raw and could be refined a bit--expecially if we
    # consider the fact that after a certain amount of HTTP requests
    # the server might close the connection.
    #

    def connection_failed(self, client):
        LOG.error("* Connection failed: aborting speedtest")
        self._doCleanup()

    def connection_lost(self, client):
        if self.flags & FLAG_SUCCESS:
            return
        LOG.error("* Connection lost: aborting speedtest")
        self._doCleanup()

    def got_response(self, client, request, response):
        if self.flags & FLAG_NEGOTIATE:
            self.negotiate.got_response(client, response)
        elif self.flags & FLAG_LATENCY:
            self.latency.got_response(client, response)
        elif self.flags & FLAG_DOWNLOAD:
            self.download.got_response(client, response)
        elif self.flags & FLAG_UPLOAD:
            self.upload.got_response(client, response)
        elif self.flags & FLAG_COLLECT:
            self.collect.got_response(client, response)
        else:
            raise RuntimeError("Bad flags")

class SpeedtestController:
    def start_speedtest_simple(self, uri):
        SpeedtestClient(uri, 4, FLAG_ALL, False, self)

    def speedtest_complete(self):
        pass

#
# Test unit
#

USAGE =									\
"Usage: @PROGNAME@ --help\n"						\
"       @PROGNAME@ -V\n"						\
"       @PROGNAME@ [-svx] [-a test] [-n count] [-O fmt] [base-URI]\n"	\
"       @PROGNAME@ -S [-dv] [-D name=value]\n"

HELP = USAGE +								\
"Tests: all*, download, latency, upload.\n"				\
"Fmts: bits*, bytes, raw.\n"						\
"Options:\n"								\
"  -a test       : Add test to the list of tests.\n"			\
"  -D name=value : Set configuration file property.\n"			\
"  -d            : Debug mode, don't become a daemon.\n"                \
"  --help        : Print this help screen and exit.\n"			\
"  -n count      : Use count HTTP connections.\n"			\
"  -O fmt        : Format output numbers using fmt.\n"			\
"  -S            : Run the program in server mode.\n"			\
"  -s            : Do not print speedtest statistics.\n"		\
"  -V            : Print version number and exit.\n"			\
"  -v            : Run the program in verbose mode.\n"			\
"  -x            : Avoid negotiation and collection.\n"

# TODO move this class near SpeedtestClient1
class SpeedtestClient(SpeedtestClient1):
    def __init__(self, uri, nclients, flags, debug=False, parent=None):
        SpeedtestClient1.__init__(self, uri, nclients, flags, debug, parent)
        self.formatter = speed_formatter

    def __del__(self):
        pass

    def speedtest_complete(self):
        LOG.info("*** Begin test result ***")
        LOG.info("Timestamp: %d\n" % timestamp())
        LOG.info("Base-URI: %s\n" % self.uri)
        # connect
        v = []
        if len(self.latency.connect) > 0:
            v.append("Connect:")
            for x in self.latency.connect:
                v.append(" %f s" % x)
            LOG.info("".join(v))
        # latency
        v = []
        if len(self.latency.latency) > 0:
            v.append("Latency:")
            for x in self.latency.latency:
                v.append(" %f s" % x)
            LOG.info("".join(v))
        # download
        v = []
        if len(self.download.speed) > 0:
            v.append("Download:")
            for x in self.download.speed:
                v.append(" %s" % self.formatter(x))
            LOG.info("".join(v))
        # upload
        v = []
        if len(self.upload.speed) > 0:
            v.append("Upload:")
            for x in self.upload.speed:
                v.append(" %s" % self.formatter(x))
            LOG.info("".join(v))
        LOG.info("*** End test result ***")

FLAGS = {
    "all": FLAG_ALL,
    "download": FLAG_DOWNLOAD,
    "latency": FLAG_LATENCY,
    "upload": FLAG_UPLOAD,
}

FORMATTERS = {
    "raw": lambda n: " %f iByte/s" % n,
    "bits": lambda n: unit_formatter(n*8, base10=True, unit="bit/s"),
    "bytes": lambda n: unit_formatter(n, unit="B/s"),
}

URI = "http://neubot.blupixel.net/speedtest"

def main(args):
    fakerc = StringIO()
    fakerc.write("[speedtest]\r\n")
    daemonize = True
    servermode = False
    xdebug = False
    flags = 0
    fmt = "bits"
    nclients = 4
    # parse
    try:
        options, arguments = getopt(args[1:], "a:D:dn:O:SsVvx", ["help"])
    except GetoptError:
        stderr.write(USAGE.replace("@PROGNAME@", args[0]))
        exit(1)
    # options
    for name, value in options:
        if name == "-a":
            if not FLAGS.has_key(value):
                LOG.error("Invalid argument to -a: %s" % value)
                exit(1)
            flags |= FLAGS[value]
        elif name == "-D":
            fakerc.write(value + "\n")
        elif name == "-d":
            daemonize = False
        elif name == "--help":
            stdout.write(HELP.replace("@PROGNAME@", args[0]))
            exit(0)
        elif name == "-n":
            try:
                nclients = int(value)
            except ValueError:
                nclients = -1
            if nclients <= 0:
                LOG.error("Invalid argument to -n: %s" % value)
                exit(1)
        elif name == "-O":
            if not value in FORMATTERS.keys():
                LOG.error("Invalid argument to -O: %s" % value)
                exit(1)
            fmt = value
        elif name == "-S":
            servermode = True
        elif name == "-s":
            # XXX for backward compatibility only
            pass
        elif name == "-V":
            stdout.write(version + "\n")
            exit(0)
        elif name == "-v":
            LOG.verbose()
        elif name == "-x":
            xdebug = True
    # config
    fakerc.seek(0)
    database.configure(pathnames.CONFIG, fakerc)
    speedtest.configure(pathnames.CONFIG, fakerc)
    # server
    if servermode:
        if len(arguments) > 0:
            stderr.write(USAGE.replace("@PROGNAME@", args[0]))
            exit(1)
        database.start()
        speedtest.start()
        if daemonize:
            become_daemon()
        POLLER.loop()
        exit(0)
    # client
    if len(arguments) > 1:
        stderr.write(USAGE.replace("@PROGNAME@", args[0]))
        exit(1)
    elif len(arguments) == 1:
        uri = arguments[0]
    else:
        uri = URI
    if flags == 0:
        flags = FLAG_ALL
    # run
    client = SpeedtestClient(uri, nclients, flags, xdebug)
    client.formatter = FORMATTERS[fmt]
    POLLER.loop()

if __name__ == "__main__":
    main(argv)
