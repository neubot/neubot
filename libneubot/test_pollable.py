#!/usr/bin/env python
# Public domain, 2013 Simone Basso <bassosimone@gmail.com>

""" Test for NeubotPollable """

import ctypes
import os
import sys

LIBNEUBOT = ctypes.CDLL("/usr/local/lib/libneubot.so")

def read_callback(pollable):
    """ Read callback """
    data = os.read(0, 1024)
    if not data:
        LIBNEUBOT.NeubotPollable_close(pollable)
        return

    sys.stdout.write(data)

def close_callback(pollable):
    """ Close callback """
    poller = LIBNEUBOT.NeubotPollable_poller(pollable)
    LIBNEUBOT.NeubotPoller_break_loop(poller)

def main():
    """ Main function """

    callback_type = ctypes.CFUNCTYPE(None, ctypes.c_void_p)
    _read_callback = callback_type(read_callback)
    _close_callback = callback_type(close_callback)


    poller = LIBNEUBOT.NeubotPoller_construct()

    pollable = LIBNEUBOT.NeubotPollable_construct(poller, _read_callback,
      None, _close_callback, None)
    LIBNEUBOT.NeubotPollable_attach(pollable, 0)
    LIBNEUBOT.NeubotPollable_set_readable(pollable)

    LIBNEUBOT.NeubotPoller_loop(poller)

if __name__ == "__main__":
    main()
