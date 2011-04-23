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

import subprocess
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.config import CONFIG
from neubot.log import LOG
from neubot import boot

CONFIG.register_defaults({
    "net.CA.bits": 2048,
    "net.CA.cacert": "cacert.pem",
    "net.CA.days": 1095,
    "net.CA.privkey": "privkey.pem",
})
CONFIG.register_descriptions({
    "net.CA.bits": "Set private key bits number",
    "net.CA.cacert": "Set certificate file path",
    "net.CA.days": "Set days before expire",
    "net.CA.privkey": "Set private key file path",
})

def main(args):
    boot.common("net.CA", "generate test certificates", args)
    conf = CONFIG.select("net.CA")

    genrsa = [ "openssl", "genrsa", "-out", conf["net.CA.privkey"],
               str(conf["net.CA.bits"]) ]
    LOG.debug("CA: exec: %s" % genrsa)
    subprocess.call(genrsa)

    req = [ "openssl", "req", "-new", "-x509", "-key", conf["net.CA.privkey"],
            "-out", conf["net.CA.cacert"], "-days", str(conf["net.CA.days"]) ]
    LOG.debug("CA: exec: %s" % req)
    subprocess.call(req)

if __name__ == "__main__":
    main(sys.argv)
