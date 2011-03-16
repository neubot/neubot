/* neubot/www/js/neubot.js */
/*-
 * Copyright (c) 2010 Antonio Servetti <antonio.servetti@polito.it>,
 *  Politecnico di Torino
 *
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

/*
 * For results.html we have js/results.js, therefore it might
 * make sense to rename this file js/index.js for consistency.
 * OTOH js/index.js seems odd to me.
 */

function process_state(data) {

    var actions = ['idle', 'rendezvous', 'negotiate', 'test', 'collect'];
    var now = utils.getNow();
    var value;

    // Reset style

    jQuery('#testResultsBox h4').text("Latest test details");

    // Keep processing simple to read and understand:
    // consider each relevant event on its own and delay
    // the show / hide decisions

    if (data.events.config) {
        if (data.events.config.enabled != undefined) {
            setStatusLabels(data.events.config.enabled);
        }
    }

    if (data.events.pid) {
        jQuery("#pid").text(data.events.pid);
    }

    if (data.events.next_rendezvous) {
        value = utils.getTimeFromSeconds(data.events.next_rendezvous);
        // The sysadmin might have adjusted the clock
        if (value && value > now) {
            jQuery("#next_rendezvous").text(utils.formatMinutes(value - now));
        }
    }

    if (data.events.since) {
        value = utils.getTimeFromSeconds(data.events.since, true);
        if (value) {
            jQuery("#since").text(value);
        }
    }

    if (data.update_version) {
        jQuery("#updateUrl").attr("href", data.update_uri);
        jQuery("#updateUrl").text(data.update_uri);
        jQuery("#updateVersion").text(data.update_version);
        setTimeout(function() { jQuery('#update').slideDown("slow"); }, 500);
    }

    if (data.events.negotiate) {
        if (data.events.negotiate.queue_pos) {
            jQuery("#queuePos").text(data.events.negotiate.queue_pos);
        }
        else {
            jQuery("#queuePos").text(0);
        }

        // Maybe it is not so useful
        // I agree -- Simone
        if (data.events.negotiate.queue_len) {
            jQuery("#queueLen").text(data.events.negotiate.queue_len);
        }
        else {
            jQuery("#queueLen").text(0);
        }
    }

    if (data.events.test_name) {
        // XXX XXX XXX This is sooo ugly!
        jQuery("#testName").text(data.events.test_name);
        jQuery("#testName1").text(data.events.test_name);
    }
    if (data.events.speedtest_latency) {
        jQuery("#latencyResult").text(data.events.speedtest_latency.value);
    }
    if (data.events.speedtest_download) {
        jQuery("#downloadResult").text(data.events.speedtest_download.value);
    }
    if (data.events.speedtest_upload) {
        jQuery("#uploadResult").text(data.events.speedtest_upload.value);
    }

    // Update the results plot after a test
    // Note this is untested code

    // Not yet
    /*
    if (in_array(data.current, actions) && data.current == "collect")
        neubot.update_results_plot();
    */

    // Adjust style
    // The qtip must be visible while we are testing
    // and must not be visible otherwise

    // data.current should always be in_array() but I am leaving the
    // check in-place for robustness and simmetry with state.py

    if (in_array(data.current, actions)) {
        if (data.current == "negotiate") {
            jQuery("#latencyResult").text("---");
            jQuery("#downloadResult").text("---");
            jQuery("#uploadResult").text("---");
        }
        if (data.current == "test") {
            jQuery('#testResultsBox').qtip("show");
        }
        else {
            jQuery('#testResultsBox').qtip("hide");
        }
        jQuery('table#state tr').css('background-color', 'transparent');
        jQuery('table#state tr#' + data.current).css('background-color', '#ffc');
    }
}

jQuery(document).ready(function() {
    jQuery.jqplot.config.enablePlugins = true;

    getSetConfigVar("enabled", setStatusLabels, false);

    jQuery('#testResultsBox').qtip({
        content: "A new test is running.",
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

    // Not yet
    /*
    neubot.update_results_plot(500);
    */

    tracker = state.tracker(process_state);
    tracker.start();
});
