#
# This file is part of Neubot <http://www.neubot.org/>.
#
# Neubot is free software. See AUTHORS and COPYING for more
# information on the copying conditions.
#

# pylint: disable = missing-docstring

import os
import time

if os.name == 'nt':
    _TICKS_FUNC = time.clock
elif os.name == 'posix':
    _TICKS_FUNC = time.time
else:
    raise RuntimeError("Operating system not supported")

def _ticks():
    ''' Returns a real representing the most precise clock available
        on the current platform.  Note that, depending on the platform,
        the returned value MIGHT NOT be a timestamp.  So, you MUST
        use this clock to calculate the time elapsed between two events
        ONLY, and you must not use it with timestamp semantics. '''
    return _TICKS_FUNC()

def _strip_ipv4mapped_prefix(function):
    ''' Strip IPv4-mapped and IPv4-compatible prefix when the kernel does
        not implement a hard separation between IPv4 and IPv6 '''

    def do_strip(result):
        result = list(result)
        if result[0].startswith('::ffff:'):
            result[0] = result[0][7:]
        elif result[0].startswith('::') and result[0] != '::1':
            result[0] = result[0][2:]
        return tuple(result)

    return do_strip(function())

def _getpeername(sock):
    ''' getpeername() wrapper that strips IPv4-mapped prefix '''
    return _strip_ipv4mapped_prefix(sock.getpeername)

def _getsockname(sock):
    ''' getsockname() wrapper that strips IPv4-mapped prefix '''
    return _strip_ipv4mapped_prefix(sock.getsockname)
