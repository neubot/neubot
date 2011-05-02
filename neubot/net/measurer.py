# neubot/net/measurer.py

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

import sys
from neubot.net.poller import POLLER
from neubot import utils


class Measurer(object):
    def __init__(self):
        self.last = utils.ticks()
        self.streams = []
        self.rtts = []

    def register_stream(self, stream):
        self.streams.append(stream)
        stream.measurer = self

    def unregister_stream(self, stream):
        self.streams.remove(stream)
        stream.measurer = None

    def measure_rtt(self):
        rttavg = 0
        rttdetails = []
        if len(self.rtts) > 0:
            for rtt in self.rtts:
                rttavg += rtt
            rttavg = rttavg / len(self.rtts)
            rttdetails = self.rtts
            self.rtts = []
        return rttavg, rttdetails

    def compute_delta_and_sums(self, clear=True):
        now = utils.ticks()
        delta = now - self.last
        self.last = now

        if delta <= 0:
            return 0.0, 0, 0

        recvsum = 0
        sendsum = 0
        for stream in self.streams:
            recvsum += stream.bytes_recv
            sendsum += stream.bytes_sent
            if clear:
                stream.bytes_recv = stream.bytes_sent = 0

        return delta, recvsum, sendsum

    def measure_speed(self):
        delta, recvsum, sendsum = self.compute_delta_and_sums(clear=False)
        if delta <= 0:
            return 0, 0, []

        recvavg = recvsum / delta
        sendavg = sendsum / delta

        percentages = []
        for stream in self.streams:
            recvp, sendp = 0, 0
            if recvsum:
                recvp = 100 * stream.bytes_recv / recvsum
            if sendsum:
                sendp = 100 * stream.bytes_sent / sendsum
            percentages.append((recvp, sendp))
            stream.bytes_recv = stream.bytes_sent = 0

        return recvavg, sendavg, percentages


class HeadlessMeasurer(Measurer):
    def __init__(self, poller, interval=1):
        Measurer.__init__(self)
        self.poller = poller
        self.interval = interval
        self.recv_hist = {}
        self.send_hist = {}
        self.marker = None
        self.task = None

    def start(self, marker):
        self.collect()
        self.marker = marker
        if marker in self.recv_hist:
            del self.recv_hist[marker]
        if marker in self.send_hist:
            del self.send_hist[marker]

    def stop(self):
        if self.task:
            self.task.unsched()

    def collect(self):
        if self.task:
            self.task.unsched()
        self.task = self.poller.sched(self.interval, self.collect)
        delta, recvsum, sendsum = self.compute_delta_and_sums()
        if self.marker:
            self.recv_hist.setdefault(self.marker, []).append((delta, recvsum))
            self.send_hist.setdefault(self.marker, []).append((delta, sendsum))


class VerboseMeasurer(Measurer):
    def __init__(self, poller, output=sys.stdout, interval=1):
        Measurer.__init__(self)

        self.poller = poller
        self.output = output
        self.interval = interval

    def start(self):
        self.poller.sched(self.interval, self.report)
        self.output.write("\t\trtt\t\trecv\t\t\tsend\n")

    def report(self):
        self.poller.sched(self.interval, self.report)

        rttavg, rttdetails = self.measure_rtt()
        if len(rttdetails) > 0:
            rttavg = "%d us" % int(1000000 * rttavg)
            self.output.write("\t\t%s\t\t---\t\t---\n" % rttavg)
            if len(rttdetails) > 1:
                for detail in rttdetails:
                    detail = "%d us" % int(1000000 * detail)
                    self.output.write("\t\t  %s\t\t---\t\t---\n" % detail)

        recvavg, sendavg, percentages = self.measure_speed()
        if len(percentages) > 0:
            recv, send = (utils.speed_formatter(recvavg),
                          utils.speed_formatter(sendavg))
            self.output.write("\t\t---\t\t%s\t\t%s\n" % (recv, send))
            if len(percentages) > 1:
                for val in percentages:
                    val = map(lambda x: "%.2f%%" % x, val)
                    self.output.write("\t\t---\t\t  %s\t\t  %s\n" %
                                      (val[0], val[1]))


MEASURER = VerboseMeasurer(POLLER)
