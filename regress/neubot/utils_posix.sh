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

stat_perms()
{
    if [ "$(uname -s)" = "Linux" ]; then
        echo $(ls -ld $1|awk '{print $1}')
    else
        echo $(stat $1|awk '{print $3}')
    fi
}

stat_user()
{
    if [ "$(uname -s)" = "Linux" ]; then
        echo $(ls -ld $1|awk '{print $3}')
    else
        echo $(stat $1|awk '{print $5}')
    fi
}

stat_group()
{
    if [ "$(uname -s)" = "Linux" ]; then
        echo $(ls -ld $1|awk '{print $4}')
    else
        echo $(stat $1|awk '{print $6}')
    fi
}

nobody_group()
{
    if [ "$(uname -s)" = "Linux" ]; then
        echo "nogroup"
    else
        echo "nobody"
    fi
}

root_group()
{
    if [ "$(uname -s)" = "Linux" ]; then
        echo "root"
    else
        echo "wheel"
    fi
}

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
    [ $(python neubot/utils_posix.py -u $LOGNAME getpwnam pw_uid) = $(id -u) ]
)
if [ $? -ne 0 ]; then
    printf "NO\n"
    exit 1
fi
printf "YES\n"

printf "Make sure getpwnam correctly reports the gid..."
(
    set -e
    [ $(python neubot/utils_posix.py -u $LOGNAME getpwnam pw_gid) = $(id -g) ]
)
if [ $? -ne 0 ]; then
    printf "NO\n"
    exit 1
fi
printf "YES\n"

printf "Make sure getpwnam fails for nonexistent users..."
(
    set -e
    python neubot/utils_posix.py getpwnam -u nonexistent pw_uid 2>/dev/null
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
    python neubot/utils_posix.py -u 'nobody' mkdir XO
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
    [ "$(stat_perms XO)" = 'drwxr-xr-x' ]
)
if [ $? -ne 0 ]; then
    printf "NO\n"
    exit 1
fi
printf "YES\n"

printf "Make sure directory user is OK..."
(
    set -e
    [ "$(stat_user XO)" = 'nobody' ]
)
if [ $? -ne 0 ]; then
    printf "NO\n"
    exit 1
fi
printf "YES\n"

printf "Make sure directory group is OK..."
(
    set -e
    [ "$(stat_group XO)" = "$(nobody_group)" ]
)
if [ $? -ne 0 ]; then
    printf "NO\n"
    exit 1
fi
printf "YES\n"

printf "Make sure mkdir is idempotent..."
(
    set -e
    python neubot/utils_posix.py -u 'nobody' mkdir XO
    [ -d XO ]
    [ "$(stat_perms XO)" = 'drwxr-xr-x' ]
    [ "$(stat_user XO)" = 'nobody' ]
    [ "$(stat_group XO)" = "$(nobody_group)" ]
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
    python neubot/utils_posix.py -u 'nobody' mkdir XO
    [ "$(stat_perms XO)" = 'drwxr-xr-x' ]
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
    [ "$(stat_user XO)" = 'root' ]
    [ "$(stat_group XO)" = "$(root_group)" ]
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
    python neubot/utils_posix.py -u 'nobody' touch XO/f
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
    [ "$(stat_perms XO/f)" = '-rw-r--r--' ]
)
if [ $? -ne 0 ]; then
    printf "NO\n"
    exit 1
fi
printf "YES\n"

printf "Make sure file user is OK..."
(
    set -e
    [ "$(stat_user XO/f)" = 'nobody' ]
)
if [ $? -ne 0 ]; then
    printf "NO\n"
    exit 1
fi
printf "YES\n"

printf "Make sure file group is OK..."
(
    set -e
    [ "$(stat_group XO/f)" = "$(nobody_group)" ]
)
if [ $? -ne 0 ]; then
    printf "NO\n"
    exit 1
fi
printf "YES\n"

printf "Make sure touch is idempotent..."
(
    set -e
    python neubot/utils_posix.py -u 'nobody' touch XO/f
    [ -f XO/f ]
    [ "$(stat_perms XO/f)" = '-rw-r--r--' ]
    [ "$(stat_user XO/f)" = 'nobody' ]
    [ "$(stat_group XO/f)" = "$(nobody_group)" ]
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
    python neubot/utils_posix.py -u 'nobody' touch XO/f
    [ "$(stat_perms XO/f)" = '-rw-r--r--' ]
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
    [ "$(stat_user XO/f)" = 'root' ]
    [ "$(stat_group XO/f)" = "$(root_group)" ]
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
