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
# Make sure database schema version is consistent between
# database/table_config.py and database/migrate.py.
#

TABLE_CONFIG=$(grep ^SCHEMA_VERSION neubot/database/table_config.py	\
               |awk -F= '{print $2}'|tr -d \'|tr -d ' ')
MIGRATE=$(python neubot/database/migrate2.py)

if [ "$TABLE_CONFIG" != "$MIGRATE" ]; then
    echo "<ERR> Inconsistent database schema version" 1>&2
    echo "<ERR> Table config: $TABLE_CONFIG, migrate: $MIGRATE" 1>&2
    exit 1
fi
