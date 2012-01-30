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
# Regression tests for neubot/utils_posix.py
#

if [ `id -u` -ne 0 ]; then
    echo "$0: you must be root to run this test" 1>&2
    exit 1
fi

#
# Garner confidence that getpwnam() correctly reports the right
# information for the root user and that it fails if passed a
# nonexistent user name.
#

printf "Make sure getpwnam correctly reports the uid..."
(
    set -e
    [ $(python neubot/utils_posix.py -f pw_uid getpwnam $LOGNAME) = $(id -u) ]
)
if [ $? -ne 0 ]; then
    printf "NO\n"
    exit 1
fi
printf "YES\n"

printf "Make sure getpwnam correctly reports the gid..."
(
    set -e
    [ $(python neubot/utils_posix.py -f pw_gid getpwnam $LOGNAME) = $(id -g) ]
)
if [ $? -ne 0 ]; then
    printf "NO\n"
    exit 1
fi
printf "YES\n"

printf "Make sure getpwnam fails for nonexistent users..."
(
    set -e
    python neubot/utils_posix.py getpwnam nonexistent 2>/dev/null
)
if [ $? -eq 0 ]; then
    printf "NO\n"
    exit 1
fi
printf "YES\n"

#
# We assume that 'nobody' exists and we don't compare the
# results directly vs. its user and group IDs, because they
# may be negative numbers, e.g. on MacOSX nobody user id's
# -2.  That makes the comparison problematic because they
# are not always treated as signed numbers.
# So we compare against the user and group name, which is
# 'nobody' in BSD and 'nogroup' in Debian.
#

NOBODY_UID=$(python neubot/utils_posix.py -f pw_uid getpwnam nobody)
NOBODY_GID=$(python neubot/utils_posix.py -f pw_gid getpwnam nobody)

#
# Garner confidence that the mkdir functionality works as
# expected, i.e. is idempotent and updates permissions and
# ownership as requested.
#

printf "Initializing mkdir test..."
(
    set -e
    rm -rf -- XO
)
if [ $? -ne 0 ]; then
    printf "ERROR\n"
    exit 1
fi
printf "OK\n"

printf "Make sure mkdir can create a new directory..."
(
    set -e
    python neubot/utils_posix.py -u $NOBODY_UID -g $NOBODY_GID mkdir XO
)
if [ $? -ne 0 ]; then
    printf "NO\n"
    exit 1
fi
printf "YES\n"

printf "Make sure the directory was actually created..."
(
    set -e
    [ -d XO ]
)
if [ $? -ne 0 ]; then
    printf "NO\n"
    exit 1
fi
printf "YES\n"

printf "Make sure directory permissions are OK..."
(
    set -e
    [ $(stat XO|awk '{print $3}') = 'drwxr-xr-x' ]
)
if [ $? -ne 0 ]; then
    printf "NO\n"
    exit 1
fi
printf "YES\n"

printf "Make sure directory user is OK..."
(
    set -e
    [ $(stat XO|awk '{print $5}') = 'nobody' ]
)
if [ $? -ne 0 ]; then
    printf "NO\n"
    exit 1
fi
printf "YES\n"

printf "Make sure directory group is OK..."
(
    set -e
    [ $(stat XO|awk '{print $6}') = 'nobody' ] ||
      [ $(stat XO|awk '{print $6}') = 'nogroup' ]
)
if [ $? -ne 0 ]; then
    printf "NO\n"
    exit 1
fi
printf "YES\n"

printf "Make sure mkdir is idempotent..."
(
    set -e
    python neubot/utils_posix.py -u $NOBODY_UID -g $NOBODY_GID mkdir XO
    [ -d XO ]
    [ $(stat XO|awk '{print $3}') = 'drwxr-xr-x' ]
    [ $(stat XO|awk '{print $5}') = 'nobody' ]
    [ $(stat XO|awk '{print $6}') = 'nobody' ] ||
      [ $(stat XO|awk '{print $6}') = 'nogroup' ]
)
if [ $? -ne 0 ]; then
    printf "NO\n"
    exit 1
fi
printf "YES\n"

printf "Initializing permissions test..."
(
    set -e
    chmod 000 XO
)
if [ $? -ne 0 ]; then
    printf "ERROR\n"
    exit 1
fi
printf "OK\n"

printf "Make sure mkdir updates permissions..."
(
    set -e
    python neubot/utils_posix.py -u $NOBODY_UID -g $NOBODY_GID mkdir XO
    [ $(stat XO|awk '{print $3}') = 'drwxr-xr-x' ]
)
if [ $? -ne 0 ]; then
    printf "NO\n"
    exit 1
fi
printf "YES\n"

printf "Make sure mkdir updates ownership..."
(
    set -e
    python neubot/utils_posix.py mkdir XO
    [ $(stat -f %u XO) = '0' ]
    [ $(stat -f %g XO) = '0' ]
)
if [ $? -ne 0 ]; then
    printf "NO\n"
    exit 1
fi
printf "YES\n"

#
# Garner confidence that the touch functionality works as
# expected, i.e. is idempotent and updates permissions and
# ownership as requested.
#

printf "Make sure touch can create a new file..."
(
    set -e
    python neubot/utils_posix.py -u $NOBODY_UID -g $NOBODY_GID touch XO/f
)
if [ $? -ne 0 ]; then
    printf "NO\n"
    exit 1
fi
printf "YES\n"

printf "Make sure the file was actually created..."
(
    set -e
    [ -f XO/f ]
)
if [ $? -ne 0 ]; then
    printf "NO\n"
    exit 1
fi
printf "YES\n"

printf "Make sure file permissions are OK..."
(
    set -e
    [ $(stat XO/f|awk '{print $3}') = '-rw-r--r--' ]
)
if [ $? -ne 0 ]; then
    printf "NO\n"
    exit 1
fi
printf "YES\n"

printf "Make sure file user is OK..."
(
    set -e
    [ $(stat XO/f|awk '{print $5}') = 'nobody' ]
)
if [ $? -ne 0 ]; then
    printf "NO\n"
    exit 1
fi
printf "YES\n"

printf "Make sure file group is OK..."
(
    set -e
    [ $(stat XO/f|awk '{print $6}') = 'nobody' ] ||
      [ $(stat XO/f|awk '{print $6}') = 'nogroup' ]
)
if [ $? -ne 0 ]; then
    printf "NO\n"
    exit 1
fi
printf "YES\n"

printf "Make sure touch is idempotent..."
(
    set -e
    python neubot/utils_posix.py -u $NOBODY_UID -g $NOBODY_GID touch XO/f
    [ -f XO/f ]
    [ $(stat XO/f|awk '{print $3}') = '-rw-r--r--' ]
    [ $(stat XO/f|awk '{print $5}') = 'nobody' ]
    [ $(stat XO/f|awk '{print $6}') = 'nobody' ] ||
      [ $(stat XO/f|awk '{print $6}') = 'nogroup' ]
)
if [ $? -ne 0 ]; then
    printf "NO\n"
    exit 1
fi
printf "YES\n"

printf "Initializing permissions test..."
(
    set -e
    chmod 000 XO/f
)
if [ $? -ne 0 ]; then
    printf "ERROR\n"
    exit 1
fi
printf "OK\n"

printf "Make sure touch updates permissions..."
(
    set -e
    python neubot/utils_posix.py -u $NOBODY_UID -g $NOBODY_GID touch XO/f
    [ $(stat XO/f|awk '{print $3}') = '-rw-r--r--' ]
)
if [ $? -ne 0 ]; then
    printf "NO\n"
    exit 1
fi
printf "YES\n"

printf "Make sure touch updates ownership..."
(
    set -e
    python neubot/utils_posix.py touch XO/f
    [ $(stat -f %u XO/f) = '0' ]
    [ $(stat -f %g XO/f) = '0' ]
)
if [ $? -ne 0 ]; then
    printf "NO\n"
    exit 1
fi
printf "YES\n"

#
# Make sure neither mkdir nor touch succeed when they are passed
# respectively a nondirectory and a nonfile.
#

printf "Make sure touch bails out if the target exists and is not a file..."
(
    set -e
    python neubot/utils_posix.py touch XO 2>/dev/null
)
if [ $? -eq 0 ]; then
    printf "NO\n"
    exit 1
fi
printf "YES\n"

printf "Make sure mkdir bails out if the target exists and is not a file..."
(
    set -e
    python neubot/utils_posix.py mkdir XO/f 2>/dev/null
)
if [ $? -eq 0 ]; then
    printf "NO\n"
    exit 1
fi
printf "YES\n"

#
# Cleanup
#

printf "After-test cleanup..."
(
    set -e
    rm -rf -- XO
)
if [ $? -ne 0 ]; then
    printf "ERROR\n"
    exit 1
fi
printf "OK\n"
