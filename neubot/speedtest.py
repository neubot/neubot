# neubot/speedtest.py
# Copyright (c) 2010 NEXA Center for Internet & Society

# This file is part of Neubot.
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

if __name__ == "__main__":
    from sys import path
    path.insert(0, ".")

from StringIO import StringIO
from neubot.net.pollers import disable_stats
from neubot.net.pollers import enable_stats
from neubot.database import database
from neubot.http.messages import Message
from neubot.utils import unit_formatter
from neubot.http.messages import compose
from neubot.http.clients import Client
from neubot.http.clients import ClientController
from neubot.net.pollers import loop
from neubot.utils import timestamp
from sys import stdout
from sys import argv
from neubot import log
from neubot import version
from getopt import GetoptError
from neubot.state import state
from getopt import getopt
from sys import stderr
from sys import exit

from neubot import pathnames
from collections import deque
from neubot.utils import ticks
from neubot.net.pollers import sched
from neubot.notify import publish
from neubot.notify import subscribe
from neubot.notify import RENEGOTIATE
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
            self.timestamp = XML_get_scalar(tree, "timestamp")
            self.internalAddress = XML_get_scalar(tree, "internalAddress")
            self.realAddress = XML_get_scalar(tree, "realAddress")
            self.remoteAddress = XML_get_scalar(tree, "remoteAddress")
            self.connectTime = XML_get_vector(tree, "connectTime")
            self.latency = XML_get_vector(tree, "latency")
            self.downloadSpeed = XML_get_vector(tree, "downloadSpeed")
            self.uploadSpeed = XML_get_vector(tree, "uploadSpeed")

RESTRICTED = [
    "/speedtest/latency",
    "/speedtest/download",
    "/speedtest/upload",
    "/speedtest/collect",
]

class SpeedtestServer(Server):
    def __init__(self, config):
        self.config = config
        Server.__init__(self, address=config.address, port=config.port)
        self.queue = deque()
        self.table = {}
        self._init_table()

    def _init_table(self):
        self.table["/speedtest/negotiate"] = self._do_negotiate
        self.table["/speedtest/latency"] = self._do_latency
        self.table["/speedtest/download"] = self._do_download
        self.table["/speedtest/upload"] = self._do_upload
        self.table["/speedtest/collect"] = self._do_collect

    def bind_failed(self):
        exit(1)

    def got_request_headers(self, connection, request):
        ret = True
        if self.config.only_auth and request.uri in RESTRICTED:
            token = request["authorization"]
            if len(self.queue) == 0 or self.queue[0] != token:
                log.warning("* Connection %s: Forbidden" % (
                 connection.handler.stream.logname))
                ret = False
        return ret

    def got_request(self, connection, request):
        try:
            self.process_request(connection, request)
        except KeyboardInterrupt:
            raise
        except:
            log.exception()
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

    #
    # A client is allowed to access restricted URIs if: (i) either
    # only_auth is False, (ii) or the authorization token is valid.
    # Here we decide how to give clients authorization tokens.
    # We start with a very simple (to implement) rule.  We give the
    # client a token and we remove the token after 30+ seconds, or
    # when the authorized client uploads the results.
    # Wish list:
    # - Revoke auth on connection lost. (?)
    # - Avoid client synchronization
    #

    def _do_renegotiate(self, event, atuple):
        connection, request = atuple
        self._do_negotiate(connection, request, True)

    def _publish_renegotiate(self, timeout=True):
        if self.queue:
            token = self.queue.popleft()
            if timeout:
                log.info("* Test %s: timed-out" % token)
            publish(RENEGOTIATE)

    def _do_negotiate(self, connection, request, recurse=False):
        queuePos = 0
        unchoked = True
        token = request["authorization"]
        if not token:
            token = str(uuid4())
            request["authorization"] = token
            self.queue.append(token)
        if len(self.queue) > 0 and self.queue[0] != token:
            if not recurse:
                subscribe(RENEGOTIATE, self._do_renegotiate,
                          (connection, request))
                return
            queuePos = self._queuePos(token)
            unchoked = False
        if unchoked:
            sched(30, self._publish_renegotiate)
        self._send_negotiate(connection, request, token, unchoked, queuePos)

    # XXX horrible horrible O(length)!
    def _queuePos(self, token):
        queuePos = 0
        for element in self.queue:
            if element == token:
                break
            if queuePos >= 64:
                break
            queuePos = queuePos + 1
        return queuePos

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

    def _do_latency(self, connection, request):
        response = Message()
        compose(response, code="200", reason="Ok")
        connection.reply(request, response)

    def _do_download(self, connection, request):
        response = Message()
        # open
        try:
            body = open(self.config.path, "rb")
        except (IOError, OSError):
            log.exception()
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
                log.exception()
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

    def _do_upload(self, connection, request):
        response = Message()
        compose(response, code="200", reason="Ok")
        connection.reply(request, response)

    def _do_collect(self, connection, request):
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
            database.dbm.save_result("speedtest", request.body.read())
        compose(response, code="200", reason="Ok")
        connection.reply(request, response)
        self._publish_renegotiate(False)

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
        log.start("* Latency run #%d" % self.repeat)
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
        state.append_result("latency", latency, "s")
        self.complete.append(client)
        if len(self.complete) == len(self.speedtest.clients):
            self._pass_complete()

    def _pass_complete(self):
        log.complete()
        self.repeat = self.repeat + 1
        if self.repeat <= REPEAT:
            del self.complete[:]
            self.start()
            return
        if len(self.latency) > 0:
            latency = sum(self.latency) / len(self.latency)
            del self.latency[:]
            self.latency.append(latency)
        if len(self.connect) > 0:
            connect = sum(self.connect) / len(self.connect)
            del self.connect[:]
            self.connect.append(connect)
        self.speedtest.complete()

#
# Here we measure download speed.  Note that it is possible to employ
# more than one connection to reduce the effect of distance (in terms
# of RTT) from the origin server.
# This implementation is still rather prototypal and indeed we need to
# follow-up with the following improvements:
#
# 1. Do not measure the speed as the average of the speed seen by each
#    connection because this might become inaccurate if connections do
#    not start and finish nearly at the same time.
#

MIN_DOWNLOAD = 1<<16
MAX_DOWNLOAD = 1<<26

class Download(SpeedtestHelper):
    def __init__(self, parent):
        SpeedtestHelper.__init__(self, parent)
        self.length = MIN_DOWNLOAD
        self.complete = []
        self.begin = []
        self.end = []
        self.total = 0
        self.speed = []

    def __del__(self):
        SpeedtestHelper.__del__(self)

    def start(self):
        log.start("* Download %d bytes" % self.length)
        for client in self.speedtest.clients:
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
        self.begin.append(client.receiving.start)
        self.end.append(client.receiving.stop)
        self.total += client.receiving.length
        self.complete.append(client)
        if len(self.complete) == len(self.speedtest.clients):
            self.speedtest.upload.body = response.body.read()
            self._pass_complete()

    def _pass_complete(self):
        log.complete()
        # time
        dtime = max(self.end) - min(self.begin)
        if dtime < 1 and self.length < MAX_DOWNLOAD:
            self.length <<= 1
            del self.complete[:]
            del self.begin[:]
            del self.end[:]
            self.total = 0
            self.start()
            return
        # speed
        speed = self.total / dtime
        self.speed.append(speed)
        # done
        state.append_result("download", speed, "iB/s")
        self.speedtest.complete()

#
# Here we measure upload speed.  Note that it is possible to employ
# more than one connection to reduce the effect of distance (in terms
# of RTT) from the origin server.
# This implementation is still rather prototypal and indeed we need to
# follow-up with the following improvements:
#
# 1. Do not measure the speed as the average of the speed seen by each
#    connection because this might become inaccurate if connections do
#    not start and finish nearly at the same time.
#

MIN_UPLOAD = 1<<15
#MAX_UPLOAD = 1<<25

class Upload(SpeedtestHelper):
    def __init__(self, parent):
        SpeedtestHelper.__init__(self, parent)
        self.length = MIN_UPLOAD
        self.body = "\0" * 1048576
        self.complete = []
        self.begin = []
        self.end = []
        self.total = 0
        self.speed = []

    def __del__(self):
        SpeedtestHelper.__del__(self)

    def start(self):
        log.start("* Upload %d bytes" % self.length)
        for client in self.speedtest.clients:
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
        self.begin.append(client.sending.start)
        self.end.append(client.sending.stop)
        self.total += client.sending.length
        self.complete.append(client)
        if len(self.complete) == len(self.speedtest.clients):
            self._pass_complete()

    def _pass_complete(self):
        log.complete()
        # time
        utime = max(self.end) - min(self.begin)
        if utime < 1 and self.length < len(self.body):
            self.length <<= 1
            del self.complete[:]
            del self.begin[:]
            del self.end[:]
            self.total = 0
            self.start()
            return
        # speed
        speed = self.total / utime
        self.speed.append(speed)
        # done
        state.append_result("upload", speed, "iB/s")
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
        log.start("* Negotiate permission to take the test")
        m = Message()
        compose(m, method="GET", uri=self.speedtest.uri + "negotiate")
        if self.authorization:
            m["authorization"] = self.authorization
        client.sendrecv(m)

    def got_response(self, client, response):
        if response.code != "200":
            self.speedtest.bad_response(response)
            return
        log.complete()
        negotiation = SpeedtestNegotiate_Response()
        try:
            negotiation.parse(response.body)
        except ValueError:
            log.error("* Bad response message")
            log.exception()
            self.speedtest.bad_response(response)
            return
        self.authorization = str(negotiation.authorization)
        self.publicAddress = negotiation.publicAddress
        if not negotiation.unchoked:
            if negotiation.queuePos and negotiation.queueLen:
                log.info("* Waiting in queue: %d/%d" % (negotiation.queuePos,
                                                        negotiation.queueLen))
                state.set_queueInfo(negotiation.queuePos, negotiation.queueLen)
                state.commit()
            self.start()
            return
        log.info("* Authorized to take the test!")
        self.speedtest.complete()

class Collect(SpeedtestHelper):
    def __init__(self, parent):
        SpeedtestHelper.__init__(self, parent)

    def __del__(self):
        SpeedtestHelper.__del__(self)

    def start(self):
        client = self.speedtest.clients[0]
        log.start("* Collecting results")
        # XML
        root = Element("SpeedtestCollect")
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
            database.dbm.save_result("speedtest", stringio.read())
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
        log.complete()
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

class SpeedtestClient(ClientController):
    def __init__(self, uri, nclients, flags, debug=False, parent=None):
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
            state.set_activity("negotiate").commit()
            self.negotiate.start()
        elif self.flags & FLAG_LATENCY:
            state.set_activity("test", ["latency", "download", "upload"],
                               "speedtest")
            state.set_task("latency").commit()
            self.latency.start()
        elif self.flags & FLAG_DOWNLOAD:
            state.set_task("download").commit()
            self.download.start()
        elif self.flags & FLAG_UPLOAD:
            state.set_task("upload").commit()
            self.upload.start()
        elif self.flags & FLAG_COLLECT:
            state.set_activity("collect").commit()
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
        log.error("* Bad response: aborting speedtest")
        self._doCleanup()

    #
    # Here we manage callbacks from clients.
    # The management of connection_failed() and connection_lost()
    # is quite raw and could be refined a bit--expecially if we
    # consider the fact that after a certain amount of HTTP requests
    # the server might close the connection.
    #

    def connection_failed(self, client):
        log.error("* Connection failed: aborting speedtest")
        self._doCleanup()

    def connection_lost(self, client):
        if self.flags & FLAG_SUCCESS:
            return
        log.error("* Connection lost: aborting speedtest")
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
        SpeedtestClient(uri, 2, FLAG_ALL, False, self)

    def speedtest_complete(self):
        pass

#
# Test unit
#

USAGE =									\
"Usage: @PROGNAME@ --help\n"						\
"       @PROGNAME@ -V\n"						\
"       @PROGNAME@ [-svx] [-a test] [-n count] [-O fmt] [base-URI]\n"	\
"       @PROGNAME@ -S [-v] [-D name=value]\n"

HELP = USAGE +								\
"Tests: all*, download, latency, upload.\n"				\
"Fmts: bits*, bytes, raw.\n"						\
"Options:\n"								\
"  -a test       : Add test to the list of tests.\n"			\
"  -D name=value : Set configuration file property.\n"			\
"  --help        : Print this help screen and exit.\n"			\
"  -n count      : Use count HTTP connections.\n"			\
"  -O fmt        : Format output numbers using fmt.\n"			\
"  -S            : Run the program in server mode.\n"			\
"  -s            : Do not print speedtest statistics.\n"		\
"  -V            : Print version number and exit.\n"			\
"  -v            : Run the program in verbose mode.\n"			\
"  -x            : Avoid negotiation and collection.\n"

class VerboseClient(SpeedtestClient):
    def __init__(self, uri, nclients, flags, debug, parent=None):
        SpeedtestClient.__init__(self, uri, nclients, flags, debug, parent)
        self.formatter = None

    def __del__(self):
        pass

    def speedtest_complete(self):
        stdout.write("Timestamp: %d\n" % timestamp())
        stdout.write("Base-URI: %s\n" % self.uri)
        # connect
        if len(self.latency.connect) > 0:
            stdout.write("Connect:")
            for x in self.latency.connect:
                stdout.write(" %f" % x)
            stdout.write("\n")
        # latency
        if len(self.latency.latency) > 0:
            stdout.write("Latency:")
            for x in self.latency.latency:
                stdout.write(" %f" % x)
            stdout.write("\n")
        # download
        if len(self.download.speed) > 0:
            stdout.write("Download:")
            for x in self.download.speed:
                stdout.write(" %s" % self.formatter(x))
            stdout.write("\n")
        # upload
        if len(self.upload.speed) > 0:
            stdout.write("Upload:")
            for x in self.upload.speed:
                stdout.write(" %s" % self.formatter(x))
            stdout.write("\n")

FLAGS = {
    "all": FLAG_ALL,
    "download": FLAG_DOWNLOAD,
    "latency": FLAG_LATENCY,
    "upload": FLAG_UPLOAD,
}

FORMATTERS = {
    "raw": lambda n: " %fiB/s" % n,
    "bits": lambda n: unit_formatter(n*8, base10=True, unit="bps"),
    "bytes": lambda n: unit_formatter(n, unit="B/s"),
}

URI = "http://speedtest1.neubot.org/"

def main(args):
    fakerc = StringIO()
    fakerc.write("[speedtest]\r\n")
    servermode = False
    xdebug = False
    flags = 0
    new_client = VerboseClient
    fmt = "bits"
    nclients = 1
    # parse
    try:
        options, arguments = getopt(args[1:], "a:D:n:O:SsVvx", ["help"])
    except GetoptError:
        stderr.write(USAGE.replace("@PROGNAME@", args[0]))
        exit(1)
    # options
    for name, value in options:
        if name == "-a":
            if not FLAGS.has_key(value):
                log.error("Invalid argument to -a: %s" % value)
                exit(1)
            flags |= FLAGS[value]
        elif name == "-D":
            fakerc.write(value + "\n")
        elif name == "--help":
            stdout.write(HELP.replace("@PROGNAME@", args[0]))
            exit(0)
        elif name == "-n":
            try:
                nclients = int(value)
            except ValueError:
                nclients = -1
            if nclients <= 0:
                log.error("Invalid argument to -n: %s" % value)
                exit(1)
        elif name == "-O":
            if not value in FORMATTERS.keys():
                log.error("Invalid argument to -O: %s" % value)
                exit(1)
            fmt = value
        elif name == "-S":
            servermode = True
        elif name == "-s":
            new_client = SpeedtestClient
        elif name == "-V":
            stdout.write(version + "\n")
            exit(0)
        elif name == "-v":
            log.verbose()
        elif name == "-x":
            xdebug = True
    # config
    fakerc.seek(0)
    speedtest.configure(pathnames.CONFIG, fakerc)
    # server
    if servermode:
        if len(arguments) > 0:
            stderr.write(USAGE.replace("@PROGNAME@", args[0]))
            exit(1)
        speedtest.start()
        loop()
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
    client = new_client(uri, nclients, flags, xdebug)
    if new_client == VerboseClient:
        client.formatter = FORMATTERS[fmt]
    loop()

if __name__ == "__main__":
    main(argv)
