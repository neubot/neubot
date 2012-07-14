# neubot/resmon_linux.py

#
# Copyright (c) 2011 Simone Basso <bassosimone@gmail.com>,
#  NEXA Center for Internet & Society at Politecnico di Torino
# Copyright (c) individual contributors
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

# Monitor resources with Linux (this file is currently unused)

import os.path


class _SysInfo(object):

    def get_load_avg(self):

        """Get load averages as returned by uptime(1)."""

        vector = []

        fp = open("/proc/loadavg", "rb")
        octets = fp.read()
        vector = octets.split()[0:3]

        return vector

    def get_meminfo(self):

        """Get the amount of free and total memory."""

        # Note: As of 2.6.38 the kernel prints out values in kB,
        # see fs/proc/meminfo.c for more information.

        dictionary = {}

        fp = open("/proc/meminfo", "rb")
        total, free = -1, -1
        for line in fp:
            if line.startswith("MemTotal:"):
                total = int(line.replace("MemTotal:", "").split()[0])
            elif line.startswith("MemFree:"):
                free = int(line.replace("MemFree:", "").split()[0])
        if total >= 0 and free >= 0:
            dictionary = {"free": free, "total": total}

        return dictionary

    def get_netlist(self):

        """Get the list of network interfaces."""

        #
        # Adapted from libgtop sysdeps/linux/netlist.c
        # Copyright (c) 1998-99 Martin Baulig
        # Released under version 2 of the GNU GPL
        #

        vector = []

        fp = open("/proc/net/dev", "rb")
        for line in fp:
            if ":" in line:
                vector.append(line.split(":")[0].strip())

        return vector

    def get_netload(self, dev):

        """Get the load of a network interface."""

        #
        # Adapted from libgtop sysdeps/linux/netload.c
        # Copyright (c) 1998-99 Martin Baulig
        # Released under version 2 of the GNU GPL
        #

        dictionary = {}

        fp = open("/sys/class/net/%s/statistics/rx_bytes" % dev)
        rx_bytes = long(fp.read().strip())
        dictionary["rx_bytes"] = rx_bytes

        fp = open("/sys/class/net/%s/statistics/tx_bytes" % dev)
        tx_bytes = long(fp.read().strip())
        dictionary["tx_bytes"] = tx_bytes

        return dictionary

    def get_procnames(self):

        """Get the names of running processes."""

        #
        # Adapted from libgtop sysdeps/linux/proclist.c
        # Copyright (c) 1998-99 Martin Baulig
        # Released under version 2 of the GNU GPL
        #

        result = set()

        for entry in os.listdir("/proc/"):
            if not os.path.isdir("/proc/" + entry):
                continue
            try:
                pid = int(entry)
            except ValueError:
                continue
            fp = open("/proc/%d/stat" % pid, "rb")
            result.add(fp.read().split()[1][1:-1])

        return sorted(result)

    def get_defaultgw(self):

        """Get the name of the default gateway."""

        fp = open("/proc/net/route", "rb")
        for line in fp:
            iface, dest = line.split()[0:2]
            try:
                gateway = int(dest, 16)
            except ValueError:
                continue
            if gateway == 0:
                return iface

        return None


if __name__ == "__main__":
    sysinfo = _SysInfo()

    print "System load avg :", sysinfo.get_load_avg()
    print "Free/total mem  :", sysinfo.get_meminfo()
    print "Net Interfaces  :", sysinfo.get_netlist()
    print "Net Default GW  :", sysinfo.get_defaultgw()

    for dev in sysinfo.get_netlist():
        print "%16s:" % dev, sysinfo.get_netload(dev)

    print "Proc names      :", sysinfo.get_procnames()
