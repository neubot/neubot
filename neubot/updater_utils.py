# neubot/updater_utils.py

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

''' Utils for the updater '''

# Adapted from neubot/updater/unix.py

import decimal
import hashlib
import re

from neubot import utils_path
from neubot import utils_version

VERSION = utils_version.NUMERIC_VERSION

def versioninfo_extract(content):
    ''' Extract version info '''
    regexp = '^([0-9]+\.[0-9]{9})$'
    content = content.strip()
    match = re.match(regexp, content)
    if not match:
        return None
    return match.group(1)

def versioninfo_is_newer(vinfo):
    ''' Is vinfo newer than current version? '''
    return decimal.Decimal(vinfo) > decimal.Decimal(VERSION)

def versioninfo_get_uri(system, channel):
    ''' Return URI for versioninfo '''
    return 'http://releases.neubot.org/updates/%s/%s' % (system, channel)

def sha256sum_extract(vinfo, content):
    ''' Extract sha256sum '''
    regexp = '^([a-fA-F0-9]{64})  %s.tar.gz$' % vinfo
    content = content.strip()
    match = re.match(regexp, content)
    if not match:
        return None
    return match.group(1)

def sha256sum_verify(sha256, content):
    ''' Verify tarball sha256sum '''

    hashp = hashlib.new('sha256')
    hashp.update(content)
    digest = hashp.hexdigest()
    return digest == sha256

def sha256sum_get_uri(system, vinfo):
    ''' Return URI for sha256sum '''
    return 'http://releases.neubot.org/updates/%s/%s.tar.gz.sha256' % (
             system, vinfo)

def tarball_path(basedir, vinfo):
    ''' Return tarball path '''
    name = '.'.join([vinfo, 'tar', 'gz'])
    path = utils_path.append(basedir, name, False)
    if not path:
        raise RuntimeError("updater_utils: append() path failed")
    return path

def tarball_save(basedir, vinfo, tarball):
    ''' Save tarball on filesystem '''
    path = tarball_path(basedir, vinfo)
    filep = open(path, 'wb')
    filep.write(tarball)
    filep.close()

def tarball_get_uri(system, vinfo):
    ''' Return URI for tarball '''
    return 'http://releases.neubot.org/updates/%s/%s.tar.gz' % (
             system, vinfo)

def signature_path(basedir, vinfo):
    ''' Return signature path '''
    name = '.'.join([vinfo, 'tar', 'gz', 'sig'])
    path = utils_path.append(basedir, name, False)
    if not path:
        raise RuntimeError("updater_utils: append() path failed")
    return path

def signature_save(basedir, vinfo, signature):
    ''' Save signature on filesystem '''
    path = signature_path(basedir, vinfo)
    filep = open(path, 'wb')
    filep.write(signature)
    filep.close()

def signature_get_uri(system, vinfo):
    ''' Return URI for signature '''
    return 'http://releases.neubot.org/updates/%s/%s.tar.gz.sig' % (
             system, vinfo)
