# neubot/utils.py
# Copyright (c) 2010 NEXA Center for Internet & Society

# This file is part of Neubot.
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

import json
import logging
import logging.handlers
import sys
import time
import traceback

import neubot

from os import SEEK_SET

def prettyprint_exception(write=logging.error, eol=""):
    neubot.log.exception()

def versioncmp(left, right):
    left = map(int, left.split("."))
    right = map(int, right.split("."))
    for i in range(0, 3):
        diff = left[i] - right[i]
        if diff:
            return diff
    return 0

def prettyprint_json(write, prefix, octets, eol=""):
    obj = json.loads(octets)
    lines = json.dumps(obj, ensure_ascii=True, indent=2)
    for line in lines.splitlines():
        write(prefix + line + eol)

def fixkwargs(kwargs, defaults):
    for key in defaults.keys():
        if not kwargs.has_key(key):
            kwargs[key] = defaults[key]
    return kwargs

#
# neubot.utils.timestamp()
#   Suitable for timestamping, returns an *integer* representing the
#   number of seconds elapsed since the epoch, in UTC.
#
# neubot.utils.ticks()
#   An very precise monotonic clock, that might not be suitable for
#   timestamping (depending on the plaform.)  It should only be used
#   to calculate the time elapsed between two events.
#

timestamp = lambda: int(time.time())

if sys.platform == 'win32':
    ticks = time.clock
else:
    ticks = time.time

#
# When stdin, stdout, stderr are attached to console, seek(0)
# fails because it's not possible to rewind a console device.
# So, do not re-raise the Exception if the offending file was
# one of stdin, stdout, stderr.
#

def safe_seek(afile, offset, whence=SEEK_SET):
    try:
        afile.seek(offset, whence)
    except IOError:
        if afile not in [sys.stdin, sys.stdout, sys.stderr]:
            raise

#
# Unit formatter
#

# base 2
KIBI = (1024.0, "Ki")
GIBI = (1073741824.0, "Gi")
MEBI = (1048576.0, "Mi")

# base 10
KILO = (1000.0, "K")
GIGA = (1000000000.0, "G")
MEGA = (1000000.0, "M")

def _unit_formatter(n, v, unit):
    for k, s in v:
        if n >= k:
            n /= k
            return "%.1f%s%s" % (n, s, unit)
    return "%.1f%s" % (n, unit)

def unit_formatter(n, base10=False, unit=""):
    if base10:
        return _unit_formatter(n, [GIGA,MEGA,KILO], unit)
    else:
        return _unit_formatter(n, [GIBI,MEBI,KIBI], unit)
