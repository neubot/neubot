#!/usr/bin/env python
# Public domain, 2013 Simone Basso <bassosimone@gmail.com>

""" Test for NeubotPollable """

import ctypes
import sys

LIBNEUBOT = ctypes.CDLL("/usr/local/lib/libneubot.so")

def periodic_callback(poller):
    """ The periodic callback """
    sys.stdout.write("Periodic callback\n")
    schedule_callback(poller)

CALLBACK_T = ctypes.CFUNCTYPE(None, ctypes.c_void_p)
PERIODIC_CALLBACK = CALLBACK_T(periodic_callback)

def schedule_callback(poller):
    """ Schedule the periodic callback """
    LIBNEUBOT.NeubotPoller_sched(poller, ctypes.c_double(1.0),
      PERIODIC_CALLBACK, poller)

def main():
    """ Main function """
    poller = LIBNEUBOT.NeubotPoller_construct()
    schedule_callback(poller)
    LIBNEUBOT.NeubotPoller_loop(poller)

if __name__ == "__main__":
    main()
