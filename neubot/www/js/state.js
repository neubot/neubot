/* neubot/www/state.js */
/*
 * Copyright (c) 2011 Alessio Palmero Aprosio <alessio@apnetwork.it>,
 *  Università degli Studi di Milano
 * Copyright (c) 2010 Simone Basso <bassosimone@gmail.com>,
 *  NEXA Center for Internet & Society at Politecnico di Torino
 *
 * This file is part of Neubot <http://www.neubot.org/>.
 *
 * Neubot is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Neubot is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Neubot.  If not, see <http://www.gnu.org/licenses/>.
 */

var state = (function() {
    var self = {};

    self.tracker = function(callback) {
        var my = {};
        var curtime = 0;
        var next_rendezvous = 0;

        // In case of error keep trying because it might just
        // be that the user is restarting neubot, but also add
        // a significant delay to let the browser breathe

        function get_state_error() {
            setTimeout(get_state, 5000);
        }

        function get_state_success(data) {
            if (!data.events) {
                data.events = {};
            }

            if (data.events.next_rendezvous) {
                next_rendezvous = data.events.next_rendezvous;
            }
            else {
                data.events.next_rendezvous = next_rendezvous;
            }

            if (data.t) {
                var t = data.t;
                if (curtime == undefined) {
                    setTimeout(get_state, 5000);
                    return;
                }
                curtime = t;
            }
            callback(data);
            setTimeout(get_state, 0);
        }

        function get_state() {
            var params = {
                url: "/api/state?t=" + curtime,
                error: get_state_error,
                success: get_state_success,
                dataType: "json"
            };
            jQuery.ajax(params);
        }

        // Google Chrome tab icon will keep spinning unless we
        // delay the first get_state a bit

        my.start = function() {
            setTimeout(get_state, 100);
        }

        return my;
    }

    return self;
})();
