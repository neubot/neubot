# neubot/utils.py

#
# Copyright (c) 2010-2011 Simone Basso <bassosimone@gmail.com>,
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
import os
import types

from neubot.log import LOG

def versioncmp(left, right):
    left = map(int, left.split("."))
    right = map(int, right.split("."))

    if len(left) > len(right):
        [right.append(0) for i in range(len(left) - len(right))]
    elif len(right) > len(left):
        [left.append(0) for i in range(len(right) - len(left))]

    for i in range(len(left)):
        diff = left[i] - right[i]
        if diff:
            return diff
    return 0

#
# When stdin, stdout, stderr are attached to console, seek(0)
# fails because it's not possible to rewind a console device.
# So, do not re-raise the Exception if the offending file was
# one of stdin, stdout, stderr.
#

def safe_seek(afile, offset, whence=os.SEEK_SET):
    try:
        afile.seek(offset, whence)
    except IOError:
        if afile not in [sys.stdin, sys.stdout, sys.stderr]:
            raise

#
# Here we don't use safe_seek() because safe_seek() makes sense
# when you want to rewind the body of an HTTP message because the
# user might want to read such body from the beginning.
# Instead, it would be wrong to safe_seek() when calculating file
# length, because if we pass one of (stdin, stdout, stderr) to this
# function we want the function to fail and not to return some
# non-sense file length (tell() does not fail for these files and
# just returns a long integer).
#

def file_length(afile):
    afile.seek(0, os.SEEK_END)
    length = afile.tell()
    afile.seek(0, os.SEEK_SET)
    return length

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
            return "%.1f %s%s" % (n, s, unit)
    return "%.1f %s" % (n, unit)

def unit_formatter(n, base10=False, unit=""):
    if base10:
        return _unit_formatter(n, [GIGA,MEGA,KILO], unit)
    else:
        return _unit_formatter(n, [GIBI,MEBI,KIBI], unit)

def speed_formatter(speed, base10=True, bytes=False):
    unit = "Byte/s"
    if not bytes:
        speed = speed * 8
        unit = "bit/s"
    return unit_formatter(speed, base10, unit)

def time_formatter(n):
    if n >= 1.0:
        return "%.1f s" % n
    elif n >= 0.001:
        n *= 1000
        return "%.1f ms" % n
    elif n >= 0.000001:
        n *= 1000000
        return "%.1f us" % n
    else:
        return "%f" % n

# Coerce types

def asciiify(s):
    return s.encode("ascii")

def stringify(value):
    if type(value) == types.UnicodeType:
        return value.encode("utf-8")
    elif type(value) == types.StringType:
        return value
    else:
        return str(value)

def unicodize(value):
    if type(value) == types.UnicodeType:
        return value
    elif type(value) == types.StringType:
        return value.decode("utf-8")
    else:
        return unicode(value)

def boolize(s):
    return str(s).lower() not in ("0", "off", "false", "no")
