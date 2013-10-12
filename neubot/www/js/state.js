/* neubot/www/state.js */
/*
 * Copyright (c) 2011 Alessio Palmero Aprosio <alessio@apnetwork.it>,
 *  Universita` degli Studi di Milano
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

//
// This file contains the code that tracks the state of the Neubot
// daemon and updates current test information in the right sidebar
// of the web user interface.
//
// Further processing is possible by passing the tracker() method
// a callback function.
//

var state = (function() {
    var state_ctx = {};

    state_ctx.actions = ['idle', 'rendezvous', 'negotiate', 'test', 'collect'];

    state_ctx.tracker = function(callback) {
        var tracker_ctx = {};
        var curtime = 0;
        var next_rendezvous = 0;

        //
        // In case of error keep trying because it might just
        // be that the user is restarting neubot, but also add
        // a significant delay to let the browser breathe.
        //
        function get_state_error() {
            setTimeout(get_state, 5000);
        }

        // Update the right sidebar using current state
        function update_sidebar(data) {

            // Update the state of automatic tests
            if (data.events.config) {
                if (data.events.config.enabled != undefined) {
                    utils.setStatusLabels(data.events.config);
                }
            }

            //
            // Honor information on available updates.
            //
            // Note that we DON'T trust URI information sent
            // by the server, since it's not signed (yes,
            // today I'm "paranoid mode ON").
            //
            if (data.events.update && data.events.update.version) {
                jQuery("#updateVersion").text(data.events.update.version);

                // Show update information nicely
                setTimeout(function() {
                    jQuery('#update').slideDown("slow");
                }, 500);
            }

            //
            // This updates latest/current test results in the
            // right sidebar.
            //
            if (data.events.test_name) {
                jQuery("#testNameSideBar").text(data.events.test_name);
            }
            if (data.events.test_latency) {
                jQuery("#latencyResult").text(data.events.test_latency);
            }
            if (data.events.test_download) {
                jQuery("#downloadResult").text(data.events.test_download);
            }
            if (data.events.test_upload) {
                jQuery("#uploadResult").text(data.events.test_upload);
            }
            if (data.events.test_progress) {
                jQuery("#testProgress").text(data.events.test_progress);
            }

            // Filter out interesting actions only
            if (in_array(data.current, state.actions)) {

                // Do we need to show or hide the qtip?
                if (data.current == "test") {
                    jQuery('#testResultsBox').qtip("show");
                    jQuery('#testResultsBox h4').text(
                      i18n.get("Current test results"));
                }
                else {
                    jQuery('#testResultsBox').qtip("hide");
                    jQuery('#testResultsBox h4').text(
                      i18n.get("Latest test results"));
                }

                //
                // Highlight the current state in the
                // index.html web page.
                //
                jQuery('table#state tr').css('background-color',
                  'transparent');
                jQuery('table#state tr#' + data.current).css(
                  'background-color', '#ffc');
            }
        }

        //
        // Invoked when GET /api/state?t=T succeeds.
        // This function performs some more checks than needed
        // on the incoming data, for extra robustness.
        //
        function get_state_success(data) {

            // Always provide a nonempty events dictionary
            if (!data.events) {
                data.events = {};
            }

            // Always provide next rendezvous information
            if (data.events.next_rendezvous) {
                next_rendezvous = data.events.next_rendezvous;
            }
            else {
                data.events.next_rendezvous = next_rendezvous;
            }

            // Update time of latest event
            if (data.t) {
                curtime = data.t;
            }

            //
            // Update the sidebar and, if a callback was provided,
            // pass it the state for further processing.
            //
            update_sidebar(data);
            if (callback != undefined) {
                callback(data);
            }

            //
            // Use comet and send out immediately another request
            //
            setTimeout(get_state, 0);
        }

        //
        // Request the current state of the Neubot daemon and pass
        // along the time of the latest change.
        // If there are no changes since the latest change the daemon
        // will delay the response until either something changes or
        // a timeout expires.
        //
        function get_state() {
            var params = {
                url: "/api/state?t=" + curtime,
                error: get_state_error,
                success: get_state_success,
                dataType: "json"
            };
            jQuery.ajax(params);
        }

        tracker_ctx.start = function() {

            //
            // Create a qtip that will be shown when a test
            // is in progress.
            //
            jQuery('#testResultsBox').qtip({
                content: i18n.get("Test running"),
                position: {
                    target: jQuery('#testTime'),
                    corner: {
                        tooltip: "rightMiddle",
                        target: "leftMiddle"
                    }
                },
                show: {
                    when: false,
                    ready: false
                },
                hide: false,
                style: {
                    border: {
                        width: 2,
                        radius: 5
                    },
                    padding: 10,
                    textAlign: 'center',
                    tip: true,
                    name: 'blue'
                }
            });

            //
            // Fetch information on whether automatic tests are
            // enabled and update the user interface accordingly.
            //
            utils.getConfigVars(utils.setStatusLabels);

            //
            // Google Chrome tab icon will keep spinning unless we
            // delay the first get_state() a bit.
            //
            setTimeout(get_state, 100);
        }

        return tracker_ctx;
    }

    return state_ctx;
})();
