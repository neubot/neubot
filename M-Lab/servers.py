#!/usr/bin/env python

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

''' Write the approxymate location of all nodes in a slice '''

#
# This file is used to compile M-Lab/servers.dat.
#
# We cannot use the Internet address associated with a node,
# because we need to address of the sliver, not the address
# of the node.  Indeed, the Neubot server is listening on the
# sliver and not on the node.  The task of getting the address
# of a sliver is performed by another script.
#

import ConfigParser
import GeoIP
import asyncore
import os
import socket
import sys
import xmlrpclib

GEOIP_DATABASE = '/usr/local/share/GeoIP/GeoIP.dat'

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

    filep = open('M-Lab/servers.dat', 'wb')
    geoip = GeoIP.open(GEOIP_DATABASE, GeoIP.GEOIP_STANDARD)
    for hostname in hostnames:
        address = socket.getaddrinfo(hostname, 80, socket.AF_INET)[0][4][0]
        country = geoip.country_code_by_addr(address)
        continent = GeoIP.country_continents[country]
        filep.write('%s %s %s\n' % (hostname, country, continent))
    filep.close()

def main():
    ''' Wrapper for the real main '''
    try:
        serversmain()
    except:
        sys.stderr.write('%s\n' % str(asyncore.compact_traceback()))
        sys.exit(1)

if __name__ == '__main__':
    main()
