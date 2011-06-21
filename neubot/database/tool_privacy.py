#!/usr/bin/env python

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

import sqlite3
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.database import table_speedtest

PERMS = {}

# Inherit privacy settings
def main(args):
    arguments = args[1:]

    if len(arguments) != 1:
        sys.stderr.write("Usage: tool_privacy.py file\n")
        sys.exit(1)

    # Because I'm lazy below
    if not arguments[0].endswith(".sqlite3"):
        sys.stderr.write("error: Input file name must end with .sqlite3\n")
        sys.exit(1)

    connection = sqlite3.connect(arguments[0])
    connection.row_factory = sqlite3.Row

    #
    # Walk the database once and collect the most recent
    # permission for each unique identifier.  We will then
    # use it to decide whether we can publish or not.
    #
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM speedtest;")
    for row in cursor:
        PERMS[row['uuid']] = (row['privacy_informed'],
                              row['privacy_can_collect'],
                              row['privacy_can_share'])

    #
    # Build another database.  Yes, from scratch.  I don't
    # want leakage of your personal data to be possible, by
    # design.
    #
    output = sqlite3.connect(arguments[0].replace(".sqlite3",
                             "-privacy.sqlite3"))
    table_speedtest.create(output)

    #
    # Walk again the original database and honour the
    # privacy permissions.  We replace your Internet address
    # with all zeros, which is quite a good measure to
    # hide who you are.
    #
    total, can_share = 0, 0
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM speedtest;")
    for row in cursor:
        total = total + 1
        dictionary = dict(row)

        # Honour permissions
        if PERMS[dictionary['uuid']] != (1, 1, 1):
            can_share = can_share + 1
            dictionary['internal_address'] = "0.0.0.0"
            dictionary['real_address'] = "0.0.0.0"

        # Override permissions
        (dictionary['privacy_informed'],
         dictionary['privacy_can_collect'],
         dictionary['privacy_can_share']) = PERMS[dictionary['uuid']]

        # NOTE commit=False or it will take an Age!
        table_speedtest.insert(output, dictionary, commit=False)

    output.execute("VACUUM;")
    output.commit()

    #
    # Spit out per row statistics so we see how many rows we
    # can publish out of the total number of rows we have been
    # able to collect.
    #
    if total:
        sys.stdout.write("rows: %d/%d (%.02f%%)\n" % (can_share, total,
          (100.0 * can_share)/total))
    else:
        sys.stdout.write("rows: 0/0 (0.0%)\n")

    #
    # Now tell the poor programmer what is the distribution
    # of privacy permissions one can find in the wild.
    #
    per_uuid= {}
    total_uuid = len(PERMS.values())
    for tpl in PERMS.values():
        if not tpl in per_uuid:
            per_uuid[tpl] = 0
        per_uuid[tpl] += 1

    if total_uuid:
        for perm in per_uuid:
            sys.stdout.write("perms: %s: %d/%d (%.02f%%)\n" % (perm,
              per_uuid[perm], total_uuid, (100.0 * per_uuid[perm])/total_uuid))
    else:
        sys.stdout.write("perms: N/A: 0/0 (0.0%)\n")

    sys.exit(0)

if __name__ == "__main__":
    main(sys.argv)
