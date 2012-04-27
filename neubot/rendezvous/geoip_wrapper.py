# neubot/rendezvous/geoip_wrapper.py

#
# Copyright (c) 2010-2011 Simone Basso <bassosimone@gmail.com>,
#  NEXA Center for Internet & Society at Politecnico di Torino
# Copyright (c) 2011 Roberto D'Auria <everlastingfire@autistici.org>
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

''' Wrapper for MaxMind's GeoIP '''

import os.path
import sys
import logging

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.config import CONFIG

from neubot import utils

try:
    import GeoIP as GEOIP
except ImportError:
    GEOIP = None

COUNTRY_DATABASE = "/usr/local/share/GeoIP/GeoIP.dat"

class Geolocator(object):

    ''' Geolocator object '''

    def __init__(self):
        ''' Initialize geolocator object '''
        self.countries = None

    def open_or_die(self):

        ''' Open the database or die '''

        if not GEOIP:
            logging.error("Missing dependency: GeoIP")
            logging.info("Please install GeoIP python wrappers, e.g.")
            logging.info("    sudo apt-get install python-geoip")
            sys.exit(1)

        path = CONFIG.get("rendezvous.geoip_wrapper.country_database",
                          COUNTRY_DATABASE)

        #
        # Detect the common error case, i.e. that the user has
        # not downloaded the database.  If something fancy is
        # going on, let the GeoIP library stacktrace for us.
        #
        if not os.path.exists(path):
            logging.error("Missing GeoLiteCountry database: %s", path)
            logging.info("Please download it from "
                     "<http://www.maxmind.com/app/geolitecountry>.")
            sys.exit(1)

        self.countries = GEOIP.open(path, GEOIP.GEOIP_STANDARD)

    def lookup_country(self, address):
        ''' Lookup for country entry '''
        country = self.countries.country_code_by_addr(address)
        if not country:
            logging.error("Geolocator: %s: not found", address)
            return ""
        return utils.stringify(country)

if __name__ == "__main__":
    GEOLOC = Geolocator()
    GEOLOC.open_or_die()
    print GEOLOC.lookup_country("130.192.91.211")
