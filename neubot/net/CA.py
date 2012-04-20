# neubot/net/CA.py

#
# Copyright (c) 2010-2011 Simone Basso <bassosimone@gmail.com>,
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

"""
 Generate private key and certificate file for the Neubot
 server.  This works under posix only and typically the file
 is written at `/etc/neubot/cert.pem`.

 The flaw of this schema is that if someone attacks neubot(1)
 successfully she has enough permissions to steal and/or modify
 the content of `/etc/neubot/cert.pem`.
"""

import sys
import os.path
import logging

if os.name != "posix":
    sys.exit("This command runs under 'posix' only")

import pwd
import subprocess

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.config import CONFIG
from neubot.main import common

CONFIG.register_defaults({
    "net.CA.basedir": "/etc/neubot",
    "net.CA.bits": 4096,
    "net.CA.cacert": "_cacert.pem",
    "net.CA.days": 1095,
    "net.CA.privkey": "_privkey.pem",
})

def main(args):
    """ Generate private key and certificate file for Neubot server """

    CONFIG.register_descriptions({
        "net.CA.bits": "Set private key bits number",
        "net.CA.cacert": "Set certificate file path",
        "net.CA.days": "Set days before expire",
        "net.CA.privkey": "Set private key file path",
    })

    common.main("net.CA", "generate test certificates", args)
    conf = CONFIG.copy()

    #
    # We need to be root because we play with file and
    # directories permissions and ownership which, in the
    # common case, cannot be done by other users.
    #
    if os.getuid():
        sys.exit("This command must be invoked as root")

    #
    # Force a standard umask but note that we will
    # override perms when needed.
    # Create the base directory and allow root to
    # populate and others just to read and list.
    #
    os.umask(0022)
    if not os.path.exists(conf["net.CA.basedir"]):
        os.mkdir(conf["net.CA.basedir"], 0755)

    # Make paths absolute
    conf["net.CA.cacert"] = os.sep.join([
                                         conf["net.CA.basedir"],
                                         conf["net.CA.cacert"]
                                        ])
    conf["net.CA.privkey"] = os.sep.join([
                                          conf["net.CA.basedir"],
                                          conf["net.CA.privkey"]
                                         ])

    # Generate RSA private key
    genrsa = [ "openssl", "genrsa", "-out", conf["net.CA.privkey"],
               str(conf["net.CA.bits"]) ]
    logging.debug("CA: exec: %s", genrsa)
    subprocess.call(genrsa)

    # Generate self-signed certificate
    req = [ "openssl", "req", "-new", "-x509", "-key", conf["net.CA.privkey"],
            "-out", conf["net.CA.cacert"], "-days", str(conf["net.CA.days"]) ]
    logging.debug("CA: exec: %s", req)
    subprocess.call(req)

    #
    # Merge private key and self-signed certificate into
    # the same file.  While there, remove the original files
    # from the filesystem.
    #
    certfile = os.sep.join([conf["net.CA.basedir"], "cert.pem"])
    outfp = open(certfile, "w")
    for key in ("net.CA.privkey", "net.CA.cacert"):
        fpin = open(conf[key], "r")
        os.unlink(conf[key])
        outfp.write(fpin.read())
        fpin.close()
    outfp.close()

    #
    # Allow the `_neubot` user to read the file and set
    # very restrictive permissions.  Note that an attacker
    # running as the `_neubot` user can steal or modify
    # the on-disk private key quite easily.  This is the
    # basic flaw of the current SSL schema in Neubot.
    #
    rec = pwd.getpwnam("_neubot")
    os.chown(certfile, rec.pw_uid, rec.pw_gid)
    os.chmod(certfile, 0400)

if __name__ == "__main__":
    main(sys.argv)
