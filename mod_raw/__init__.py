# mod_dash/__init__.py

#
# Copyright (c) 2013
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

""" The RAW TCP test """

from .raw_clnt import RawClient
from .raw_negotiate import RawNegotiate
from .raw_negotiate_srvr import NegotiateServerRaw
from .raw_srvr import RawServer
from .raw_srvr_glue import RawServerEx

def _run_test_provider_client(params, context):
    """ Run RAW TestProvider client """
    handler = RawClient(context["POLLER"], context["STATE"])
    handler.connect((params["address"], params["port"]),
      context["SETTINGS"]["prefer_ipv6"], 0, {})

def _run_test_controller_client(params, context):
    """ Run RAW TestController client """
    handler = RawNegotiate(context["BACKEND"], context["NOTIFIER"],
        context["SETTINGS"], context["POLLER"], context["STATE"])
    handler.connect((params["address"], params["port"]),
      context["SETTINGS"]["prefer_ipv6"], 0, {})

def _run_test_provider_server(params, context):
    """ Run DASH TestProvider server """
    handler = RawServer(context["POLLER"])
    handler.listen((params["address"], params["port"]),
      context["SETTINGS"]["prefer_ipv6"], 0, "")

def _run_test_controller_server(params, context):
    """ Run DASH TestController server """

    controller = NegotiateServerRaw(context["BACKEND"])
    context["NEGOTIATE_SERVER"].register_module("raw", controller)

    handler = RawServerEx(context["POLLER"], controller)
    handler.listen((params["test_provider_address"],
      params["test_provider_port"]), context["SETTINGS"]["prefer_ipv6"], 0, "")

def neubot_plugin_spec():
    """ Returns the plugin spec """
    return {
        "spec_version": 1.0,
        "name": "raw",
        "short_description": "Neubot RAW TCP test",
        "author": "Simone Basso <bassosimone@gmail.com>",
        "version": 1.0,
        "www": {
            "spec_version": 1.0,
            "description": "raw.html",
            "results_producer": "raw.json",
        },
        "backend": {
            "spec_version": 1.0,  # FIXME
        },
        "test_provider": {
            "spec_version": 1.0,
            "client": {
                "run": _run_test_provider_client,
                "params": {
                    "address": str,
                    "port": int,
                },
            },
            "server": {
                "run": _run_test_provider_server,
                "params": {
                    "address": str,
                    "port": int,
                },
            },
        },
        "test_controller": {
            "spec_version": 1.0,
            "client": {
                "run": _run_test_controller_client,
                "params": {
                    "address": str,
                    "port": int,
                },
            },
            "server": {
                "run": _run_test_controller_server,
                "params": {
                    "test_provider_address": str,
                    "test_provider_port": int,
                },
            },
        },
    }
