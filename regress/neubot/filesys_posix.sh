#!/bin/sh

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
# Regression test for neubot/filesys_posix.py
#

#
# FIXME This regression test works with the BSD version of stat(1)
# only and should be fixed such that it works with Linux too.
#

if [ `id -u` -ne 0 ]; then
    echo "$0: you must be root to run this test" 1>&2
    exit 1
fi

printf "Initialize test..."
(
    set -e
    rm -rf -- /tmp/neubot
)
if [ $? -ne 0 ]; then
    printf "ERROR\n"
    exit 1
fi
printf "OK\n"

#
# A/B/C
#

#
# We assume that 'nobody' exists and we don't compare the
# results directly vs. its user and group IDs, because they
# may be negative numbers, e.g. on MacOSX nobody user id's
# -2.  That makes the comparison problematic because they
# are not always treated as signed numbers.
# So we compare against the user and group name, which is
# 'nobody' in BSD and 'nogroup' in Debian.
#

printf "Create /A/B/C in /tmp/neubot with owner nobody..."
(
    set -e
    python neubot/filesys_posix.py -d /tmp/neubot -u nobody A B C
)
if [ $? -ne 0 ]; then
    printf "ERROR\n"
    exit 1
fi
printf "OK\n"

printf "Make sure /tmp/neubot type, permissions and owner are OK..."
(
    set -e
    [ -d /tmp/neubot ]
    [ $(stat /tmp/neubot|awk '{print $3}') = 'drwxr-xr-x' ]
    [ $(stat /tmp/neubot|awk '{print $5}') = 'nobody' ]
    [ $(stat /tmp/neubot|awk '{print $6}') = 'nobody' ] ||
      [ $(stat /tmp/neubot|awk '{print $6}') = 'nogroup' ]
)
if [ $? -ne 0 ]; then
    printf "NO\n"
    exit 1
fi
printf "YES\n"

printf "Make sure /tmp/neubot/A type, permissions and owner are OK..."
(
    set -e
    [ -d /tmp/neubot/A ]
    [ $(stat /tmp/neubot/A|awk '{print $3}') = 'drwxr-xr-x' ]
    [ $(stat /tmp/neubot/A|awk '{print $5}') = 'nobody' ]
    [ $(stat /tmp/neubot/A|awk '{print $6}') = 'nobody' ] ||
      [ $(stat /tmp/neubot/A|awk '{print $6}') = 'nogroup' ]
)
if [ $? -ne 0 ]; then
    printf "NO\n"
    exit 1
fi
printf "YES\n"

printf "Make sure /tmp/neubot/A/B type, permissions and owner are OK..."
(
    set -e
    [ -d /tmp/neubot/A/B ]
    [ $(stat /tmp/neubot/A/B|awk '{print $3}') = 'drwxr-xr-x' ]
    [ $(stat /tmp/neubot/A/B|awk '{print $5}') = 'nobody' ]
    [ $(stat /tmp/neubot/A/B|awk '{print $6}') = 'nobody' ] ||
      [ $(stat /tmp/neubot/A/B|awk '{print $6}') = 'nogroup' ]
)
if [ $? -ne 0 ]; then
    printf "NO\n"
    exit 1
fi
printf "YES\n"

printf "Make sure /tmp/neubot/A/B/C permissions and owner are OK..."
(
    set -e
    [ -f /tmp/neubot/A/B/C ]
    [ $(stat /tmp/neubot/A/B/C|awk '{print $3}') = '-rw-r--r--' ]
    [ $(stat /tmp/neubot/A/B/C|awk '{print $5}') = 'nobody' ]
    [ $(stat /tmp/neubot/A/B/C|awk '{print $6}') = 'nobody' ] ||
      [ $(stat /tmp/neubot/A/B/C|awk '{print $6}') = 'nogroup' ]
)
if [ $? -ne 0 ]; then
    printf "NO\n"
    exit 1
fi
printf "YES\n"

#
# A/B/D
#

printf "Create /A/B/D in /tmp/neubot with owner nobody..."
(
    set -e
    python neubot/filesys_posix.py -d /tmp/neubot -u nobody A B D
)
if [ $? -ne 0 ]; then
    printf "ERROR\n"
    exit 1
fi
printf "OK\n"

printf "Make sure /tmp/neubot/A/B/D permissions and owner are OK..."
(
    set -e
    [ -f /tmp/neubot/A/B/D ]
    [ $(stat /tmp/neubot/A/B/D|awk '{print $3}') = '-rw-r--r--' ]
    [ $(stat /tmp/neubot/A/B/D|awk '{print $5}') = 'nobody' ]
    [ $(stat /tmp/neubot/A/B/D|awk '{print $6}') = 'nobody' ] ||
      [ $(stat /tmp/neubot/A/B/D|awk '{print $6}') = 'nogroup' ]
)
if [ $? -ne 0 ]; then
    printf "NO\n"
    exit 1
fi
printf "YES\n"

#
# A/K/D
#

printf "Create /A/K/D in /tmp/neubot with owner nobody..."
(
    set -e
    python neubot/filesys_posix.py -d /tmp/neubot -u nobody A K D
)
if [ $? -ne 0 ]; then
    printf "ERROR\n"
    exit 1
fi
printf "OK\n"

printf "Make sure /tmp/neubot/A/K type, permissions and owner are OK..."
(
    set -e
    [ -d /tmp/neubot/A/K ]
    [ $(stat /tmp/neubot/A/K|awk '{print $3}') = 'drwxr-xr-x' ]
    [ $(stat /tmp/neubot/A/K|awk '{print $5}') = 'nobody' ]
    [ $(stat /tmp/neubot/A/K|awk '{print $6}') = 'nobody' ] ||
      [ $(stat /tmp/neubot/A/K|awk '{print $6}') = 'nogroup' ]
)
if [ $? -ne 0 ]; then
    printf "NO\n"
    exit 1
fi
printf "YES\n"

printf "Make sure /tmp/neubot/A/K/D permissions and owner are OK..."
(
    set -e
    [ -f /tmp/neubot/A/K/D ]
    [ $(stat /tmp/neubot/A/K/D|awk '{print $3}') = '-rw-r--r--' ]
    [ $(stat /tmp/neubot/A/K/D|awk '{print $5}') = 'nobody' ]
    [ $(stat /tmp/neubot/A/K/D|awk '{print $6}') = 'nobody' ] ||
      [ $(stat /tmp/neubot/A/K/D|awk '{print $6}') = 'nogroup' ]
)
if [ $? -ne 0 ]; then
    printf "NO\n"
    exit 1
fi
printf "YES\n"

printf "Cleanup after test..."
(
    set -e
    rm -rf -- /tmp/neubot
)
if [ $? -ne 0 ]; then
    printf "ERROR\n"
    exit 1
fi
printf "OK\n"
