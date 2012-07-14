# regress/neubot/database/table_bittorrent_gen.py

#
# Copyright (c) 2010-2011 Simone Basso <bassosimone@gmail.com>,
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

import random
import time

if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")

from neubot.utils import get_uuid
from neubot.utils import timestamp

#
# DAYS          Time-span of simulation in days
# ROWS          Number of rows in simulation
# UUIDS         Number of UUIDs in simulation
# IPCHANGETHR   Prob. that client IP address would change
# START         Simulation start time
#
DAYS = 100
ROWS = 100
UUIDS = 100
IPCHANGETHR = 0.05
START = timestamp() - DAYS * 24 * 60 * 60

def get_addr():
    return "".join(map(str, ["10.0.", random.randint(0, 254), ".",
                             random.randint(1, 254)]))

def get_time(start, days):
    return int(start + random.randint(0, days*3600*24))

class ResultIterator(object):

    def __init__(self):
        self.times = (get_time(START, DAYS) for _ in xrange(ROWS))
        self.uuids = [get_uuid() for _ in xrange(0, UUIDS)]
        self.addrs = {}

    def __iter__(self):
        return self

    def next(self):
        myuuid = self.uuids[random.randrange(0, len(self.uuids))]
        if not myuuid in self.addrs or random.random() < IPCHANGETHR:
            self.addrs[myuuid] = get_addr()
        return {
            "timestamp": next(self.times),
            "uuid": myuuid,
            "internal_address": self.addrs[myuuid],
            "real_address": self.addrs[myuuid],
            "remote_address": "130.192.91.211",
            "connect_time": random.random(),
            "download_speed": random.random() * 100000,
            "upload_speed": random.random() * 40000,
            "privacy_informed": 1,
            "privacy_can_collect": 1,
            "privacy_can_publish": 1,
            "neubot_version": "0.4.12",
            "platform": "Linux",
        }

if __name__ == "__main__":
    import pprint
    for d in ResultIterator():
        pprint.pprint(d)
