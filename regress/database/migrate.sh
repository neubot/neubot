#!/bin/sh -e

#
# Copyright (c) 2012 Simone Basso <bassosimone@gmail.com>,
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
# Make sure the migration table contains all the functions
# defined in neubot/migrate.py
#

NUM_DEF=$(grep '^def migrate_from__' neubot/database/migrate.py|wc -l)
NUM_TBL=$(grep '^    migrate_from__' neubot/database/migrate.py|wc -l)

if [ "$NUM_DEF" != "$NUM_TBL" ]; then
    echo "<ERR> Not all migrate functions in migrate table" 1>&2
    echo "<ERR> Migrate funcs: $NUM_DEF, migrate table: $NUM_TBL" 1>&2
    exit 1
fi
