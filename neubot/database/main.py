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

import getopt
import sys

from neubot.database import DATABASE
from neubot.database import table_config
from neubot.database import table_speedtest

from neubot import compat
from neubot import utils

USAGE = '''\
Neubot database -- Low-level database operations

Usage: neubot database [-f FILE]
       neubot database [-f FILE] delete_all
       neubot database [-f FILE] dump
       neubot database [-f FILE] prune
       neubot database [-f FILE] regen_uuid
       neubot database [-f FILE] show

'''


def main(args):

    try:
        options, arguments = getopt.getopt(args[1:], "f:")
    except getopt.GetoptError:
        sys.stderr.write(USAGE)
        sys.exit(1)

    for key, value in options:
        if key == "-f":
            DATABASE.set_path(value)

    DATABASE.connect()

    if not arguments:
        sys.stdout.write('%s\n' % DATABASE.path)

    elif arguments[0] == "regen_uuid":
        if DATABASE.readonly:
            sys.exit('ERROR: readonly database')

        table_config.update(DATABASE.connection(),
          {"uuid": utils.get_uuid()}.iteritems())

    elif arguments[0] == "prune":
        if DATABASE.readonly:
            sys.exit('ERROR: readonly database')

        table_speedtest.prune(DATABASE.connection())

    elif arguments[0] == "delete_all":
        if DATABASE.readonly:
            sys.exit('ERROR: readonly database')

        table_speedtest.prune(DATABASE.connection(), until=utils.timestamp())
        DATABASE.connection().execute("VACUUM;")

    elif arguments[0] in ("show", "dump"):
        d = { "config": table_config.dictionarize(DATABASE.connection()),
             "speedtest": table_speedtest.listify(DATABASE.connection()) }
        if arguments[0] == "show":
            compat.json.dump(d, sys.stdout, indent=4)
        elif arguments[0] == "dump":
            compat.json.dump(d, sys.stdout)

    else:
        sys.stdout.write(USAGE)
        sys.exit(0)
