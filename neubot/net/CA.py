# neubot/net/CA.py

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

import getopt
import subprocess
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.options import OptionParser
from neubot.log import LOG

USAGE = """Neubot CA -- Generate test certificates

Usage: neubot CA [-Vv] [-D macro[=value]] [-f file] [--help]

Options:
    -D macro=value   : Set the value of the macro `macro`
    -f file          : Read options from the file `file`
    --help           : Print this help screen and exit
    -V               : Print version number and exit
    -v               : Run the program in verbose mode

Macros (defaults in square brackets):
    bits=count       : Generate count bits RSA privkey   [2048]
    cacert=file      : Override cacert file name         [cacert.pem]
    days=count       : Certificate valid for count days  [1095]
    privkey=file     : Override privkey file name        [privkey.pem]

"""

VERSION = "Neubot 0.3.5\n"

def main(args):

    conf = OptionParser()
    conf.set_option("CA", "bits", "2048")
    conf.set_option("CA", "cacert", "cacert.pem")
    conf.set_option("CA", "days", "1095")
    conf.set_option("CA", "privkey", "privkey.pem")

    try:
        options, arguments = getopt.getopt(args[1:], "D:Vv", ["help"])
    except getopt.error:
        sys.stderr.write(USAGE)
        sys.exit(1)

    if len(arguments) != 0:
        sys.stderr.write(USAGE)
        sys.exit(1)

    for name, value in options:
        if name == "-D":
             conf.register_opt(value, "CA")
             continue
        if name == "-f":
             conf.register_file(value)
             continue
        if name == "--help":
             sys.stdout.write(USAGE)
             sys.exit(0)
        if name == "-V":
             sys.stdout.write(VERSION)
             sys.exit(0)
        if name == "-v":
             LOG.verbose()
             continue

    conf.merge_files()
    conf.merge_environ()
    conf.merge_opts()

    bits = conf.get_option("CA", "bits")
    cacert = conf.get_option("CA", "cacert")
    days = conf.get_option("CA", "days")
    privkey = conf.get_option("CA", "privkey")

    genrsa = [ "openssl", "genrsa", "-out", privkey, bits ]
    LOG.debug("CA: exec: %s" % genrsa)
    subprocess.call(genrsa)

    req = [ "openssl", "req", "-new", "-x509", "-key", privkey,
            "-out", cacert, "-days", days ]
    LOG.debug("CA: exec: %s" % req)
    subprocess.call(req)

if __name__ == "__main__":
    main(sys.argv)
