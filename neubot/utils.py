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

''' Miscellaneous utility functions '''

import sys
import os
import types
import time
import uuid

def safe_seek(afile, offset, whence=os.SEEK_SET):

    ''' Seek() implementation that does not throw IOError when
        @afile is a console device. '''

    #
    # When stdin, stdout, stderr are attached to console, seek(0)
    # fails because it's not possible to rewind a console device.
    # So, do not re-raise the Exception if the offending file was
    # one of stdin, stdout, stderr.
    #

    try:
        afile.seek(offset, whence)
    except IOError:
        if afile not in (sys.stdin, sys.stdout, sys.stderr):
            raise

#
# Unit formatter
#

# base 2
KIBI = (1024.0, "Ki")
MEBI = (1048576.0, "Mi")
GIBI = (1073741824.0, "Gi")

# base 10
KILO = (1000.0, "K")
MEGA = (1000000.0, "M")
GIGA = (1000000000.0, "G")

def _unit_formatter(number, unit_info, unit_name):
    ''' Internal unit formatter '''
    for scale, suffix in unit_info:
        if number >= scale:
            number /= scale
            return "%.1f %s%s" % (number, suffix, unit_name)
    return "%.1f %s" % (number, unit_name)

def unit_formatter(number, base10=False, unit=""):
    ''' Unit formatter '''
    if base10:
        return _unit_formatter(number, (GIGA, MEGA, KILO), unit)
    else:
        return _unit_formatter(number, (GIBI, MEBI, KIBI), unit)

def speed_formatter(speed, base10=True, bytez=False):
    ''' Speed formatter '''
    unit = "Byte/s"
    if not bytez:
        speed = speed * 8
        unit = "bit/s"
    return unit_formatter(speed, base10, unit)

def time_formatter(number):
    ''' Time formatter '''
    if number >= 1.0:
        return "%.1f s" % number
    elif number >= 0.001:
        number *= 1000
        return "%.1f ms" % number
    elif number >= 0.000001:
        number *= 1000000
        return "%.1f us" % number
    else:
        number *= 1000000
        return "%e us" % number

# Coerce types

def asciiify(string):
    ''' Convert something to ASCII string '''
    return string.encode("ascii")

def stringify(value):
    ''' Convert something to string '''
    if type(value) == types.UnicodeType:
        return value.encode("utf-8")
    elif type(value) == types.StringType:
        return value
    else:
        return str(value)

def unicodize(value):
    ''' Convert something to unicode '''
    if type(value) == types.UnicodeType:
        return value
    elif type(value) == types.StringType:
        return value.decode("utf-8")
    else:
        return unicode(value)

def intify(string):
    ''' Convert something to integer '''
    if type(string) == types.StringType or type(string) == types.UnicodeType:
        if string.lower() in ("off", "false", "no"):
            return 0
        elif string.lower() in ("on", "true", "yes"):
            return 1
    return int(string)

def smart_cast(value):
    ''' Return the proper cast depending on value '''
    if type(value) == types.StringType:
        return stringify
    elif type(value) == types.UnicodeType:
        return unicodize
    elif type(value) == types.BooleanType:
        return intify
    elif type(value) == types.IntType:
        return intify
    elif type(value) == types.LongType:
        return intify
    elif type(value) == types.FloatType:
        return float
    else:
        raise TypeError("No such cast for this type")

def timestamp():
    ''' Returns an integer representing the number of seconds elapsed
        since the EPOCH in UTC '''
    return int(time.time())

if os.name == 'nt':
    __TICKS = time.clock
elif os.name == 'posix':
    __TICKS = time.time
else:
    raise RuntimeError("Operating system not supported")

def ticks():
    ''' Returns a real representing the most precise clock available
        on the current platform.  Note that, depending on the platform,
        the returned value MIGHT NOT be a timestamp.  So, you MUST
        use this clock to calculate the time elapsed between two events
        ONLY, and you must not use it with timestamp semantics. '''
    return __TICKS()

#
# T()
#   Returns the opaque time, i.e. the time used to identify
#   events by the web user interface.  This is an integer, and
#   is calculated as follows: ``int(10^6 * ticks())``.  So,
#   the same caveat regarding ticks() also applies to this
#   function.
#
T = lambda: int(1000000 * ticks())

def get_uuid():
    ''' Returns per-Neubot random unique identifier.

        Each Neubot is identified by an anonymous unique random ID,
        which allows to perform time series analysis. '''
    return str(uuid.uuid4())
