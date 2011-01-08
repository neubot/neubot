#!/usr/bin/env python

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

#
# Create fake database for testing
#

import sys
import uuid
import time
import random
from subprocess import call
from sqlite3 import connect

ROWS = 10

RESULTS_SAVE = "INSERT INTO results VALUES(null, :tag, :result, :timestamp, :ident);"

if __name__ == "__main__":
    if len(sys.argv) != 2:
        stderr.write("Usage: %s database\n" % sys.argv[0])
        sys.exit(1)
    call(["/usr/bin/env", "python", "neubot/database.py", "-i", sys.argv[1]])
    connection = connect(sys.argv[1])
    cursor = connection.cursor()
    count = 0
    tag = "speedtest"
    ident = str(uuid.uuid4())
    timestamp = int(time.time())
    remote = "130.192.91.211"

    while count < ROWS:
        addr = "10.0.0." + str(random.randint(1, 254))
        download = str(random.random() * 100000)
        upload = str(random.random() * 40000)
        result = """\
<SpeedtestCollect>\
<client>%s</client>\
<timestamp>%s</timestamp>\
<internalAddress>%s</internalAddress>\
<realAddress>%s</realAddress>\
<remoteAddress>%s</remoteAddress>\
<connectTime>%s</connectTime>\
<latency>%s</latency>\
<downloadSpeed>%s</downloadSpeed>\
<uploadSpeed>%s</uploadSpeed>\
</SpeedtestCollect>""" % (ident, timestamp, addr, addr, remote, str(random.random()),
            str(random.random()), download, upload)
        cursor.execute(RESULTS_SAVE, {'tag': tag, 'result': result,
            'timestamp': timestamp, 'ident': ident})
        count = count + 1
    connection.commit()
    cursor.close()
    connection.close()
