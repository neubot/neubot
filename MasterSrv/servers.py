#!/usr/bin/env python

#
# Copyright (c) 2011-2013
#     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#     and Simone Basso <bassosimone@gmail.com>
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

''' Write the approxymate location of all nodes in a slice 
    to MasterSrv/servers.dat '''

import ConfigParser
import json
import logging
import os
import shlex
import sys
import xmlrpclib

def __load_airports():
    ''' Load and patch airports information '''

    airports_new = {}

    filep = open('MasterSrv/airports.json', 'rb')
    airports_orig = json.load(filep)
    filep.close()

    for airport in airports_orig:
        code = airport['code'].lower()
        location = airport['location'].lower()
        airports_new[code] = location

    return airports_new

def __load_airports_cache():
    ''' Load already mapped airports information '''

    cache = {}

    filep = open('MasterSrv/airports_cache.dat', 'rb')
    for line in filep:
        line = shlex.split(line)
        if not line:
            continue
        cache[line[0]] = ( line[1], line[2] )
    filep.close()

    return cache

def serversmain():
    ''' Write the approxymate location of all nodes in a slice '''

    config = ConfigParser.RawConfigParser()
    config.read(os.sep.join([os.environ['HOME'], '.planet-lab']))

    auth_info = {
        'AuthMethod': 'password',
        'Username': config.get('planet-lab', 'user'),
        'AuthString': config.get('planet-lab', 'password'),
        'Role': 'user'
    }

    proxy = xmlrpclib.ServerProxy('https://www.planet-lab.org/PLCAPI/')

    ids = proxy.GetSlices(auth_info, config.get('planet-lab', 'slice'),
                          ['node_ids'])[0]['node_ids']

    hostnames = [
        entry['hostname'] for entry in
            proxy.GetNodes(auth_info, ids, ['hostname'])
    ]

    airports = __load_airports()
    cache = __load_airports_cache()

    filep = open('MasterSrv/servers.dat', 'wb')
    for hostname in sorted(hostnames):
        # E.g. mlab1.atl01.measurement-lab.org
        vector = hostname.split('.')
        code = vector[1][:3]
        location = airports[code]
        if not location in cache:
            sys.exit('FATAL: Not in cache: %s' % location)
        continent, country = cache[location]
        filep.write('%s %s %s\n' % (hostname, country, continent))
    filep.close()

def main():
    ''' Wrapper for the real main '''
    try:
        serversmain()
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        logging.error('unhandled exception', exc_info=1)
        sys.exit(1)

if __name__ == '__main__':
    main()
