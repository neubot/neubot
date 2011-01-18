#!/usr/bin/env python

#
# Copyright (c) 2010 Simone Basso <bassosimone@gmail.com>,
#  NEXA Center for Internet & Society at Politecnico di Torino
# Copyright (c) 2011 Roberto D'Auria <everlastingfire@autistici.org>
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
import subprocess
import sqlite3
from datetime import datetime

# Fill the database with DAYS days and DAILYROWS daily records
# for each day, using UUIDS random-generated clients

DAYS = 100
DAILYROWS = 100
UUIDS = 100

# Probability of a client to change IP
IPCHANGETHR = 0.05

# Generation start timestamp
START = time.mktime(datetime(2011, 1, 1).timetuple())

# Server IP
REMOTE = "130.192.91.211"

# Insert query
RESULTS_SAVE = "INSERT INTO results VALUES(null, :tag, :result, :timestamp, \
                :ident);"

# Generate fake clients
clients = []
for i in xrange(UUIDS):
    clients.append([str(uuid.uuid4()), "10.0." + str(random.randint(0, 254)) + \
                    "." + str(random.randint(1, 254))])

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.stderr.write("Usage: %s database\n" % sys.argv[0])
        sys.exit(1)
    subprocess.call(["/usr/bin/env", "python", "neubot/database.py", "-i", sys.argv[1]])
    connection = sqlite3.connect(sys.argv[1])
    cursor = connection.cursor()
    tag = "speedtest"

    for i in xrange(DAYS):
        # To make realistic timestamps, we use randint() here
        timestamps = [random.randint(START + i*3600*24, START + (i+1)*3600*24) \
                      for x in xrange(DAILYROWS)]

        timestamps.sort() # Records are sorted by timestamp

        # IP changes
        for client in clients:
            r = random.random()
            if r < IPCHANGETHR:
                client[1] = "10.0." + str(random.randint(0, 254)) + "." + str(random.randint(1, 254))

        for timestamp in timestamps:
            download = str(random.random() * 100000)
            upload = str(random.random() * 40000)

            # Pick a random client
            n = random.randint(0, len(clients)-1)
            ident = clients[n][0]
            addr = clients[n][1]

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
</SpeedtestCollect>""" % (ident, timestamp, addr, addr, REMOTE, str(random.random()),
                str(random.random()), download, upload)
            cursor.execute(RESULTS_SAVE, {'tag': tag, 'result': result,
                'timestamp': timestamp, 'ident': ident})

    connection.commit()
    cursor.close()
    connection.close()
