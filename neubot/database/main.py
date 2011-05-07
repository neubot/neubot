# neubot/database/main.py

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

import sys

from neubot.config import CONFIG
from neubot.database import DATABASE
from neubot.database import table_config
from neubot.database import table_speedtest

from neubot import boot
from neubot import compat
from neubot import utils

def main(args):
    CONFIG.register_defaults({
        "database.delete_all": False,
        "database.dump": False,
        "database.prune": False,
        "database.regen_uuid": False,
        "database.show": False,
    })
    CONFIG.register_descriptions({
        "database.delete_all": "Delete all database entries",
        "database.dump": "Dump content in JSON format to standard output",
        "database.prune": "Remove old entries older than one year",
        "database.regen_uuid": "Regenerate unique identifier",
        "database.show": "Pretty-print database content",
    })

    boot.common("database", "Database manager", args)
    conf = CONFIG.copy()

    if conf["database.regen_uuid"]:
        table_config.update(DATABASE.connection(),
          {"uuid": utils.get_uuid()}.iteritems())

    if conf["database.prune"]:
        table_speedtest.prune(DATABASE.connection())

    if conf["database.delete_all"]:
        table_speedtest.prune(DATABASE.connection(), until=utils.timestamp())
        DATABASE.connection().execute("VACUUM;")

    if conf["database.show"] or conf["database.dump"]:
        d = { "config": table_config.dictionarize(DATABASE.connection()),
             "speedtest": table_speedtest.listify(DATABASE.connection()) }
        if conf["database.show"]:
            compat.json.dump(d, sys.stdout, indent=4)
        elif conf["database.dump"]:
            compat.json.dump(d, sys.stdout)
