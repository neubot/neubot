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

ADDRESS = "127.0.0.1"
FAMILY = socket.AF_INET
PORT = "9774"

from neubot.http.servers import Server
from neubot.http.servers import SimpleConnection
from neubot.http.messages import Message
from neubot.http.messages import compose

#
# BaseComposer.
# We employ classes derived from BaseComposer to compose the response
# body in HTML and plain-text format (and possibly we will add some
# more formats in the future, such as JSON, and XML).
# The general idea of a composer is that all the pieces of the res-
# ponse body are appended to a vector, and, when all the pieces have
# been appended, it is possible to serialize it into a StringIO.
# We serialize into a StringIO because this the format compose() ex-
# pects the response body to be.
#

class BaseComposer:
    def __init__(self):
        self.vector = []

    def stringio(self):
        content = "".join(self.vector)
        stringio = StringIO.StringIO(content)
        return stringio

#
# TextPlain Composer.
# This is a line-oriented composer, and so the base operation it
# provides is the one that appends a line to the vector.
# However it is also possible to write data using the Record-Jar
# Format [1] adding headers and record-separators.
# To avoid confusion between free-format and Record-JAR we prep-
# end a space to lines starting with '%%' and we *assume* that
# the receiver does not identify '<space>%%' as a separator.
# [While we employ just free-format we plan to employ Record-JAR
#  when the textual API becomes more coarse-grained.]
#
# See [1] http://www.faqs.org/docs/artu/ch05s02.html
#

class TextPlainComposer(BaseComposer):
    def __init__(self):
        BaseComposer.__init__(self)

    def append_separator(self):
        self.vector.append("%%\r\n")

    def append_header(self, name, value):
        self.vector.append(name)
        self.vector.append(": ")
        self.vector.append(value)
        self.vector.append("\r\n")

    def append_line(self, line):
        if line.startswith("%%"):
            self.vector.append(" ")
        self.vector.append(line)
        self.vector.append("\r\n")

#
# XHTML composer.
# The general idea of this composer is to try to use <div>,
# <span>, and other generic elements rather than  <table>.
# The purpose of this constructor is to provide a workable
# interface when Javascript is not implemented.
# When Javascript is implemented it is probably better to
# employ AJAX coupled with a set of static (and *nice*) web
# pages.
# So, the body we construct here is a sequence of <div> tags,
# where each <div> is made of zero of more <span>s.  For this
# reason we need an helper class that represents the content
# of a <div> element.
# XXX An open issue is that we don't escape what we send and
# so we must need to be VERY careful when we add strings to
# the composer.
#

DOCTYPE =                                                              \
'<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"\r\n'   \
' "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">'

class DivContent:
    def __init__(self):
        self.vector = []

    def append_link(self, name, uri):
        self.vector.append("<span>")
        self.vector.append("<a href=\"%s\">%s</a>" % (uri, name))
        self.vector.append("</span>")

    def append_text(self, text):
        self.vector.append("<span>")
        self.vector.append(text)
        self.vector.append("</span>")

    def append_toggle_button(self, action):
        self.vector.append("<span>")
        self.vector.append("<form action=\"%s\" method=\"post\">" % action)
        self.vector.append("<input type=\"hidden\" name=\"toggle\"\\>")
        self.vector.append("<input type=\"submit\" value=\"Toggle\"\\>")
        self.vector.append("</form>")
        self.vector.append("</span>")

class XHTMLComposer(BaseComposer):
    def __init__(self, title):
        BaseComposer.__init__(self)
        self.vector.append(DOCTYPE)
        self.vector.append("<html>")
        self.vector.append("<head>")
        self.vector.append("<title> %s </title>" % title)
        self.vector.append("</head>")
        self.vector.append("<body>")

    def stringio(self):
        self.vector.append("</body>")
        self.vector.append("</html>")
        # merge-in
        vector = self.vector
        self.vector = []
        for elem in vector:
            if isinstance(elem, DivContent):
                for x in elem.vector:
                    self.vector.append(x)
            else:
                self.vector.append(elem)
        # marshal
        self._tidy()
        return BaseComposer.stringio(self)

    def append_div(self):
        div = DivContent()
        self.vector.append("<div>")
        self.vector.append(div)
        self.vector.append("</div>")
        return div

    #
    # We need to special-case <a>, <input>, <script>, and
    # <title> because we always emit these tags on a single
    # line.
    # We can safely raise ValueError()s here because the
    # code in UIConnection converts exceptions in "500 In-
    # ternal Server Error".
    #

    SPECIAL = ["a", "input", "script", "title"]

    def _indent(self, indent, elem):
        self.vector.append(" " * indent)
        self.vector.append(elem)
        self.vector.append("\r\n")

    def _tidy(self):
        vector = self.vector
        self.vector = []
        indent = 0
        for elem in vector:
            if elem.startswith("<"):
                i = elem.find(">")
                if i == -1:
                    raise ValueError("Malformed HTML")
                name = elem[1:i]
                # closing-tag
                if name.startswith("/"):
                    indent = indent - 1
                    if indent < 0:
                        raise ValueError("Malformed HTML")
                    self._indent(indent, elem)
                    continue
                # SGML-directive
                if name.startswith("!"):
                    self._indent(indent, elem)
                    continue
                # special-case
                if name in self.SPECIAL:
                    self._indent(indent, elem)
                    continue
                # default
                self._indent(indent, elem)
                indent = indent + 1
            else:
                self._indent(indent, elem)

#
# A connection with an UIClient.
# Most of the work is done in the parent because the parent
# contains the tables required to dispatch the request.
# Here we just check for exceptions because we want to sim-
# plify the code of the parent a little.
#

class UIConnection(SimpleConnection):
    def __init__(self, parent, handler):
        SimpleConnection.__init__(self, parent, handler)

    def got_request(self, m):
        try:
            self.parent.got_request(self, m)
        except KeyboardInterrupt:
            raise
        except:
            m1 = Message()
            compose(m1, code="500", reason="Internal Server Error")
            self.reply(m, m1)

#
# UIServer
# This class listens for incoming connections and process incoming
# requests.
# We employ dispatch tables as much as possible because we want to
# avoid the burden (and obscurity) of generating HTML at hand.
# From an high level perspective the code is organized as follows:
# 1. handlers for each defined URI; 2. code that dispatches the
# request to the proper handler; 3. code that listens for incoming
# connections.
# When a connection is created a UIConnection class is attached to
# it, and this class will immediately upcall us when a full request
# has been received.
#

class UIServer(Server):

    def BOOL(self, value):
        return value.upper() not in ["0", "FALSE", "NO"]

    #
    #  _     _                     _ _
    # / |   | |__   __ _ _ __   __| | |
    # | |   | '_ \ / _` | '_ \ / _` | |/ _ \ '__/ __|
    # | |_  | | | | (_| | | | | (_| | |  __/ |  \__ \
    # |_(_) |_| |_|\__,_|_| |_|\__,_|_|\___|_|  |___/
    #
    #

    #
    # Handler for /
    #

    ROOT = [{
        "name": "enabled",
        "uri": "/enabled",
        "reader": lambda: str(neubot.auto.enabled),
    },{
        "name": "force",
        "uri": "/force",
        "reader": lambda: str(neubot.config.force),
    },{
        "name": "logs",
        "uri": "/logs",
        "reader": lambda: str(len(neubot.log.getlines())) + " lines"
    },{
        "name": "results",
        "uri": "/results",
        "reader": lambda: str(len(neubot.database.export())) + " lines"
    },{
        "name": "state",
        "uri": "/state",
        "reader": lambda: neubot.config.state,
    }]

    def root_get_html(self, uri):
        composer = XHTMLComposer("%s on neubot" % uri)
        for dictionary in self.ROOT:
            div = composer.append_div()
            div.append_link(dictionary["name"], dictionary["uri"])
            div.append_text(dictionary["reader"]())
        return composer.stringio()

    def root_get_plain(self, uri):
        composer = TextPlainComposer()
        for dictionary in self.ROOT:
            composer.append_header(dictionary["name"], dictionary["reader"]())
        return composer.stringio()

    #
    # Handler for /enabled
    # XXX It is a pity that the "Toggle" button does not stay
    # on the same line of the other <span>s.
    # The result of pressing the "Toggle" button is always the
    # "toggle=" string because we specify the name but not the
    # value (we don't need the value because we just need to
    # know that we have to toggle :-P).
    #

    def enabled_get_html(self, uri):
        composer = XHTMLComposer("%s on neubot" % uri)
        div = composer.append_div()
        div.append_text("enabled")
        div.append_text(str(neubot.auto.enabled))
        div.append_toggle_button("/enabled")
        return composer.stringio()

    def enabled_get_plain(self, uri):
        composer = TextPlainComposer()
        composer.append_line(str(neubot.auto.enabled))
        return composer.stringio()

    def enabled_post(self, body):
        if body.strip() == "toggle=":
            neubot.auto.enabled = not neubot.auto.enabled
            return True
        else:
            return False

    def enabled_put(self, body):
        neubot.auto.enabled = self.BOOL(body.strip())
        return True

    #
    # Handler for /force
    #

    def force_get_html(self, uri):
        composer = XHTMLComposer("%s on neubot" % uri)
        div = composer.append_div()
        div.append_text("force")
        div.append_text(str(neubot.config.force))
        div.append_toggle_button("/force")
        return composer.stringio()

    def force_get_plain(self, uri):
        composer = TextPlainComposer()
        composer.append_line(str(neubot.config.force))
        return composer.stringio()

    def force_post(self, body):
        if body.strip() == "toggle=":
            neubot.config.force = not neubot.config.force
            return True
        else:
            return False

    def force_put(self, body):
        neubot.config.force = self.BOOL(body.strip())
        return True

    #
    # Handler for /logs
    #

    def logs_get_html(self, uri):
        composer = XHTMLComposer("%s on neubot" % uri)
        for timestamp, line in neubot.log.getlines():
            composer.append_div().append_text(line)
        return composer.stringio()

    def logs_get_plain(self, uri):
        composer = TextPlainComposer()
        for timestamp, line in neubot.log.getlines():
            composer.append_line(line)
        return composer.stringio()

    #
    # Handler for /results
    #

    def results_get_html(self, uri):
        composer = XHTMLComposer("%s on neubot" % uri)
        for line in neubot.database.export():
            composer.append_div().append_text(line)
        return composer.stringio()

    def results_get_plain(self, uri):
        composer = TextPlainComposer()
        for line in neubot.database.export():
            composer.append_line(line)
        return composer.stringio()

    #
    # Handler for /state
    #

    def state_get_html(self, uri):
        composer = XHTMLComposer("%s on neubot" % uri)
        composer.append_div().append_text(neubot.config.state)
        return composer.stringio()

    def state_get_plain(self, uri):
        composer = TextPlainComposer()
        composer.append_line(neubot.config.state)
        return composer.stringio()

    #
    #  ____          _ _                 _       _
    # |___ \      __| (_)___ _ __   __ _| |_ ___| |__
    #   __) |    / _` | / __| '_ \ / _` | __/ __| '_ \
    #  / __/ _  | (_| | \__ \ |_) | (_| | || (__| | | |
    # |_____(_)  \__,_|_|___/ .__/ \__,_|\__\___|_| |_|
    #                       |_|
    #

    #
    # We need to init the tables inside a function because
    # otherwise self does not exist.
    # We MUST have a "text/plain" entry for each "GET" method
    # of each registered URI, because below we will negotiate
    # mime using "text/plain" as the default type.
    # We MUST have an entry for each entry in the COMETs table,
    # because this entry will be employed to generate the de-
    # layed response.
    #

    def _init_tables(self):
        self.COMETs = {
            "/state/change": neubot.notify.STATECHANGE,
        }
        self.URIs = {
            "/": {
                "GET": {
                    "text/html": self.root_get_html,
                    "text/plain": self.root_get_plain,
                },
            },
            "/enabled": {
                "GET": {
                    "text/html": self.enabled_get_html,
                    "text/plain": self.enabled_get_plain,
                },
                "POST": {
                    "application/x-www-form-urlencoded": self.enabled_post,
                },
                "PUT": {
                    "text/plain": self.enabled_put,
                },
            },
            "/force": {
                "GET": {
                    "text/html": self.force_get_html,
                    "text/plain": self.force_get_plain,
                },
                "POST": {
                    "application/x-www-form-urlencoded": self.force_post,
                },
                "PUT": {
                    "text/plain": self.force_put,
                },
            },
            "/logs": {
                "GET": {
                    "text/html": self.logs_get_html,
                    "text/plain": self.logs_get_plain,
                },
            },
            "/results": {
                "GET": {
                    "text/html": self.results_get_html,
                    "text/plain": self.results_get_plain,
                },
            },
            "/state": {
                "GET": {
                    "text/html": self.state_get_html,
                    "text/plain": self.state_get_plain,
                },
            },
            "/state/change": {
                "GET": {
                    "text/html": self.state_get_html,
                    "text/plain": self.state_get_plain,
                },
            },
        }

    #
    # When negotiating the MIME type of the response we follow
    # the recommendation of RFC2616 section 10.4.7 and so we
    # default to "text/plain" if we don't find an acceptable MIME
    # type.  Then, it's up to the *receiver* to check whether the
    # response mime type is acceptable or not.
    #

    def _got_comet(self, event, atuple):
        handler, m = atuple
        self.got_request(handler, m, True)

    def got_request(self, handler, m, recurse=False):
        # comet
        if self.COMETs.has_key(m.uri) and not recurse:
            event = self.COMETs[m.uri]
            neubot.notify.subscribe(event, self._got_comet, (handler, m))
            return
        # not-found
        m1 = Message()
        if not self.URIs.has_key(m.uri):
            compose(m1, code="404", reason="Not Found")
            handler.reply(m, m1)
            return
        # not-allowed
        uri = self.URIs[m.uri]
        if not uri.has_key(m.method):
            compose(m1, code="405", reason="Method Not Allowed")
            m1["allow"] = reduce(lambda r, m: r + ", " + m, uri.keys())
            handler.reply(m, m1)
            return
        # set
        method = uri[m.method]
        if m.method in ["POST", "PUT"]:
            mimetype = m["content-type"]
            # unsupported-mime
            if not method.has_key(mimetype):
                compose(m1, code="415", reason="Unsupported Media Type")
                handler.reply(m, m1)
                return
            # process
            success = method[mimetype](m.body.read())
            # error
            if not success:
                compose(m1, code="500", reason="Internal Server Error")
                handler.reply(m, m1)
                return
            # ok
            location = "http://%s:%s%s" % (self.address,self.port,m.uri)
            compose(m1, code="303", reason="See Other")
            m1["location"] = location
            handler.reply(m, m1)
            return
        # get
        mimetype = neubot.http.negotiate_mime(m, method.keys(), "text/plain")
        stringio = method[mimetype](m.uri)
        compose(m1, code="200", reason="Ok", body=stringio, mimetype=mimetype)
        if m.method == "HEAD":
            stringio.seek(0, os.SEEK_END)
        handler.reply(m, m1)
        return

    #
    #  _____    _ _     _
    # |___ /   | (_)___| |_ ___ _ __
    #   |_ \   | | / __| __/ _ \ '_ \
    #  ___) |  | | \__ \ ||  __/ | | |
    # |____(_) |_|_|___/\__\___|_| |_|
    #
    #

    #
    # We don't want to listen on the open network because this
    # interface is meant to control neubot from the local host
    # only.
    # We fail if we cannot bind() the local address because it
    # seems a bit confusing to the average user to have some
    # instances of neubot around that it's not possible to
    # control.
    #

    def __init__(self):
        Server.__init__(self, ADDRESS, port=PORT, family=FAMILY)
        self.new_connection = UIConnection
        self._init_tables()

    def bind_failed(self):
        neubot.log.error("Is another instance of Neubot already running?")
        raise Exception("UI server: bind failed")

#
# auto should start-up the UI before entering into its
# main loop, using neubot.ui.init()
#

uiserver = UIServer()
init = uiserver.listen

#
# The purpose of this command is to test the UI server
# per-se, without the need of starting up auto.
#

def douiserver(vector):
    if len(vector) == 0:
        init()
        neubot.net.loop()

#
# Simple client capable of GETting and PUTting fine-grained
# text/plain variables.
# Yes, web-services should be coarse-grained, but this fine-
# grained API is valuable to test selected neubot bits.
#

from neubot.http.clients import SimpleClient

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
        compose(m, method="GET", uri=uri, keepalive=False)
        self.send(m)

    def get(self, variable):
        self.following = None
        m = Message()
        uri = makeuri(self.address, self.port, variable)
        compose(m, method="GET", uri=uri, keepalive=False)
        self.send(m)

    def set(self, variable, value):
        self.following = None
        m = Message()
        uri = makeuri(self.address, self.port, variable)
        compose(m, method="PUT", uri=uri, mimetype="text/plain",
                body=StringIO.StringIO(value), keepalive=False)
        self.send(m)

    def got_response(self, request, response):
        if response.code == "200":
            value = response.body.read()
            if self.following:
                sys.stdout.write(" " * 80)
                sys.stdout.write("\r" + value.strip())
                sys.stdout.flush()
                m = Message()
                uri = makeuri(self.address, self.port,
                              self.following+"/change")
                compose(m, method="GET", uri=uri, keepalive=False)
                self.send(m)
            else:
                sys.stdout.write(value)
        else:
            sys.stderr.write("Error: %s %s\n" %
             (response.code, response.reason))

textclient = TextClient(ADDRESS, PORT)

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
    "uiserver": {
        "descr": "Run UI server for testing purpose",
        "func": douiserver,
        "usage": "uiserver",
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
            sys.stdout.write(HELP % args[0])
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
