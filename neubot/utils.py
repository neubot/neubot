# neubot/utils.py

#
# Copyright (c) 2010 Simone Basso <bassosimone@gmail.com>,
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

from StringIO import StringIO
from neubot.times import ticks
from time import clock
from time import sleep
from time import time
from neubot.log import LOG
from sys import stdin
from sys import stdout
from sys import stderr

import signal
import os

if os.name == "posix":
    import pwd

def versioncmp(left, right):
    left = map(int, left.split("."))
    right = map(int, right.split("."))
    for i in range(0, 3):
        diff = left[i] - right[i]
        if diff:
            return diff
    return 0

def fixkwargs(kwargs, defaults):
    for key in defaults.keys():
        if not kwargs.has_key(key):
            kwargs[key] = defaults[key]
    return kwargs

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
        if afile not in [stdin, stdout, stderr]:
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

#
# Daemonize
#

DAEMON_SYSLOG = 1<<0
DAEMON_CHDIR = 1<<1
DAEMON_DETACH = 1<<2
DAEMON_SIGNAL = 1<<3
DAEMON_PIDFILE = 1<<4
DAEMON_DROP = 1<<5

DAEMON_ALL = (DAEMON_SYSLOG|DAEMON_CHDIR|DAEMON_DETACH|DAEMON_SIGNAL|
              DAEMON_PIDFILE|DAEMON_DROP)

USERS = ["_neubot", "nobody"]

def getpwnaml(users=USERS):
    passwd = None
    if os.name == "posix":
        for user in users:
            try:
                passwd = pwd.getpwnam(user)
            except KeyError:
                pass
            else:
                break
    return passwd

def getpwnamlx(users=USERS):
    passwd = getpwnaml(users)
    if not passwd:
        LOG.error("* Can't getpwnam for: %s" % str(users))
        # XXX Because we catch SystemExit where we should not
        os._exit(1)
    return passwd

def become_daemon(flags=DAEMON_ALL):
    if os.name == "posix":
        try:
            if flags & DAEMON_SYSLOG:
                LOG.debug("* Redirect logs to syslog(3)")
                LOG.redirect()
                for descriptor in range(0,3):
                    os.close(descriptor)
                devnull = os.open("/dev/null", os.O_RDWR)
                for descriptor in range(1,3):
                    os.dup2(devnull, descriptor)
            if flags & DAEMON_CHDIR:
                LOG.debug("* Move working directory to /")
                os.chdir("/")
            if flags & DAEMON_DETACH:
                LOG.debug("* Detach from controlling tty")
                if os.fork() > 0:
                    os._exit(0)
                LOG.debug("* Become leader of a new session")
                os.setsid()
                LOG.debug("* Detach from controlling session")
                if os.fork() > 0:
                    os._exit(0)
            if flags & DAEMON_SIGNAL:
                LOG.debug("* Ignoring the SIGINT signal")
                signal.signal(signal.SIGINT, signal.SIG_IGN)
            if flags & DAEMON_PIDFILE:
                pidfiles = ["/var/run/neubot.pid"]
                if os.environ.has_key("HOME"):
                    pidfiles.append(os.environ["HOME"] + "/.neubot/pidfile")
                for pidfile in pidfiles:
                    try:
                        f = open(pidfile, "wb")
                        f.write(str(os.getpid()) + "\n")
                        f.close()
                        LOG.debug("* Written pidfile: %s" % pidfile)
                        break
                    except (IOError, OSError):
                        pass
            if flags & DAEMON_DROP and os.getuid() == 0:
                passwd = getpwnamlx()
                os.setgid(passwd.pw_gid)
                os.setuid(passwd.pw_uid)
        except:
            LOG.error("fatal: become_daemon() failed")
            LOG.exception()
            os._exit(1)
    else:
        pass

#
# XML
#

def XML_text(node):
    vector = []
    if node.nodeType != node.ELEMENT_NODE:
        raise ValueError("Bad node type")
    element = node
    for node in element.childNodes:
        if node.nodeType != node.TEXT_NODE:
            continue
        text = node
        vector.append(text.data)
    return "".join(vector).strip()

def XML_to_string(document):
    return document.toprettyxml(indent="    ", newl="\n", encoding="utf-8")

def XML_to_stringio(document):
    return StringIO(XML_to_string(document))

#
# Stats
#

class SimpleStats(object):
    def __init__(self):
        self.begin()

    def __del__(self):
        pass

    def begin(self):
        self.start = ticks()
        self.stop = 0
        self.length = 0

    def end(self):
        self.stop = ticks()

    def account(self, count):
        self.length += count

    def diff(self):
        return self.stop - self.start

    def speed(self):
        return self.length / self.diff()

class Stats(object):
    def __init__(self):
        self.send = SimpleStats()
        self.recv = SimpleStats()


def asciify(s):
    try:
        return s.encode("ascii")
    except UnicodeDecodeError:
        raise ValueError("ssi: Cannot ASCIIfy path name")
