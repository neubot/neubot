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

if __name__ == "__main__":
   from sys import path
   path.insert(0, ".")

from neubot import version
from StringIO import StringIO
from neubot.http.servers import Server
from neubot.http.messages import Message
from neubot.http.messages import compose
from neubot.http.clients import ClientController
from neubot.http.clients import Client
from neubot.notify import needs_publish
from neubot.notify import subscribe
from ConfigParser import SafeConfigParser
from neubot.notify import STATECHANGE
from mimetypes import guess_type
from mimetypes import guess_extension
from os.path import normpath
from urlparse import urlsplit
from neubot.database import database
from neubot.net.pollers import loop
from neubot.config import config
from neubot.state import state
from urllib import urlencode
from textwrap import wrap
from neubot import log
from cgi import parse_qs
from sys import stderr
from sys import stdout
from sys import stdin
from os import isatty
from neubot import pathnames
from sys import exit
from shlex import split
from sys import argv

class UIServer(Server):
    def __init__(self, config):
        Server.__init__(self, config.address, port=config.port)
        self.config = config
        self.table = {}
        self._initialize()

    def _initialize(self):
        self.table["/api/config"] = self._do_api_config
        self.table["/api/results"] = self._do_api_results
        self.table["/api/state"] = self._do_api_state

    def bind_failed(self):
        log.error("Is another neubot(1) instance running?")
        exit(1)

    def got_request(self, connection, request):
        try:
            self._map_request(connection, request)
        except KeyboardInterrupt:
            raise
        except:
            log.exception()
            response = Message()
            compose(response, code="500", reason="Internal Server Error")
            connection.reply(request, response)

    def _map_request(self, connection, request):
        uri = request.uri
        if uri.startswith("/api"):
            self._api_request(connection, request)
            return
        if uri.startswith("/"):
            if uri == "/":
                response = Message()
                compose(response, code="301", reason="Moved Permanently")
                location = "http://%s:%s/neubot.html" % (self.config.address,
                                                         self.config.port)
                response["location"] = location
                connection.reply(request, response)
                return
            filename = normpath(self.config.document_root + request.uri)
            log.debug("* Normalized path: %s" % filename)
            if filename.startswith(self.config.document_root):
                self._fs_request(connection, request, filename)
                return
        response = Message()
        compose(response, code="403", reason="Forbidden")
        connection.reply(request, response)

    def _fs_request(self, connection, request, filename):
        response = Message()
        try:
            body = open(filename, "rb")
        except (OSError, IOError):
            compose(response, code="404", reason="Not Found")
        else:
            mimetype, encoding = guess_type(filename)
            compose(response, code="200", reason="Ok",
                    body=body, mimetype=mimetype)
        connection.reply(request, response)

    def _do_delayed_request(self, event, atuple):
        connection, request = atuple
        self._api_request(connection, request, True)

    def _api_request(self, connection, request, recurse=False):
        try:
            resource, query = urlsplit(request.uri)[2:4]
            self.table[resource](connection, request, query, recurse)
        except KeyError:
            response = Message()
            compose(response, code="404", reason="Not Found")
            connection.reply(request, response)

    def _do_api_config(self, connection, request, query, recurse=False):
        response = Message()
        if request.method == "POST":
            config.update(request.body)
            location = "http://%s:%s/neubot.html" % (self.config.address,
                                                     self.config.port)
            compose(response, code="303", reason="See Other")
            response["location"] = location
            connection.reply(request, response)
            return
        stringio = config.marshal()
        compose(response, code="200", reason="Ok",
         mimetype="text/xml", body=stringio)
        connection.reply(request, response)

    def _do_api_results(self, connection, request, query, recurse=False):
        dictionary = parse_qs(query)
        filt, start, stop = None, 0, -1
        # parse
        if dictionary.has_key("filter"):
            filt = dictionary["filter"][0]
        if dictionary.has_key("start"):
            start = int(dictionary["start"][0])
            if start < 0:
                raise ValueError("Invalid query string")
        if dictionary.has_key("stop"):
            stop = int(dictionary["stop"][0])
            if stop < 0:
                raise ValueError("Invalid query string")
        # XML+HTTP
        response = Message()
        if not database.dbm:
            compose(response, code="204", reason="No Content")
            connection.reply(request, response)
            return
        stringio = database.dbm.get_cached_results(filt, start, stop)
        compose(response, code="200", reason="Ok",
                body=stringio, mimetype="text/xml")
        connection.reply(request, response)

    def _do_api_state(self, connection, request, query, recurse=False):
        dictionary = parse_qs(query)
        if not recurse and dictionary.has_key("t"):
            timestamp = dictionary["t"][0]
            stale = needs_publish(STATECHANGE, timestamp)
            if not stale:
                subscribe(STATECHANGE, self._do_delayed_request,
                          (connection, request))
                return
        stringio = state.marshal()
        response = Message()
        compose(response, code="200", reason="Ok",
                body=stringio, mimetype="text/xml")
        connection.reply(request, response)

#
# [ui]
# address: 127.0.0.1
# document_root: /usr/local/neubot/www/
# port: 9774
#

class UIConfig(SafeConfigParser):
    def __init__(self):
        SafeConfigParser.__init__(self)
        self.address = "127.0.0.1"
        self.document_root = pathnames.WWW
        self.port = "9774"

#   def check(self):
#       pass

    def readfp(self, fp, filename=None):
        SafeConfigParser.readfp(self, fp, filename)
        self._do_parse()

    def _do_parse(self):
        if self.has_option("ui", "address"):
            self.address = self.get("ui", "address")
        if self.has_option("ui", "document_root"):
            self.document_root = self.get("ui", "document_root")
        if self.has_option("ui", "port"):
            self.port = self.get("ui", "port")

    def read(self, filenames):
        SafeConfigParser.read(self, filenames)
        self._do_parse()

class UIModule:
    def __init__(self):
        self.config = UIConfig()
        self.server = None

    def configure(self, filenames, fakerc):
        self.config.read(filenames)
        self.config.readfp(fakerc)
        # XXX other modules need to read() it too
        fakerc.seek(0)

    def start(self):
        self.server = UIServer(self.config)
        self.server.listen()

ui = UIModule()

class UIClient(ClientController):
    def __init__(self, address, port):
        self.address = address
        self.port = port

    def makeuri(self, variable):
        return "http://" + self.address + ":" + self.port + variable

    def get(self, variable):
        self.following = None
        request = Message()
        uri = self.makeuri(variable)
        compose(request, method="GET", uri=uri, keepalive=False)
        client = Client(self)
        client.sendrecv(request)

    def set(self, variable, value):
        self.following = None
        request = Message()
        uri = self.makeuri("config")
        stringio = StringIO()
        stringio.write(urlencode({variable: value}))
        stringio.seek(0)
        compose(request, method="POST", uri=uri, body=stringio, keepalive=False,
         mimetype="application/x-www-form-urlencoded")
        client = Client(self)
        client.sendrecv(request)

    def got_response(self, client, request, response):
        if response.code == "303":
            log.info("See Other: %s" % response["location"])
            return
        if response.code == "200":
            stdout.write(response.body.read())
            return
        log.error("Error: %s %s" % (response.code, response.reason))

uiclient = UIClient("127.0.0.1", "9774")

def doget(vector):
    if len(vector) == 1:
        variable = vector[0]
        if not variable.startswith("/"):
            variable = "/" + variable
        uiclient.get(variable)
        loop()
    else:
        dohelp(["get"])

def doset(vector):
    if len(vector) == 2:
        variable, value = vector
        if not variable.startswith("/"):
            variable = "/" + variable
        uiclient.set(variable, value)
        loop()
    else:
        dohelp(["set"])

def dohelp(vector, ofile=stderr):
    if len(vector) == 0:
        line = "Commands:"
        for name in sorted(COMMANDS.keys()):
            line += " " + name
        for line in wrap(line):
            ofile.write(line + "\n")
        ofile.write("Try `help <command>' for more help.\n")
    elif len(vector) == 1:
        name = vector[0]
        if COMMANDS.has_key(name):
            dictionary = COMMANDS[name]
            ofile.write("Name  : %s - %s\n" % (name, dictionary["descr"]))
            ofile.write("Usage : %s\n" % dictionary["usage"])
        else:
            ofile.write("Unknown command: %s\n" % name)
            ofile.write("Try `help' to get a list of commands.\n")
    else:
        dohelp(["help"])

def dosource(vector):
    if len(vector) == 1:
        try:
            filename = vector[0]
            fin = open(filename, "r")
        except (IOError, OSError):
            log.exception()
        else:
            mainloop([], fin)
    else:
        dohelp(["source"])

def doversion(vector):
    if len(vector) == 0:
        stdout.write(version + "\n")
    else:
        dohelp(["version"])

def doquiet(vector):
    if len(vector) == 0:
        log.quiet()
    else:
        dohelp(["quiet"])

def doverbose(vector):
    if len(vector) == 0:
        log.verbose()
    else:
        dohelp(["verbose"])

def doexit(vector):
    if len(vector) == 0:
        exit(0)
    else:
        dohelp(["exit"])

#
# Dispatch table
# This table contains all the available commands.  Each command
# should check whether the user supplied enough arguments and, if
# not, the command should invoke dohelp() as follows:
#
#   dohelp(["command-name"])
#
# This will print the result on the standard error.  Below, we
# wrap dohelp() with a lambda function to ensure that it prints
# on the standard output when invoked as a command.
#

COMMANDS = {
    "exit" : {
        "descr": "Exit from the program",
        "func": doexit,
        "usage": "exit",
    },
    "get": {
        "descr": "Get the value of variable",
        "func": doget,
        "usage": "get variable",
    },
    "help": {
        "descr": "Get generic help or help on command",
        "func": lambda x: dohelp(x, ofile=stdout),
        "usage": "help [variable]",
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
            stderr.write("Unknown command: %s\n" % command)
            stderr.write("Try `help' to get a list of commands.\n")

#
# Main
# Process command line arguments and dispatch control to the
# specified command.  If no command is specified then enter in
# interactive mode and read commands from standard input until
# the user enters EOF.
#

from getopt import GetoptError
from getopt import getopt

USAGE =									\
"Usage: @PROGNAME@ --help\n"						\
"       @PROGNAME@ -V\n"						\
"       @PROGNAME@ [-v] [command [arguments]]\n"			\
"       @PROGNAME@ -S [-v] [-D name=value]\n"

HELP = USAGE +								\
"Options:\n"								\
"  -D name=value : Set configuration file property.\n"			\
"  --help        : Print this help screen and exit.\n"			\
"  -S            : Run the program in server mode.\n"			\
"  -v            : Run the program in verbose mode.\n"			\
"  -V            : Print version number and exit.\n"

def main(args):
    fakerc = StringIO()
    fakerc.write("[ui]")
    servermode = False
    # parse
    try:
        options, arguments = getopt(args[1:], "D:SvV", ["help"])
    except GetoptError:
        stderr.write(USAGE.replace("@PROGNAME@", args[0]))
        exit(1)
    # options
    for name, value in options:
        if name == "-D":
            fakerc.write(value + "\n")
        elif name == "--help":
            stdout.write(HELP.replace("@PROGNAME@", args[0]))
            exit(0)
        elif name == "-S":
            servermode = True
        elif name == "-v":
            log.verbose()
        elif name == "-V":
            stdout.write(version + "\n")
            exit(0)
    # config
    fakerc.seek(0)
    ui.configure(pathnames.CONFIG, fakerc)
    # server
    if servermode:
        if len (arguments) > 0:
            stderr.write(USAGE.replace("@PROGNAME@", args[0]))
            exit(1)
        ui.start()
        loop()
        exit(0)
    # arguments
    mainloop(arguments, stdin)

def mainloop(arguments, fin):
    if not arguments:
        while True:
            if isatty(fin.fileno()):
                stdout.write("neubot> ")
                stdout.flush()
            line = fin.readline()
            if not line:
                break
            vector = split(line)
            try:
                docommand(vector)
            except SystemExit:
                raise
            except:
                log.exception()
    else:
        docommand(arguments)

if __name__ == "__main__":
    main(argv)
