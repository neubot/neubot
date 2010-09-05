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

from sys import path
if __name__ == "__main__":
    path.insert(0, ".")

from StringIO import StringIO
from neubot.net import disable_stats
from neubot.net import enable_stats
from neubot.http.messages import Message
from neubot.utils import unit_formatter
from neubot.http.messages import compose
from neubot.http.clients import Client
from neubot.net.pollers import loop
from neubot.utils import timestamp
from sys import stdout
from sys import argv
from neubot import log
from neubot import version
from getopt import GetoptError
from getopt import getopt
from sys import stderr

#
# The purpose of this class is that of emulating the behavior of the
# test you can perform at speedtest.net.  As you can see, there is
# much work to do before we achieve our goal, and, in particular, we
# need to: (i) report the aggregate speed of the N connections; and
# (ii) improve our upload strategy.
#

FLAG_LATENCY = (1<<0)
FLAG_DOWNLOAD = (1<<1)
FLAG_UPLOAD = (1<<2)
FLAG_ALL = FLAG_LATENCY|FLAG_DOWNLOAD|FLAG_UPLOAD

class SpeedtestClient:

    #
    # We assume that the webserver contains two empty resources,
    # named "/latency" and "/upload" and one BIG resource named
    # "/download".  The user has the freedom to choose the base
    # URI, and so different servers might put these three files
    # at diffent places.
    # We make sure that the URI ends with "/" because below
    # we need to append "latency", "download" and "upload" to
    # it and we don't want the result to contain consecutive
    # slashes.
    #

    def __init__(self, uri, nclients, flags):
        self.length = (1<<16)
        self.repeat = {}
        self.clients = []
        self.complete = 0
        self.connect = []
        self.latency = []
        self.download = []
        self.upload = []
        self.uri = uri
        self.nclients = nclients
        self.flags = flags
        self._start_speedtest()

    def _start_speedtest(self):
        if self.uri[-1] != "/":
            self.uri = self.uri + "/"
        if self.flags & FLAG_LATENCY:
            log.start("* Latency")
            func = self._measure_latency
        elif self.flags & FLAG_DOWNLOAD:
            log.start("* Download %d bytes" % self.length)
            func = self._measure_download
        elif self.flags & FLAG_UPLOAD:
            log.start("* Upload")
            func = self._measure_upload
        else:
            func = self._speedtest_complete
        count = 0
        while count < self.nclients:
            count = count + 1
            func()

    #
    # Measure latency
    # We connect to the server using N different connections and
    # we measure (i) the time required to connect and (ii) the time
    # required to get the response to an HEAD request.
    # We measure the time required to connect() only here and not
    # in download or upload because we assume that the webserver
    # supports (and whish to use) keep-alive, and so we hope to
    # re-use the connection.
    # XXX I am not sure whether we can define that latency or the
    # name is incorrect/misleading.
    #

    def _measure_latency(self, client=None):
        if not client:
            client = Client()
        m = Message()
        compose(m, method="HEAD", uri=self.uri + "latency")
        client.notify_success = self._measured_latency
        client.send(m)
        self.repeat[client] = 5

    def _measured_latency(self, client, request, response):
        if response.code == "200":
            if client.connecting.diff() > 0:
                self.connect.append(client.connecting.diff())
                client.connecting.start = client.connecting.stop = 0
            latency = client.receiving.stop - client.sending.start
            self.latency.append(latency)
            self.repeat[client] = self.repeat[client] -1
            if self.repeat[client] == 0:
                self._latency_complete(client)
            else:
                client.send(request)
        else:
            log.error("Response: %s %s" % (response.code, response.reason))

    def _latency_complete(self, client):
        self.clients.append(client)
        self.complete = self.complete + 1
        if self.complete == self.nclients:
            log.complete()
            self.complete = 0
            clients = self.clients
            self.clients = []
            if self.flags & FLAG_DOWNLOAD:
                log.start("* Download %d bytes" % self.length)
            elif self.flags & FLAG_UPLOAD:
                log.start("* Upload")
            for client in clients:
                if self.flags & FLAG_DOWNLOAD:
                    self._measure_download(client)
                elif self.flags & FLAG_UPLOAD:
                    self._measure_upload(client)
                else:
                    self._speedtest_complete(client)

    #
    # Measure download speed
    # We use N connections and this should mitigate a bit the effect
    # of distance (in terms of RTT) from the origin server.
    #

    def _measure_download(self, client=None):
        if not client:
            client = Client()
        self.repeat[client] = 2
        m = Message()
        compose(m, method="GET", uri=self.uri + "download")
        m["range"] = "bytes=0-%d" % self.length
        client.notify_success = self._measured_download
        client.send(m)

    def _measured_download(self, client, request, response):
        if response.code in ["200", "206"]:
            speed = client.receiving.speed()
            self.download.append(speed)
            self.repeat[client] = self.repeat[client] -1
            if self.repeat[client] == 0:
                self._download_complete(client, response)
            else:
                client.send(request)
        else:
            log.error("Response: %s %s" % (response.code, response.reason))

    def _download_complete(self, client, response):
        self.clients.append(client)
        self.complete = self.complete + 1
        if self.complete == self.nclients:
            log.complete()
            self.complete = 0
            clients = self.clients
            self.clients = []
            if clients[0].receiving.diff() < 1:
                self.download = []
                self.length <<= 1
                log.start("* Download %d bytes" % self.length)
                for client in clients:
                    self._measure_download(client)
                return
            if self.flags & FLAG_UPLOAD:
                body = response.body.read()
                # there are many ADSLs around
                body = body[:len(body)/4]
                log.debug("Using %d bytes for upload" % len(body))
            else:
                body = None
            if self.flags & FLAG_UPLOAD:
                log.start("* Upload")
            for client in clients:
                if self.flags & FLAG_UPLOAD:
                    self._measure_upload(client, StringIO(body))
                else:
                    self._speedtest_complete(client)

    #
    # Measure upload speed
    # If we passed for download we receive a body that is 1/4
    # of the one we downloaded (because there are many ADSLs
    # around).  Otherwise, send a sequence of zeroes, even if
    # it should be better to send random bytes.
    #

    def _measure_upload(self, client=None, body=None):
        if not client:
            client = Client()
        if not body:
            body = StringIO("\0" * 1048576)
        self.repeat[client] = 2
        m = Message()
        compose(m, method="POST", uri=self.uri + "upload",
         body=body, mimetype="application/octet-stream")
        client.notify_success = self._measured_upload
        client.send(m)

    def _measured_upload(self, client, request, response):
        if response.code == "200":
            speed = client.sending.speed()
            self.upload.append(speed)
            self.repeat[client] = self.repeat[client] -1
            if self.repeat[client] == 0:
                self._upload_complete(client)
            else:
                # need to rewind the body
                request.body.seek(0)
                client.send(request)
        else:
            log.error("Response: %s %s" % (response.code, response.reason))

    def _upload_complete(self, client):
        self.clients.append(client)
        self.complete = self.complete + 1
        if self.complete == self.nclients:
            log.complete()
            self.complete = 0
            clients = self.clients
            self.clients = []
            for client in clients:
                self._speedtest_complete(client)

    #
    # Speedtest complete
    # Here we wait for all the clients to terminate the test and
    # we collect/print the results.
    #

    def _speedtest_complete(self, client=None):
        if client and client.handler:
            client.handler.close()
        self.complete = self.complete + 1
        if self.complete == self.nclients:
            self.speedtest_complete()

    def speedtest_complete(self):
        pass

#
# Test unit
#

USAGE = "Usage: %s [-sVv] [-a test] [-n count] [-O fmt] [--help] [base-URI]\n"

HELP = USAGE +								\
"Tests: all*, download, latency, upload.\n"				\
"Fmts: bits*, bytes, raw.\n"						\
"Options:\n"								\
"  -a test  : Add test to the list of tests.\n"				\
"  --help   : Print this help screen and exit.\n"			\
"  -n count : Use count HTTP connections.\n"				\
"  -O fmt   : Format output numbers using fmt.\n"			\
"  -s       : Do not print speedtest statistics.\n"			\
"  -V       : Print version number and exit.\n"				\
"  -v       : Run the program in verbose mode.\n"

class VerboseClient(SpeedtestClient):
    def __init__(self, uri, nclients, flags):
        SpeedtestClient.__init__(self, uri, nclients, flags)
        self.formatter = None

    def speedtest_complete(self):
        stdout.write("Timestamp: %d\n" % timestamp())
        stdout.write("URI: %s\n" % self.uri)
        stdout.write("Length: %d\n" % self.length)
        # latency
        if self.flags & FLAG_LATENCY:
            stdout.write("Connect:")
            for x in self.connect:
                stdout.write(" %f" % x)
            stdout.write("\n")
            stdout.write("Latency:")
            for x in self.latency:
                stdout.write(" %f" % x)
            stdout.write("\n")
        # download
        if self.flags & FLAG_DOWNLOAD:
            stdout.write("Download:")
            for x in self.download:
                stdout.write(" %s" % self.formatter(x))
            stdout.write("\n")
        # upload
        if self.flags & FLAG_UPLOAD:
            stdout.write("Upload:")
            for x in self.upload:
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

# should be 'http://speedtest.neubot.org/'
URI = "http://www.neubot.org:8080/"

def main(args):
    flags = 0
    new_client = VerboseClient
    fmt = "bits"
    nclients = 1
    # parse
    try:
        options, arguments = getopt(args[1:], "a:n:O:sVv", ["help"])
    except GetoptError:
        stderr.write(USAGE % args[0])
        exit(1)
    # options
    for name, value in options:
        if name == "-a":
            if not FLAGS.has_key(value):
                log.error("Invalid argument to -a: %s" % value)
                exit(1)
            flags |= FLAGS[value]
        elif name == "--help":
            stdout.write(HELP % args[0])
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
        elif name == "-s":
            new_client = SpeedtestClient
        elif name == "-V":
            stdout.write(version + "\n")
            exit(0)
        elif name == "-v":
            log.verbose()
    # sanity
    if len(arguments) > 1:
        stderr.write(USAGE % args[0])
        exit(1)
    elif len(arguments) == 1:
        uri = arguments[0]
    else:
        uri = URI
    if flags == 0:
        flags = FLAG_ALL
    # run
    client = new_client(uri, nclients, flags)
    if new_client == VerboseClient:
        client.formatter = FORMATTERS[fmt]
    loop()

if __name__ == "__main__":
    main(argv)
