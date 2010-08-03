# neubot/ui.py
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

#
# RESTful User Interface API
#

import sys

if __name__ == "__main__":
   sys.path.append(".")

import StringIO
import logging
import neubot
import os
import shlex
import socket

address = "127.0.0.1"
family = socket.AF_INET
port = "9774"

class Receiver:
    def init(self):
        logging.debug("ui: starting up")
        m = neubot.http.compose(address=address, port=port, family=family)
        neubot.http.recv(m, listening=self.listening,
         cantbind=self.cantbind, received=self.received)

    def cantbind(self, m):
        logging.error("ui: can't bind '%s:%s'" % (address, port))

    def listening(self, m):
        logging.info("ui: listening at '%s:%s'" % (address, port))

    #
    # When negotiating the MIME type of the response we follow
    # the recommendation of RFC2616 section 10.4.7--this means
    # that we default to "text/plain" if we don't find an acc-
    # eptable MIME type (it's then up to the receiver to veri-
    # fy that the response type is acceptable.)
    #
    # Side note: It is very ugly to generate HTML at hand as
    # we do below--we probably need to invent and roll-out an
    # automatic solution to generate the output according to
    # the user preferences.
    #

    def received(self, m):
        m1 = None
        if m.uri == "/":
            if m.method == "GET":
                mimetype = neubot.http.negotiate_mime(m, ["text/html",
                 "text/plain"], "text/plain")
                body = []
                if mimetype == "text/html":
                    body.append("<HTML>\n")
                    body.append(" <HEAD>\n")
                    body.append("  <TITLE>Neubot config</TITLE>\n")
                    body.append(" </HEAD>\n")
                    body.append(" <BODY>\n")
                    body.append("  <TABLE>\n")
                    body.append("   <TR>\n")
                    body.append("    <TD>\n")
                    body.append('     <a href="/enabled">enabled</a>\n')
                    body.append("    </TD>\n")
                    body.append("    <TD>\n")
                    body.append("     %d\n" % neubot.auto.enabled)
                    body.append("    </TD>\n")
                    body.append("   </TR>\n")
                    body.append("   <TR>\n")
                    body.append("    <TD>\n")
                    body.append('     <a href="/logs">logs</a>\n')
                    body.append("    </TD>\n")
                    body.append("    <TD>\n")
                    body.append('     %d lines\n' % (len(neubot.log.getlines())))
                    body.append("    </TD>\n")
                    body.append("   </TR>\n")
                    body.append("   <TR>\n")
                    body.append("    <TD>\n")
                    body.append('     <a href="/results">results</a>\n')
                    body.append("    </TD>\n")
                    body.append("    <TD>\n")
                    body.append('     %d lines\n' % (len(neubot.database.export())))
                    body.append("    </TD>\n")
                    body.append("   </TR>\n")
                    body.append("   <TR>\n")
                    body.append("    <TD>\n")
                    body.append('     <a href="/state">state</a>\n')
                    body.append("    </TD>\n")
                    body.append("    <TD>\n")
                    body.append('     %s\n' % neubot.config.state)
                    body.append("    </TD>\n")
                    body.append("   </TR>\n")
                    body.append("   <TR>\n")
                    body.append("    <TD>\n")
                    body.append('     <a href="/force">force</a>\n')
                    body.append("    </TD>\n")
                    body.append("    <TD>\n")
                    body.append("     %d\n" % neubot.config.force)
                    body.append("    </TD>\n")
                    body.append("   </TR>\n")
                    body.append("  </TABLE>\n")
                    body.append(" </BODY>\n")
                    body.append("</HTML>\n")
                elif mimetype == "text/plain":
                    body.append("enabled = %d\r\n" % neubot.auto.enabled)
                    body.append("logs = %d lines\r\n" % len(neubot.log.getlines()))
                    body.append("results = %d lines\r\n" % len(neubot.database.export()))
                    body.append("state = %s\r\n" % neubot.config.state)
                    body.append("force = %d\r\n" % neubot.config.force)
                else:
                    raise Exception("Internal error")
                body = "".join(body)
                stringio = StringIO.StringIO(body)
                m1 = neubot.http.reply(m, mimetype=mimetype,
                 code="200", reason="Ok", body=stringio)
            else:
                m1 = neubot.http.reply(m, code="405",
                 reason="Method Not Allowed")
                m1["allow"] = "GET"
        elif m.uri == "/enabled":
            if m.method == "PUT":
                if m["content-type"] == "text/plain":
                    body = m.body.read().strip()
                    if body == "0":
                        neubot.auto.enabled = False
                    else:
                        neubot.auto.enabled = True
                    m1 = neubot.http.reply(m, code="204",
                     reason="No Content")
                else:
                    m1 = neubot.http.reply(m, code="415",
                     reason="Unsupported Media Type")
            elif m.method == "GET":
                mimetype = neubot.http.negotiate_mime(m, ["text/html",
                 "text/plain"], "text/plain")
                body = []
                if mimetype == "text/html":
                    body.append("<HTML>\n")
                    body.append(" <HEAD>\n")
                    body.append("  <TITLE>Neubot enabled</TITLE>\n")
                    body.append(" </HEAD>\n")
                    body.append(" <BODY>\n")
                    body.append("  <TABLE>\n")
                    body.append("   <TR>\n")
                    body.append("    <TD>\n")
                    body.append("     enabled")
                    body.append("    </TD>\n")
                    body.append("    <TD>\n")
                    body.append("     %d" % neubot.auto.enabled)
                    body.append("    </TD>\n")
                    body.append("   </TR>\n")
                    body.append("  </TABLE>\n")
                    body.append('  <FORM action="/enabled" method="post">\n')
                    if neubot.auto.enabled:
                        body.append('   <INPUT type="hidden" name="action" value="disable">\n')
                        body.append('   <INPUT type="submit" value="Disable">\n')
                    else:
                        body.append('   <INPUT type="hidden" name="action" value="enable">\n')
                        body.append('   <INPUT type="submit" value="Enable">\n')
                    body.append("  </FORM>\n")
                    body.append(" </BODY>\n")
                    body.append("</HTML>\n")
                elif mimetype == "text/plain":
                    body.append("%d\n" % neubot.auto.enabled)
                else:
                    raise Exception("Internal error")
                body = "".join(body)
                stringio = StringIO.StringIO(body)
                m1 = neubot.http.reply(m, code="200", mimetype=mimetype,
                 reason="Ok", body=stringio)
            elif m.method == "POST":
                if m["content-type"] == "application/x-www-form-urlencoded":
                    body = m.body.read()
                    if body == "action=disable" or body == "action=enable":
                        if body == "action=disable":
                            neubot.auto.enabled = False
                        else:
                            neubot.auto.enabled = True
                        m1 = neubot.http.reply(m, code="303",
                                          reason="See Other")
                        location = []
                        location.append("http://")
                        location.append(address)
                        location.append(":")
                        location.append(port)
                        location.append("/enabled")
                        m1["location"] = "".join(location)
                    else:
                        m1 = neubot.http.reply(m, code="500",
                         reason="Internal Server Error")
                else:
                    m1 = neubot.http.reply(m, code="415",
                     reason="Unsupported Media Type")
            else:
                m1 = neubot.http.reply(m, code="405",
                 reason="Method Not Allowed")
                m1["allow"] = "GET, PUT, POST"
        elif m.uri == "/logs":
            if m.method == "GET":
                lines = neubot.log.getlines()
                mimetype = neubot.http.negotiate_mime(m, ["text/html",
                 "text/plain"], "text/plain")
                body = []
                if mimetype == "text/html":
                    body.append("<HTML>\n")
                    body.append(" <HEAD>\n")
                    body.append("  <TITLE>Neubot logs</TITLE>\n")
                    body.append(" </HEAD>\n")
                    body.append(" <BODY>\n")
                    body.append("  <TABLE>\n")
                    for timestamp, line in lines:
                        body.append("   <TR>\n")
                        body.append("    <TD>\n")
                        body.append(str(timestamp))
                        body.append("    </TD>\n")
                        body.append("    <TD>\n")
                        body.append(line)
                        body.append("    </TD>\n")
                        body.append("   </TR>\n")
                    body.append("  </TABLE>\n")
                    body.append(" </BODY>\n")
                    body.append("</HTML>\n")
                elif mimetype == "text/plain":
                    for timestamp, line in lines:
                        body.append("[" + str(timestamp) + "] " + line + "\n")
                else:
                    raise Exception("Internal error")
                body = "".join(body)
                stringio = StringIO.StringIO(body)
                m1 = neubot.http.reply(m, code="200", mimetype=mimetype,
                 reason="Ok", body=stringio)
            else:
                m1 = neubot.http.reply(m, code="405",
                 reason="Method Not Allowed")
                m1["allow"] = "GET"
        elif m.uri == "/results":
            if m.method == "GET":
                results = neubot.database.export()
                mimetype = neubot.http.negotiate_mime(m, ["text/html",
                 "text/plain"], "text/plain")
                body = []
                if mimetype == "text/html":
                    body.append("<HTML>\n")
                    body.append(" <HEAD>\n")
                    body.append("  <TITLE>Neubot results</TITLE>\n")
                    body.append(" </HEAD>\n")
                    body.append(" <BODY>\n")
                    body.append("  <TABLE>\n")
                    for line in results:
                        body.append("   <TR>\n")
                        body.append("    <TD>\n")
                        body.append("     %s\n" % line)
                        body.append("    </TD>\n")
                        body.append("   </TR>\n")
                    body.append("  </TABLE>\n")
                    body.append(" </BODY>\n")
                    body.append("</HTML>\n")
                elif mimetype == "text/plain":
                    for line in results:
                        body.append(line)
                else:
                    raise Exception("Internal error")
                body = "".join(body)
                stringio = StringIO.StringIO(body)
                m1 = neubot.http.reply(m, code="200", mimetype=mimetype,
                 reason="Ok", body=stringio)
            else:
                m1 = neubot.http.reply(m, code="405",
                 reason="Method Not Allowed")
        elif m.uri == "/state":
            if m.method == "GET":
                mimetype = neubot.http.negotiate_mime(m, ["text/html",
                 "text/plain"], "text/plain")
                body = []
                if mimetype == "text/html":
                    body.append("<HTML>\n")
                    body.append(" <HEAD>\n")
                    body.append("  <TITLE>Neubot state</TITLE>\n")
                    body.append(" </HEAD>\n")
                    body.append(" <BODY>\n")
                    body.append("  %s\n" % neubot.config.state)
                    body.append(" </BODY>\n")
                    body.append("</HTML>\n")
                elif mimetype == "text/plain":
                    body.append(neubot.config.state)
                    body.append("\n")
                else:
                    raise Exception("Internal error")
                body = "".join(body)
                stringio = StringIO.StringIO(body)
                m1 = neubot.http.reply(m, code="200", mimetype=mimetype,
                 reason="Ok", body=stringio)
            else:
                m1 = neubot.http.reply(m, code="405",
                 reason="Method Not Allowed")
        elif m.uri == "/force":
            if m.method == "PUT":
                if m["content-type"] == "text/plain":
                    body = m.body.read().strip()
                    if body == "0":
                        neubot.config.force = False
                    else:
                        neubot.config.force = True
                    m1 = neubot.http.reply(m, code="204",
                     reason="No Content")
                else:
                    m1 = neubot.http.reply(m, code="415",
                     reason="Unsupported Media Type")
            elif m.method == "GET":
                mimetype = neubot.http.negotiate_mime(m, ["text/html",
                 "text/plain"], "text/plain")
                body = []
                if mimetype == "text/html":
                    body.append("<HTML>\n")
                    body.append(" <HEAD>\n")
                    body.append("  <TITLE>Neubot force</TITLE>\n")
                    body.append(" </HEAD>\n")
                    body.append(" <BODY>\n")
                    body.append("  <TABLE>\n")
                    body.append("   <TR>\n")
                    body.append("    <TD>\n")
                    body.append("     force")
                    body.append("    </TD>\n")
                    body.append("    <TD>\n")
                    body.append("     %d" % neubot.config.force)
                    body.append("    </TD>\n")
                    body.append("   </TR>\n")
                    body.append("  </TABLE>\n")
                    body.append('  <FORM action="/force" method="post">\n')
                    if neubot.config.force:
                        body.append('   <INPUT type="hidden" name="action" value="disable">\n')
                        body.append('   <INPUT type="submit" value="Disable">\n')
                    else:
                        body.append('   <INPUT type="hidden" name="action" value="enable">\n')
                        body.append('   <INPUT type="submit" value="Enable">\n')
                    body.append("  </FORM>\n")
                    body.append(" </BODY>\n")
                    body.append("</HTML>\n")
                elif mimetype == "text/plain":
                    body.append("%d\n" % neubot.config.force)
                else:
                    raise Exception("Internal error")
                body = "".join(body)
                stringio = StringIO.StringIO(body)
                m1 = neubot.http.reply(m, code="200", mimetype=mimetype,
                 reason="Ok", body=stringio)
            elif m.method == "POST":
                if m["content-type"] == "application/x-www-form-urlencoded":
                    body = m.body.read()
                    if body == "action=disable" or body == "action=enable":
                        if body == "action=disable":
                            neubot.config.force = False
                        else:
                            neubot.config.force = True
                        m1 = neubot.http.reply(m, code="303",
                                          reason="See Other")
                        location = []
                        location.append("http://")
                        location.append(address)
                        location.append(":")
                        location.append(port)
                        location.append("/force")
                        m1["location"] = "".join(location)
                    else:
                        m1 = neubot.http.reply(m, code="500",
                         reason="Internal Server Error")
                else:
                    m1 = neubot.http.reply(m, code="415",
                     reason="Unsupported Media Type")
            else:
                m1 = neubot.http.reply(m, code="405",
                 reason="Method Not Allowed")
                m1["allow"] = "GET, PUT, POST"
        elif m.uri == "/state/change":
            neubot.notify.subscribe(neubot.notify.STATECHANGE,
             self.statechanged, m)
        else:
            m1 = neubot.http.reply(m, code="404", reason="Not Found")
        if m1:
        # We need to improve our support for keepalive
            m1["connection"] = "close"
            neubot.http.send(m1)

    def statechanged(self, event, m):
        m1 = self.compose_state(m)
        neubot.http.send(m1)

    def compose_state(self, m):
        if m.method == "GET":
            mimetype = neubot.http.negotiate_mime(m, ["text/html",
             "text/plain"], "text/plain")
            body = []
            if mimetype == "text/html":
                body.append("<HTML>\n")
                body.append(" <HEAD>\n")
                body.append("  <TITLE>Neubot state</TITLE>\n")
                body.append(" </HEAD>\n")
                body.append(" <BODY>\n")
                body.append("  %s\n" % neubot.config.state)
                body.append(" </BODY>\n")
                body.append("</HTML>\n")
            elif mimetype == "text/plain":
                body.append(neubot.config.state)
                body.append("\n")
            else:
                raise Exception("Internal error")
            body = "".join(body)
            stringio = StringIO.StringIO(body)
            m1 = neubot.http.reply(m, code="200", mimetype=mimetype,
             reason="Ok", body=stringio)
        else:
            m1 = neubot.http.reply(m, code="405",
             reason="Method Not Allowed")
            m1["allow"] = "GET"
        return m1

receiver = Receiver()
init = receiver.init

USAGE = "Usage: neubot [options] ui [command [arguments]]\n"

def got_response(m):
    if m.code[0] == "2":
        body = m.body.read()
        sys.stdout.write(body)
    else:
        sys.stderr.write("ERROR: %s %s\n" % (m.code, m.reason))

def sent_request(m):
    neubot.http.recv(m, received=got_response)

def doget(vector):
    if len(vector) == 1:
        variable = vector[0]
        uri = "http://" + address + ":" + port + "/" + variable
        m = neubot.http.compose(method="GET", uri=uri, keepalive=False)
        neubot.http.send(m, sent=sent_request)
        neubot.net.loop()
    else:
        sys.stderr.write("Usage: get variable\n")

def dols(vector):
    if len(vector) == 0:
        uri = "http://" + address + ":" + port + "/"
        m = neubot.http.compose(method="GET", uri=uri, keepalive=False)
        neubot.http.send(m, sent=sent_request)
        neubot.net.loop()
    else:
        sys.stderr.write("Usage: ls\n")

def doset(vector):
    if len(vector) == 2:
        variable = vector[0]
        uri = "http://" + address + ":" + port + "/" + variable
        value = vector[1]
        value = value + "\n"
        stringio = StringIO.StringIO(value)
        m = neubot.http.compose(method="PUT", uri=uri, keepalive=False,
                                mimetype="text/plain", body=stringio)
        neubot.http.send(m, sent=sent_request)
        neubot.net.loop()
    else:
        sys.stderr.write("Usage: set variable value\n")

def dohelp(vector):
    if len(vector) == 0:
        sys.stdout.write("Commands:\n")
        sys.stdout.write("    get variable\n")
        sys.stdout.write("    help [command]\n")
        sys.stdout.write("    ls\n")
        sys.stdout.write("    set variable value\n")
        sys.stdout.write("    source file\n")
    elif len(vector) == 1:
        name = vector[0]
        if name == "get":
            sys.stdout.write("get variable\n")
            sys.stdout.write("    Get the value of variable\n")
        elif name == "help":
            sys.stdout.write("help [command]\n")
            sys.stdout.write("    Get generic help or help on command\n")
        elif name == "ls":
            sys.stdout.write("ls\n")
            sys.stdout.write("    List all available variables\n")
        elif name == "set":
            sys.stdout.write("set variable value\n")
            sys.stdout.write("    Set the value of variable\n")
        elif name == "source":
            sys.stdout.write("source file\n")
            sys.stdout.write("    Read commands from file\n")
        else:
            sys.stderr.write("help: Unknown command\n")
    else:
        sys.stderr.write("Usage: help [command]\n")

def dosource(vector):
    if len(vector) == 1:
        stdin = sys.stdin
        try:
            filename = vector[0]
            sys.stdin = open(filename, "r")
        except IOError:
            neubot.utils.prettyprint_exception(write=sys.stderr.write, eol="")
        else:
            main(["<<internal>>"])
        sys.stdin = stdin
    else:
        sys.stderr.write("Usage: source file\n")

def docommand(vector):
    if len(vector) > 0:
        command = vector[0]
        arguments = vector[1:]
        if command == "get":
            doget(arguments)
        elif command == "help":
            dohelp(arguments)
        elif command == "ls":
            dols(arguments)
        elif command == "set":
            doset(arguments)
        elif command == "source":
            dosource(arguments)
        else:
            dohelp([])

def main(argv):
    if len(argv) == 1:
        while True:
            if os.isatty(sys.stdin.fileno()):
                sys.stdout.write("neubot> ")
                sys.stdout.flush()
            line = sys.stdin.readline()
            if not line:
                break
            vector = shlex.split(line)
            docommand(vector)
    else:
        vector = argv[1:]
        docommand(vector)

if __name__ == "__main__":
    main(sys.argv)
