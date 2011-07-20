# neubot/update.py

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
import getopt
import hashlib
import os
import sys
import threading
import time
import urllib2

INTERVAL = 4
PIECE = 1<<15

#
# Download updated archive.
#
# The caller is responsible of setting the base URI and version.
# Import as less Neubot code as possible, to minimize dependencies.
# The idea here is to allow others to work on this file without
# prior Neubot knowledge.
#
# The input is a dictionary with configuration, while the output
# is a StringIO that contains the downloaded and verified archive
# along with the file name.
#
# Where to store the archive is an open problem, maybe we can
# use the database.
#
class Download(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True
        self.baseuri = "http://releases.neubot.org/"
        self.version = "0.4"
        self.notify = lambda arg: None
        self.log = sys.stderr.write
        self.mysig = None
        self.path = None

#   def __del__(self):
#       print "Good-bye, cruel world"

    def configure(self, conf):
        self.baseuri = conf.get("update.baseuri", self.baseuri)
        self.version = conf.get("update.version", self.version)
        self.notify = conf.get("update.notify", self.notify)
        self.log = conf.get("update.log", self.log)

        if not self.baseuri[-1] == "/":
            self.baseuri += "/"

    def run(self):
        self.machinery(self.baseuri + "SHA256", StringIO.StringIO(),
                       self.got_signatures)

    def got_signatures(self, ofp):
        if not ofp:
            self.notify(None)
        else:
            self.mkpath()
            ofp.seek(0)
            for ln in ofp:
                v = ln.split()
                if len(v) == 2 and v[1] == self.path:
                    self.mysig = v[0]
                    break
            if not self.mysig:
                self.log("ERROR: cannot find signature for %s\n" % self.path)
                self.notify(None)
            else:
                self.machinery(self.baseuri + self.path,
                  StringIO.StringIO(), self.got_file)

    #
    # I know this function sucks a lot and is so stupid.
    # But, hey!, we need to start from a very basic policy
    # and then we can refine it a lot.
    #
    def mkpath(self):
        if os.name == "nt":
            self.path = "-".join(["neubot", self.version, "setup.exe"])
        elif os.name == "posix" and sys.platform == "darwin":
            self.path = "".join(["neubot-", self.version, ".app.zip"])
        else:
            self.path = "".join(["neubot-", self.version, ".zip"])

    def got_file(self, ofp):
        if not ofp:
            self.notify(None)
        else:
            ofp.seek(0)
            h = hashlib.new("sha256")
            h.update(ofp.read())
            if h.hexdigest() != self.mysig:
                self.log("Hash mismatch for %s\n" % self.version)
                self.notify(None)
            else:
                ofp.seek(0)
                ofp.name = self.path                                    #XXX
                self.notify(ofp)

    def machinery(self, uri, ofp, notify):
        try:
            self.log("INFO: downloading %s...\n" % uri)
            fp = urllib2.urlopen(uri)
            while True:
                piece = fp.read(PIECE)
                if not piece:
                    break
                ofp.write(piece)
                time.sleep(INTERVAL)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.log("ERROR: download failed for %s\n" % uri)
            notify(None)
        else:
            self.log("INFO: download succeded for %s\n" % uri)
            notify(ofp)

def testing_notify(ofp):
    if ofp:
        fp = open(ofp.name, "wb")
        fp.write(ofp.read())
        fp.close()
        sys.stderr.write("Saved: %s\n" % ofp.name)
        rv = 0
    else:
        sys.stderr.write("Error\n")
        rv = 1
    # Force program termination
    os._exit(rv)

def main(args):
    try:
        options, arguments = getopt.getopt(args[1:], "d:n:")
    except getopt.error:
        sys.stderr.write("usage: neubot update [-d uri] [-n version]\n")
        sys.exit(1)
    if arguments:
        sys.stderr.write("usage: neubot update [-d uri] [-n version]\n")
        sys.exit(1)

    conf = {"update.notify": testing_notify}
    for key, value in options:
        if key == "-d":
            conf["update.baseuri"] = value
        elif key == "-n":
            conf["update.version"] = value

    th = Download()
    th.configure(conf)
    th.start()
    del th
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main(sys.argv)
