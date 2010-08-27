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
   sys.path.insert(0, ".")

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

#
# Simple client capable of GETting and PUTting fine-grained
# text/plain variables.
# Yes, web-services should be coarse-grained, but this fine-
# grained API is valuable to test selected neubot bits.
#

from neubot.http.clients import SimpleClient
from neubot.http.messages import Message
from neubot.http.messages import compose

def makeuri(address, port, variable):
    return "http://" + address + ":" + port + "/" + variable

class TextClient(SimpleClient):
    def __init__(self, address, port):
        SimpleClient.__init__(self)
        self.following = None
        self.address = address
        self.port = port

    def follow(self, variable):
        self.following = variable
        m = Message()
        uri = makeuri(self.address, self.port, variable)
        compose(m, method="GET", uri=uri)
        self.send(m)

    def get(self, variable):
        self.following = None
        m = Message()
        uri = makeuri(self.address, self.port, variable)
        compose(m, method="GET", uri=uri)
        self.send(m)

    def set(self, variable, value):
        self.following = None
        m = Message()
        uri = makeuri(self.address, self.port, variable)
        compose(m, method="PUT", uri=uri, mimetype="text/plain",
                body=StringIO.StringIO(value))
        self.send(m)

    def got_response(self, request, response):
        if response.code == "200":
            value = response.body.read()
            if self.following:
                sys.stdout.write(" " * 80)
                sys.stdout.write("\r" + value.strip())
                m = Message()
                uri = makeuri(self.address, self.port,
                              self.following+"/change")
                compose(m, method="GET", uri=uri)
                self.send(m)
            else:
                sys.stdout.write(value)
        else:
            sys.stderr.write("Error: %s %s\n" %
             (response.code, response.reason))

textclient = TextClient(address, port)

#
# Remote commands
# These commands send a request to a remote neubot and print
# the response on the standard output.
#

def dofollow(vector):
    if len(vector) == 1:
        variable = vector[0]
        textclient.follow(variable)
        neubot.net.loop()
    else:
        dohelp(["follow"], ofile=sys.stderr)


def doget(vector):
    if len(vector) == 1:
        variable = vector[0]
        textclient.get(variable)
        neubot.net.loop()
    else:
        dohelp(["get"], ofile=sys.stderr)

def dols(vector):
    if len(vector) == 0:
        textclient.get("")
        neubot.net.loop()
    else:
        dohelp(["ls"], ofile=sys.stderr)

def doset(vector):
    if len(vector) == 2:
        variable = vector[0]
        value = vector[1]
        value = value + "\n"
        textclient.set(variable, value)
        neubot.net.loop()
    else:
        dohelp(["set"], ofile=sys.stderr)

#
# Local commands
# These commands do not open a connection with a remote neubot
# but have just a local effect.
# The source() command is hackish because replaces standard
# input and re-runs main() using a fake argv.
#

def dohelp(vector, ofile=sys.stdout):
    if len(vector) == 0:
        ofile.write("Commands:\n")
        for name in sorted(COMMANDS.keys()):
            dictionary = COMMANDS[name]
            ofile.write("    %s\n" % dictionary["usage"])
    elif len(vector) == 1:
        name = vector[0]
        if COMMANDS.has_key(name):
            dictionary = COMMANDS[name]
            ofile.write("Usage: %s\n" % dictionary["usage"])
            ofile.write("    %s\n" % dictionary["descr"])
        else:
            ofile.write("Unknown command: %s\n" % name)
    else:
        dohelp(["help"], ofile=sys.stderr)

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
        dohelp(["source"], ofile=sys.stderr)

def doversion(vector):
    if len(vector) == 0:
        sys.stdout.write(neubot.version + "\n")
    else:
        dohelp(["version"], ofile=sys.stderr)

def doquiet(vector):
    if len(vector) == 0:
        neubot.log.quiet()
    else:
        dohelp(["quiet"], ofile=sys.stderr)

def doverbose(vector):
    if len(vector) == 0:
        neubot.log.verbose()
    else:
        dohelp(["verbose"], ofile=sys.stderr)

#
# Dispatch table
# This table contains all the available commands.  Each command
# should check whether the user supplied enough arguments and, if
# not, the command should invoke dohelp() as follows:
#
#   dohelp(["command-name"], ofile=sys.stderr)
#

COMMANDS = {
    "follow": {
        "descr": "Follow variable evolution over time",
        "func": dofollow,
        "usage": "follow variable",
    },
    "get": {
        "descr": "Get the value of variable",
        "func": doget,
        "usage": "get variable",
    },
    "help": {
        "descr": "Get generic help or help on command",
        "func": dohelp,
        "usage": "help [variable]",
    },
    "ls": {
        "descr": "List all available variables",
        "func": dols,
        "usage": "ls",
    },
    "quiet": {
        "descr": "Become quiet",
        "func": doquiet,
        "usage": "quiet",
    },
    "set": {
        "descr": "Set the value of variable",
        "func": doset,
        "usage": "set variable value",
    },
    "source": {
        "descr": "Read commands from file",
        "func": dosource,
        "usage": "source file",
    },
    "verbose": {
        "descr": "Become verbose",
        "func": doverbose,
        "usage": "verbose",
    },
    "version": {
        "descr": "Print neubot version",
        "func": doversion,
        "usage": "version",
    },
}

def docommand(vector):
    if len(vector) > 0:
        command = vector[0]
        arguments = vector[1:]
        if COMMANDS.has_key(command):
            dictionary = COMMANDS[command]
            docommand = dictionary["func"]
            docommand(arguments)
        else:
            dohelp([], ofile=sys.stderr)

#
# Main
# Process command line arguments and dispatch control to the
# specified command.  If no command is specified then enter in
# interactive mode and read commands from standard input until
# the user enters EOF.
#

from getopt import GetoptError
from getopt import getopt

USAGE = "Usage: %s [-vV] [--help] [command [arguments]]\n"

HELP = USAGE +								\
"Options:\n"								\
"  --help : Print this help screen and exit.\n"				\
"  -v     : Run the program in verbose mode.\n"				\
"  -V     : Print version number and exit.\n"

def main(args):
    # parse
    try:
        options, arguments = getopt(args[1:], "vV", ["help"])
    except GetoptError:
        sys.stderr.write(USAGE % args[0])
    # options
    for name, value in options:
        if name == "--help":
            sys.stdout.write(HELP)
            exit(0)
        elif name == "-v":
            neubot.log.verbose()
        elif name == "-V":
            sys.stdout.write(neubot.version+"\n")
            exit(0)
    # arguments
    if not arguments:
        while True:
            if os.isatty(sys.stdin.fileno()):
                sys.stdout.write("neubot> ")
                sys.stdout.flush()
            line = sys.stdin.readline()
            if not line:
                break
            vector = shlex.split(line)
            try:
                docommand(vector)
            except:
                neubot.log.exception()
    else:
        docommand(arguments)

if __name__ == "__main__":
    main(sys.argv)
