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

'''
 This is the privilege separated Neubot updater daemon.  It is
 started as a system daemon, runs as root, spawns and monitors an
 unprivileged child Neubot process and periodically checks for
 updates.  The check is not performed by the privileged daemon
 itself but by a child process that runs on behalf of the
 unprivileged user ``_neubot_update``.
'''

#
# Like neubot/main/__init__.py this file is a Neubot entry point
# and so we must keep its name constant over time.
# This file contains too much code, but we're gradually moving
# such code into smaller files.
#

import asyncore
import getopt
import errno
import syslog
import signal
import hashlib
import re
import os.path
import sys
import time
import fcntl
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
from neubot import utils_posix
from neubot import utils_version

# Note: BASEDIR/VERSIONDIR/neubot/updater/unix.py
VERSIONDIR = os.path.dirname(os.path.dirname(os.path.dirname(
                                 os.path.abspath(__file__))))
BASEDIR = os.path.dirname(VERSIONDIR)

# Version number in numeric representation
VERSION = utils_version.NUMERIC_VERSION

# Configuration
CONFIG = {
    'channel': 'latest',
    'update_user': '_neubot_update',
}

# State
STATE = {
    #
    # TODO By setting 'lastcheck' to the current time, we
    # delay the first check for updates of 30 minutes.
    # I'm not sure this is a great idea, because, ideally,
    # Neubot should update and then run tests, not the
    # other way round.
    #
    'lastcheck': time.time(),
}

#
# Common
#

def __exit(code):
    ''' Invoke exit(2) '''
    os._exit(code)

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
            passwd = utils_posix.getpwnam(CONFIG['update_user'])

            # Become unprivileged as soon as possible
            utils_posix.chuser(passwd)

            if os.getuid() == 0 or os.geteuid() == 0:
                raise RuntimeError('Has not dropped privileges')

            # Close all unneeded file descriptors
            for tmpdesc in range(64):
                if tmpdesc == lfdesc or tmpdesc == fdout:
                    continue
                try:
                    os.close(tmpdesc)
                except OSError:
                    pass
                except:
                    pass
            # Ensure stdio point to something
            for _ in range(3):
                os.open('/dev/null', os.O_RDWR)

            # Send HTTP request
            if https:
                connection = __lib_http.HTTPSConnection(address)
            else:
                connection = __lib_http.HTTPConnection(address)
            headers = {'User-Agent': utils_version.HTTP_HEADER}
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
            __exit(1)
        else:
            __exit(0)

def __download_version_info(address, channel):
    '''
     Download the latest version number.  The version number here
     is in numeric representation, i.e. a floating point number with
     exactly nine digits after the radix point.
    '''
    version = __download(address, "/updates/macos/%s" % channel)
    if not version:
        raise RuntimeError('Download failed')
    version = __printable_only(version)
    match = re.match(r'^([0-9]+)\.([0-9]{9})$', version)
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
    sha256 = __download(address, '/updates/macos/%s.tar.gz.sha256' % version)
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
                         '/updates/macos/%s.tar.gz' % nversion,
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
                           '/updates/macos/%s.tar.gz.sig' % nversion,
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
            if re.match(r'^([0-9]+)\.([0-9]{9}).tar.gz$', name):
                os.unlink(path)
            elif re.match(r'^([0-9]+)\.([0-9]{9}).tar.gz.sig$', name):
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
        if (os.path.isdir(path) and re.match(r'^([0-9]+)\.([0-9]{9})$', name)
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

        if not VERSIONDIR in sys.path:
            syslog.syslog(syslog.LOG_ERR,
                          'Prepending "%s" to Python search path' %
                          VERSIONDIR)
            sys.path.insert(0, VERSIONDIR)

        # Import the required modules
        from neubot.log import LOG
        from neubot.net.poller import POLLER
        from neubot import agent

        #
        # Redirect logger to syslog now, so early errors in
        # agent.py:main() are logged.
        #
        LOG.redirect()

        #
        # Close all unneeded file descriptors, but save stdio,
        # which has just been redirected.
        #
        for tmpdesc in range(3, 64):
            try:
                os.close(tmpdesc)
            except OSError:
                pass
            except:
                pass

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
    # We must employ __exit() instead of sys.exit() because
    # the latter is catched below by our catch-all clauses and
    # the child process will start running the parent code.
    # OTOH __exit() exits immediately.
    #
    except:
        try:
            why = asyncore.compact_traceback()
            syslog.syslog(syslog.LOG_ERR,
                          'Unhandled exception in the Neubot agent: %s' %
                          str(why))
        except:
            pass
        __exit(1)
    else:
        __exit(0)

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

def __sigusr1_handler(*args):
    ''' Handler for USR1 signal '''
    if args[0] != signal.SIGUSR1:
        raise RuntimeError('Invoked for the wrong signal')
    STATE['lastcheck'] = 0

def __main():
    ''' Neubot auto-updater process '''

    # Process command line options
    logopt = syslog.LOG_PID
    daemonize = True

    try:
        options, arguments = getopt.getopt(sys.argv[1:], 'adv')
    except getopt.error:
        sys.exit('Usage: neubot/updater/unix.py [-adv]')

    if arguments:
        sys.exit('Usage: neubot/updater/unix.py [-adv]')

    check_for_updates = 0  # By default we don't check for updates
    for tpl in options:
        if tpl[0] == '-a':
            check_for_updates = 1
        elif tpl[0] == '-d':
            daemonize = False
        elif tpl[0] == '-v':
            logopt |= syslog.LOG_PERROR|syslog.LOG_NDELAY

    # We must be run as root
    if os.getuid() != 0 and os.geteuid() != 0:
        sys.exit('FATAL: You must be root.')

    # Open the system logger
    syslog.openlog('neubot(updater)', logopt, syslog.LOG_DAEMON)

    # Clear root user environment
    utils_posix.chuser(utils_posix.getpwnam('root'))

    # Daemonize
    if daemonize:
        utils_posix.daemonize('/var/run/neubot.pid')

    #
    # TODO We should install a signal handler that kills
    # properly the child process when requested to exit
    # gracefully.
    #

    firstrun = True
    pid = -1

    signal.signal(signal.SIGUSR1, __sigusr1_handler)

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

        # Read configuration files
        CONFIG.update(utils_rc.parse_safe('/etc/neubot/updater'))
        CONFIG.update(utils_rc.parse_safe('/etc/neubot/users'))

        try:

            # If needed start the agent
            if pid == -1:
                syslog.syslog(syslog.LOG_INFO, 'Starting the agent')
                pid = __start_neubot_agent()

            # Check for updates
            now = time.time()
            updates_check_in = 1800 - (now - STATE['lastcheck'])
            if updates_check_in <= 0:
                STATE['lastcheck'] = now

                if check_for_updates:
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
                else:
                    syslog.syslog(syslog.LOG_DEBUG, 'Auto-updates are disabled')

            elif check_for_updates:
                syslog.syslog(syslog.LOG_DEBUG,
                  'Auto-updates check in %d sec' % updates_check_in)

            # Monitor the agent
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
