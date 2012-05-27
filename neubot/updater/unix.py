# neubot/updater/unix.py

#
# Copyright (c) 2011 Simone Basso <bassosimone@gmail.com>,
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
# ==============================================================
# The implementation of chroot in this file is loosely inspired
# to the one of OpenSSH session.c, revision 1.258, which is avail
# under the following license:
#
# Copyright (c) 1995 Tatu Ylonen <ylo@cs.hut.fi>, Espoo, Finland
#                    All rights reserved
#
# As far as I am concerned, the code I have written for this software
# can be used freely for any purpose.  Any derived versions of this
# software must be clearly marked as such, and if the derived work is
# incompatible with the protocol description in the RFC file, it must be
# called by a name other than "ssh" or "Secure Shell".
#
# SSH2 support by Markus Friedl.
# Copyright (c) 2000, 2001 Markus Friedl.  All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# ==============================================================
#

'''
 This is the privilege separated Neubot updater daemon.  It is
 started as a system daemon, runs as root, spawns and monitors an
 unprivileged child Neubot process and periodically checks for
 updates.  The check is not not performed by the privileged daemon
 itself but by a child process that runs on behalf of the
 unprivileged user ``_neubot_update``.
'''

#
# Like neubot/main/__init__.py this file is a Neubot entry point
# and so we must keep its name constant over time.
# I'm sorry that this file is so huge, but there is a valid reason
# to do that: It must be Python3 safe.  So that we're safe if the
# system migrates to Python3 because the updater can still download
# an updated version -- which hopefully is Python3 ready.
#

import asyncore
import collections
import getopt
import compileall
import errno
import syslog
import signal
import hashlib
import pwd
import re
import os.path
import sys
import time
import fcntl
import tarfile
import stat
import subprocess
import decimal
import shutil

# For portability to Python 3
if sys.version_info[0] == 3:
    import http.client as __lib_http
else:
    import httplib as __lib_http

if __name__ == '__main__':
    # PARENT/neubot/updater/unix.py
    sys.path.insert(0, os.path.dirname (os.path.dirname(os.path.dirname
                                        (os.path.abspath(__file__)))))

from neubot import updater_install
from neubot import utils_rc

# Note: BASEDIR/VERSIONDIR/neubot/updater/unix.py
VERSIONDIR = os.path.dirname(os.path.dirname(os.path.dirname(
                                 os.path.abspath(__file__))))
BASEDIR = os.path.dirname(VERSIONDIR)

# Version number in numeric representation
VERSION = "0.004012006"

# Configuration
CONFIG = {
    'channel': 'latest',
}

#
# Common
#

def __waitpid(pid, timeo=-1):
    ''' Wait up to @timeo seconds for @pid to exit() '''

    # Are we allowed to sleep 'forever'?
    if timeo >= 0:
        options = os.WNOHANG
    else:
        options = 0

    while True:
        try:

            # Wait for process to complete
            npid, status = os.waitpid(pid, options)

            if timeo >= 0 and npid == 0 and status == 0:
                timeo = timeo - 1
                if timeo < 0:
                    break
                time.sleep(1)
                continue

            # Make sure the process actually exited
            if os.WIFEXITED(status) or os.WIFSIGNALED(status):
                return npid, status

        except OSError:

            # For portability to Python3
            why = sys.exc_info()[1]

            # Make sure it's not a transient error
            if why[0] != errno.EINTR:
                raise

    return 0, 0

def __lookup_user_info(uname):

    '''
     Lookup and return the specified user's uid and gid.
     This function is not part of __change_user() because
     you may want to __chroot() once you have user info
     and before you drop root privileges.
    '''

    try:
        return pwd.getpwnam(uname)
    except KeyError:
        raise RuntimeError('No such user: %s' % uname)

def __change_user(passwd):

    '''
     Change user, group to @passwd.pw_uid, @passwd.pw_gid and
     setup a bare environement for the new user.  This function
     is typically used to drop root privileges but can also be
     used to sanitize the privileged daemon environment.

     More in detail, this function will:

     1. set the umask to 022;

     2. change group ID to @passwd.pw_gid;

     3. clear supplementary groups;

     4. change user ID to @passwd.pw_uid;

     5. purify environment.

     Optionally, you might want to invoke __chroot() before
     invoking this function.
    '''

    #
    # I've checked that this function does more or less
    # the same steps of OpenBSD setusercontext(3) and of
    # launchd(8) to drop privileges.
    # Note that this function does not invoke setlogin(2)
    # because that should be called when becoming a daemon,
    # AFAIK, not here.
    # For dropping privileges we try to follow the guidelines
    # established by Chen, et al. in "Setuid Demystified":
    #
    #   Since setresuid has a clear semantics and is able
    #   to set each user ID individually, it should always
    #   be used if available.  Otherwise, to set only the
    #   effective uid, seteuid(new euid) should be used; to
    #   set all three user IDs, setreuid(new uid, new uid)
    #   should be used.
    #

    # Set default umask (18 == 0022)
    os.umask(18)

    # Change group ID.
    if hasattr(os, 'setresgid'):
        os.setresgid(passwd.pw_gid, passwd.pw_gid, passwd.pw_gid)
    elif hasattr(os, 'setregid'):
        os.setregid(passwd.pw_gid, passwd.pw_gid)
    else:
        raise RuntimeError('Cannot drop group privileges')

    # Clear supplementary groups.
    os.setgroups([])

    # Change user ID.
    if hasattr(os, 'setresuid'):
        os.setresuid(passwd.pw_uid, passwd.pw_uid, passwd.pw_uid)
    elif hasattr(os, 'setreuid'):
        os.setreuid(passwd.pw_uid, passwd.pw_uid)
    else:
        raise RuntimeError('Cannot drop user privileges')

    # Purify environment
    for name in list(os.environ.keys()):
        del os.environ[name]
    os.environ = {
                  "HOME": "/",
                  "LOGNAME": passwd.pw_name,
                  "PATH": "/usr/local/bin:/usr/bin:/bin",
                  "TMPDIR": "/tmp",
                  "USER": passwd.pw_name,
                 }

def __chroot(directory):

    '''
     Make sure that it's safe to chroot to @directory -- i.e.
     that all path components are owned by root and that permissions
     are safe -- then chroot to @directory.
    '''

    #
    # This function is an attempt to translate into
    # Python the checks OpenSSH performs in safely_chroot()
    # of session.c.
    #

    if not directory.startswith('/'):
        raise RuntimeError('chroot directory must start with /')

    syslog.syslog(syslog.LOG_INFO, 'Checking "%s" for safety' % directory)

    components = collections.deque(os.path.split(directory))

    curdir = '/'
    while components:

        # stat(2) curdir
        statbuf = os.stat(curdir)

        # Is it a directory?
        if (not stat.S_ISDIR(statbuf.st_mode)):
            raise RuntimeError('Not a directory: "%s"' % curdir)

        # Are permissions safe? (18 == 0022)
        if (stat.S_IMODE(statbuf.st_mode) & 18) != 0:
            raise RuntimeError('Unsafe permissions: "%s"' % curdir)

        # Is the owner root?
        if statbuf.st_uid != 0:
            raise RuntimeError('Not owned by root: "%s"' % curdir)

        # Add next component
        if curdir != '/':
            curdir = '/'.join(curdir, components.popleft())
        else:
            curdir = ''.join(curdir, components.popleft())

    # Switch rootdir
    os.chdir(directory)
    os.chroot(directory)
    os.chdir("/")

def __chroot_naive(directory):

    '''
     Change the current working directory and the root to
     @directory and then change the current directory to
     the root directory.
    '''

    #
    # XXX Under MacOSX the ownership of / is unsafe per the
    # algorithm used by __chroot().  So here's this function
    # that performs the chroot dance and performs just a
    # simplified check.
    #

    if not directory.startswith('/'):
        raise RuntimeError('chroot directory must start with /')

    # stat(2) curdir
    statbuf = os.stat(directory)

    # Is it a directory?
    if (not stat.S_ISDIR(statbuf.st_mode)):
        raise RuntimeError('Not a directory: "%s"' % directory)

    # Are permissions safe? (18 == 0022)
    if (stat.S_IMODE(statbuf.st_mode) & 18) != 0:
        raise RuntimeError('Unsafe permissions: "%s"' % directory)

    # Is the owner root?
    if statbuf.st_uid != 0:
        raise RuntimeError('Not owned by root: "%s"' % directory)

    # Switch rootdir
    os.chdir(directory)
    os.chroot(directory)
    os.chdir("/")

def __go_background(pidfile=None, sigterm_handler=None, sighup_handler=None):

    '''
     Perform the typical steps to run in background as a
     well-behaved Unix daemon.

     In detail:

     1. detach from the current shell;

     2. become a session leader;

     3. detach from the current session;

     4. chdir to rootdir;

     5. redirect stdin, stdout, stderr to /dev/null;

     6. ignore SIGINT, SIGPIPE;

     7. write pidfile;

     8. install SIGTERM, SIGHUP handler;

    '''

    #
    # I've verified that the first chunk of this function
    # matches loosely the behavior of the daemon(3) function
    # available under BSD.
    # What is missing here is setlogin(2) which is not part
    # of python library.  Doh.
    #

    # detach from the shell
    if os.fork() > 0:
        os._exit(0)

    # create new session
    os.setsid()

    # detach from the session
    if os.fork() > 0:
        os._exit(0)

    # redirect stdio to /dev/null
    for fdesc in range(3):
        os.close(fdesc)
    for _ in range(3):
        os.open('/dev/null', os.O_RDWR)

    # chdir to rootdir
    os.chdir('/')

    # ignore SIGINT, SIGPIPE
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)

    # write pidfile
    if pidfile:
        filep = open(pidfile, 'w')
        filep.write('%d\n' % os.getpid())
        filep.close()

    # install SIGTERM, SIGHUP handler
    if sigterm_handler:
        signal.signal(signal.SIGTERM, sigterm_handler)
    if sighup_handler:
        signal.signal(signal.SIGHUP, sighup_handler)

def __printable_only(string):
    ''' Remove non-printable characters from string '''
    string = re.sub(r"[\0-\31]", "", string)
    return re.sub(r"[\x7f-\xff]", "", string)

#
# Download
#

def __download(address, rpath, tofile=False, https=False, maxbytes=67108864):

    '''
     Fork an unprivileged child that will connect to @address and
     download from @rpath, using https: if @https is True and http:
     otherwise.  If @tofile is False the output is limited to 8192
     bytes and returned as a string.  Otherwise, if @tofile is True,
     the return value is the path to the file that contains the
     response body.
    '''

    syslog.syslog(syslog.LOG_INFO,
                  '__download: address=%s rpath=%s tofile=%d '
                  'https=%d maxbytes=%d' % (address, rpath,
                  tofile, https, maxbytes))

    # Create communication pipe
    fdin, fdout = os.pipe()
    flags = fcntl.fcntl(fdin, fcntl.F_GETFL)
    flags |= os.O_NONBLOCK
    fcntl.fcntl(fdin, fcntl.F_SETFL, flags)

    if not tofile:
        lfdesc, lpath = -1, None
    else:

        # Build output file name
        basename = os.path.basename(rpath)
        lpath = os.sep.join([BASEDIR, basename])

        #
        # If the output file exists and is a regular file
        # unlink it because it might be an old possibly failed
        # download attempt.
        #
        if os.path.exists(lpath):
            if not os.path.isfile(lpath):
                raise RuntimeError('%s: not a file' % lpath)
            os.unlink(lpath)

        # Open the output file (384 == 0600)
        lfdesc = os.open(lpath, os.O_RDWR|os.O_CREAT, 384)

    # Fork off a new process
    pid = os.fork()

    if pid > 0:

        # Close unneeded descriptors
        if lfdesc >= 0:
            os.close(lfdesc)
        os.close(fdout)

        # Wait for child process to complete
        status = __waitpid(pid)[1]

        # Read child process response
        try:
            response = os.read(fdin, 8192)
        except OSError:
            response = ''

        # Close communication pipe
        os.close(fdin)

        # Terminated by signal?
        if os.WIFSIGNALED(status):
            syslog.syslog(syslog.LOG_ERR,
                          'Child terminated by signal %d' %
                          os.WTERMSIG(status))
            return None

        # For robustness
        if not os.WIFEXITED(status):
            raise RuntimeError('Internal error in __waitpid()')

        # Failure?
        if os.WEXITSTATUS(status) != 0:
            error = __printable_only(response.replace('ERROR ', '', 1))
            syslog.syslog(syslog.LOG_ERR, 'Child error: %s' % error)
            return None

        # Is output a file?
        if tofile:
            syslog.syslog(syslog.LOG_ERR, 'Response saved to: %s' % lpath)
            return lpath

        #
        # Output inline
        # NOTE The caller is expected to validate the result
        # using regular expression.  Here we use __printable_only
        # for safety.
        #
        result = response.replace('OK ', '', 1)
        syslog.syslog(syslog.LOG_ERR, 'Response is: %s' %
                             __printable_only(result))
        return result

    else:

        #
        # The child code is surrounded by this giant try..except
        # because what is interesting for us is the child process
        # exit status (plus eventually the reason).
        #
        try:

            # Lookup unprivileged user info
            passwd = __lookup_user_info('_neubot_update')

            #
            # Disable chroot for 0.4.2 because it breaks a lot
            # of things such as encodings and DNS lookups and it
            # requires some effort to understand all and take
            # the proper decisions.
            #
            #__chroot_naive('/var/empty')

            # Become unprivileged as soon as possible
            __change_user(passwd)

            # Send HTTP request
            if https:
                connection = __lib_http.HTTPSConnection(address)
            else:
                connection = __lib_http.HTTPConnection(address)
            headers = {'User-Agent': 'Neubot/0.4.12-rc6'}
            connection.request("GET", rpath, None, headers)

            # Recv HTTP response
            response = connection.getresponse()
            if response.status != 200:
                raise RuntimeError('HTTP response: %d' % response.status)

            # Need to write response body to file?
            if tofile:

                assert(lfdesc >= 0)

                total = 0
                while True:

                    # Read a piece of response body
                    data = response.read(262144)
                    if not data:
                        break

                    # Enforce maximum response size
                    total += len(data)
                    if total > maxbytes:
                        raise RuntimeError('Response is too big')

                    # Copy to output descriptor
                    os.write(lfdesc, data)

                # Close I/O channels
                os.close(lfdesc)
                connection.close()

                # Notify parent
                os.write(fdout, 'OK\n')

            else:
                vector = []
                total = 0
                while True:
                    data = response.read(262144)
                    if not data:
                        break
                    vector.append(data)
                    total += len(data)
                    if total > 8192:
                        raise RuntimeError('Response is too big')
                connection.close()
                os.write(fdout, 'OK %s\n' % ''.join(vector))

        except:
            try:
                why = asyncore.compact_traceback()
                os.write(fdout, 'ERROR %s\n' % str(why))
            except:
                pass
            os._exit(1)
        else:
            os._exit(0)

def __download_version_info(address, channel):
    '''
     Download the latest version number.  The version number here
     is in numeric representation, i.e. a floating point number with
     exactly nine digits after the radix point.
    '''
    version = __download(address, "/updates/%s" % channel)
    if not version:
        raise RuntimeError('Download failed')
    version = __printable_only(version)
    match = re.match('^([0-9]+)\.([0-9]{9})$', version)
    if not match:
        raise RuntimeError('Invalid version string: %s' % version)
    else:
        return version

def __download_sha256sum(version, address):
    '''
     Download the SHA256 sum of a tarball.  Note that the tarball
     name again is a version number in numeric representation.  Note
     that the sha256 file contains just one SHA256 entry.
    '''
    sha256 = __download(address, '/updates/%s.tar.gz.sha256' % version)
    if not sha256:
        raise RuntimeError('Download failed')
    line = __printable_only(sha256)
    match = re.match('^([a-fA-F0-9]+)  %s.tar.gz$' % version, line)
    if not match:
        raise RuntimeError('Invalid version sha256: %s' % version)
    else:
        return match.group(1)

def __verify_sig(signature, tarball):

    '''
     Call OpenSSL to verify the signature.  The public key
     is ``VERSIONDIR/pubkey.pem``.  We assume the signature
     algorithm is SHA256.
    '''

    cmdline = ['/usr/bin/openssl', 'dgst', '-sha256',
               '-verify', '%s/pubkey.pem' % VERSIONDIR,
               '-signature', signature, tarball]

    syslog.syslog(syslog.LOG_INFO, 'Cmdline: %s' % str(cmdline))

    retval = subprocess.call(cmdline)

    if retval != 0:
        raise RuntimeError('Signature does not match')

def __download_and_verify_update(server, channel):

    '''
     If an update is available, download the updated tarball
     and verify its sha256sum.  Return the name of the downloaded
     file.
    '''

    syslog.syslog(syslog.LOG_INFO,
                  'Checking for updates (current version: %s)' %
                  VERSION)

    # Get latest version
    nversion = __download_version_info(server, channel)
    if decimal.Decimal(nversion) <= decimal.Decimal(VERSION):
        syslog.syslog(syslog.LOG_INFO, 'No updates available')
        return None

    syslog.syslog(syslog.LOG_INFO,
                  'Update available: %s -> %s' %
                  (VERSION, nversion))

    # Get checksum
    sha256 = __download_sha256sum(nversion, server)
    syslog.syslog(syslog.LOG_INFO, 'Expected sha256sum: %s' % sha256)

    # Get tarball
    tarball = __download(
                         server,
                         '/updates/%s.tar.gz' % nversion,
                         tofile=True
                        )
    if not tarball:
        raise RuntimeError('Download failed')

    # Calculate tarball checksum
    filep = open(tarball, 'rb')
    hashp = hashlib.new('sha256')
    content = filep.read()
    hashp.update(content)
    digest = hashp.hexdigest()
    filep.close()

    syslog.syslog(syslog.LOG_INFO, 'Tarball sha256sum: %s' % digest)

    # Verify checksum
    if digest != sha256:
        raise RuntimeError('SHA256 mismatch')

    # Download signature
    signature = __download(
                           server,
                           '/updates/%s.tar.gz.sig' % nversion,
                           tofile=True
                          )
    if not signature:
        raise RuntimeError('Download failed')

    # Verify signature
    __verify_sig(signature, tarball)

    syslog.syslog(syslog.LOG_INFO, 'Tarball OK')

    return nversion

def _download_and_verify_update(server='releases.neubot.org'):
    '''
     Wrapper around __download_and_verify_update() that catches
     and handles exceptions.
    '''
    try:
        channel = CONFIG['channel']
        return __download_and_verify_update(server, channel)
    except:
        why = asyncore.compact_traceback()
        syslog.syslog(syslog.LOG_ERR,
                      '_download_and_verify_update: %s' %
                      str(why))
        return None

#
# Install new version
#

def __install_new_version(version):
    ''' Install a new version of Neubot '''
    updater_install.install(BASEDIR, version)

def __switch_to_new_version():
    ''' Switch to the a new version of Neubot '''
    os.execv('/bin/sh', ['/bin/sh', '%s/start.sh' % BASEDIR])

def __clear_base_directory():
    ''' Clear base directory and remove old files '''

    #
    # BASEDIR/start.sh chdirs to BASEDIR, still, for robustness,
    # this function uses absolute paths.
    # First, make sure we skip known-good files that are essential
    # for the Neubot distribution.
    # We do not create symbolic links in BASEDIR, so there is no
    # point in considering symbolic links.
    #
    for name in os.listdir(BASEDIR):
        if name in ('org.neubot.plist', 'start.sh'):
            continue
        path = os.sep.join([BASEDIR, name])
        if os.path.islink(path):
            continue

        #
        # If the path is a regular file, check for the two file
        # extensions we create, validate the file name, and unlink
        # the path if the name looks good.
        #
        if os.path.isfile(path):
            if re.match('^([0-9]+)\.([0-9]{9}).tar.gz$', name):
                os.unlink(path)
            elif re.match('^([0-9]+)\.([0-9]{9}).tar.gz.sig$', name):
                os.unlink(path)
            continue

        #
        # Make sure path is a directory, validate the name and make sure
        # the version number IS NOT the current version.  If all these
        # conditions is True, it must be a previous version, and we can
        # recursively thrash the directory.
        # Note that we check if isdir() because we want to be sure the
        # file name is not e.g. a named pipe.  We create directories and
        # we remove directories.
        # Before Python 2.6 there was bug #1669 where rmtree() did not
        # made sure that path was not a symbolic link.  However, here
        # we already know that path is not a symbolic link, so we should
        # be safe even with Python 2.5.  (It goes without saying that
        # the remainder of rmtree() does not follow symlinks.)
        #
        if (os.path.isdir(path) and re.match('^([0-9]+)\.([0-9]{9})$', name)
            and decimal.Decimal(name) != decimal.Decimal(VERSION)):
            shutil.rmtree(path)

#
# Start/stop neubot
#

def __start_neubot_agent():
    ''' Fork a new process and run neubot agent '''

    # Fork a new process
    pid = os.fork()
    if pid > 0:
        syslog.syslog(syslog.LOG_INFO, 'Neubot agent PID: %d' % pid)
        return pid

    #
    # The child code is surrounded by this giant try..except
    # because we don't want the child process to eventually
    # return to the caller.
    #
    try:
        syslog.openlog('neubot', syslog.LOG_PID, syslog.LOG_DAEMON)

        # Add neubot directory to python search path
        if not os.access(VERSIONDIR, os.R_OK|os.X_OK):
            raise RuntimeError('Cannot access: %s' % VERSIONDIR)

        syslog.syslog(syslog.LOG_ERR,
                      'Prepending "%s" to Python search path' %
                      VERSIONDIR)

        sys.path.insert(0, VERSIONDIR)

        # Import the required modules
        from neubot.log import LOG
        from neubot.net.poller import POLLER
        from neubot import agent

        # XXX Redundant?
        # Because we're already in background
        LOG.redirect()

        # Handle SIGTERM gracefully
        sigterm_handler = lambda signo, frame: POLLER.break_loop()
        signal.signal(signal.SIGTERM, sigterm_handler)

        #
        # Here we're running as root but this is OK because
        # neubot/agent.py is going to drop the privileges to
        # the unprivileged user `_neubot`.
        #
        agent.main(['neubot/agent.py',
                    '-D agent.daemonize=OFF',
                    '-D agent.use_syslog=ON'])

    #
    # We must employ os._exit() instead of sys.exit() because
    # the latter is catched below by our catch-all clauses and
    # the child process will start running the parent code.
    # OTOH os._exit() exits immediately.
    #
    except:
        try:
            why = asyncore.compact_traceback()
            syslog.syslog(syslog.LOG_ERR,
                          'Unhandled exception in the Neubot agent: %s' %
                          str(why))
        except:
            pass
        os._exit(1)
    else:
        os._exit(0)

def __stop_neubot_agent(pid):
    ''' Stop a running Neubot agent '''

    # Please, terminate gracefully!
    syslog.syslog(syslog.LOG_INFO, 'Sending SIGTERM to %d' % pid)

    os.kill(pid, signal.SIGTERM)

    # Wait for the process to terminate
    syslog.syslog(syslog.LOG_INFO, 'Waiting for process to terminate')

    _pid, status = __waitpid(pid, 5)

    if _pid == 0 and status == 0:

        # Die die die!
        syslog.syslog(syslog.LOG_WARNING, 'Need to send SIGKILL to %d' % pid)

        os.kill(pid, signal.SIGKILL)

        # Wait for process to die
        __waitpid(pid)

        syslog.syslog(syslog.LOG_INFO, 'Process terminated abruptly')

    else:
        syslog.syslog(syslog.LOG_INFO, 'Process terminated gracefully')

#
# Main
#

def __main():
    ''' Neubot auto-updater process '''

    # Process command line options
    logopt = syslog.LOG_PID
    daemonize = True

    try:
        options, arguments = getopt.getopt(sys.argv[1:], 'Dd')
    except getopt.error:
        sys.exit('Usage: neubot/updater/unix.py [-Dd]')

    if arguments:
        sys.exit('Usage: neubot/updater/unix.py [-Dd]')

    for tpl in options:
        if tpl[0] == '-D':
            daemonize = False
        elif tpl[0] == '-d':
            logopt |= syslog.LOG_PERROR|syslog.LOG_NDELAY

    # We must be run as root
    if os.getuid() != 0 and os.geteuid() != 0:
        sys.exit('You must be root.')

    # Open the system logger
    syslog.openlog('neubot(updater)', logopt, syslog.LOG_DAEMON)

    # Read configuration file
    if os.path.isfile('/etc/neubot/updater'):
        cnf = utils_rc.parse_safe('/etc/neubot/updater')
        CONFIG.update(cnf)

    # Clear root user environment
    __change_user(__lookup_user_info('root'))

    # Daemonize
    if daemonize:
        __go_background('/var/run/neubot.pid')

    #
    # TODO We should install a signal handler that kills
    # properly the child process when requested to exit
    # gracefully.
    #

    lastcheck = time.time()
    firstrun = True
    pid = -1

    #
    # Loop forever, catch and just log all exceptions.
    # Spend many time sleeping and wake up just once every
    # few seconds to make sure everything is fine.
    #
    while True:
        if firstrun:
            firstrun = False
        else:
            time.sleep(15)

        try:

            # If needed start the agent
            if pid == -1:
                syslog.syslog(syslog.LOG_INFO, 'Starting the agent')
                pid = __start_neubot_agent()

            # Check for updates
            now = time.time()
            if now - lastcheck > 1800:
                lastcheck = now
                nversion = _download_and_verify_update()
                if nversion:
                    if pid > 0:
                        __stop_neubot_agent(pid)
                        pid = -1
                    __install_new_version(nversion)
                    __switch_to_new_version()
                    raise RuntimeError('Internal error')

                #
                # We have not found an update, while here make
                # sure that we keep clean our base directory,
                # remove old files and directories, the tarball
                # of this version, etc.
                #
                else:
                    __clear_base_directory()

            # Monitor the agent
            syslog.syslog(syslog.LOG_INFO, 'Monitoring the agent')
            rpid, status = __waitpid(pid, 0)

            if rpid == pid:
                pid = -1

                # Signaled?
                if os.WIFSIGNALED(status):
                    raise RuntimeError('Agent terminated by signal')

                # For robustness
                if not os.WIFEXITED(status):
                    raise RuntimeError('Internal error in __waitpid()')

                syslog.syslog(syslog.LOG_WARNING,
                  'Child exited with status %d' % os.WEXITSTATUS(status))

        except:
            try:
                why = asyncore.compact_traceback()
                syslog.syslog(syslog.LOG_ERR, 'In main loop: %s' % str(why))
            except:
                pass

def main():
    ''' Wrapper around the real __main() '''
    try:
        __main()
    except SystemExit:
        raise
    except:
        try:
            why = asyncore.compact_traceback()
            syslog.syslog(syslog.LOG_ERR, 'Unhandled exception: %s' % str(why))
        except:
            pass
        sys.exit(1)

if __name__ == '__main__':
    main()
