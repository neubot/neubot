/* neubot/www/js/speedtest.js */
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

var speedtest = (function() {
	var self = {};

    self.result_fields = ["timestamp", "internalAddress", "realAddress",
     "remoteAddress", "connectTime", "latency", "downloadSpeed", "uploadSpeed"];

    self.result_titles = ["Timestamp", "Internal Address", "Real Address",
     "Remote Address", "Connect Time", "Latency", "Download Speed",
     "Upload Speed"];

    // walk through results

    self.get_recent_results = function(callbacks) {
        var one_day_in_ms = 24 * 60 * 60 * 1000;
        var since = utils.getNow() - one_day_in_ms;
        return self.get_results(callbacks, since);
    }

    self.get_results = function(callbacks, since, unit, until) {
        var res = new Array();
        if (!since) {
            since = 0;
        }
        since_s = Math.ceil(since / 1000);
        var url = "/api/speedtest?since=" + since_s;
        if (until != undefined) {
            until_s = Math.ceil(until / 1000);
            url += "&until=" + until_s;
        }
        var params = {
            url: url,
            success: function(data) {
                for (var i = 0; i < callbacks.length; i++) {
                    res[i] = callbacks[i](data, since, unit, until);
                }
            },
            dataType: "json"
        };
        jQuery.ajax(params);
    }

    // results formatter

    self.results_formatter_table = function(data, since, unit, until) {
        var i;
        var html = "";

        html += '<center><table id="speedtest">';
        html += "<thead><tr>";
        for (i = 0; i < self.result_fields.length; i++) {
            html += '<th>' + self.result_titles[i] + '</th>';
        }
        html += "</tr></thead>";
        html += "<tbody>";

        // XXX Make sure we match self.result_titles' order (above)
        for (i = 0; i < data.length; i++) {
            var result = data[i];
            html += "<tr>";
            html += "<td>" + utils.getTimeFromSeconds(result["timestamp"], true) + "</td>";
            html += "<td>" + result["internal_address"] + "</td>";
            html += "<td>" + result["real_address"] + "</td>";
            html += "<td>" + result["remote_address"] + "</td>";
            html += "<td>" + utils.toMs(result["connect_time"]) + "</td>";
            html += "<td>" + utils.toMs(result["latency"]) + "</td>";
            html += "<td>" + utils.toMbitsPerSecond(result["download_speed"]) + "</td>";
            html += "<td>" + utils.toMbitsPerSecond(result["upload_speed"]) + "</td>";
            html += "</tr>";
        }

        html += "</tbody></table></center>";

        jQuery("#results").html(html);
        return html;
    };

    self.results_formatter_plot = function(data, since, unit, until) {
        var ipCounter = {};
        var ipCounterN = 0;
        var downloadData = [];
        var uploadData = [];
        var downloadLabels = [];
        var uploadLabels = [];

        var curtime = Math.ceil(utils.getNow() / 1000);

        for (i = 0; i < data.length; i++) {
            var result = data[i];
            var address = result["real_address"];
            var timestamp = result["timestamp"];
            var download = result["download_speed"];
            var upload = result["upload_speed"];

            // Update IP counter
            if (ipCounter[address] == undefined) {      // XXX
                ipCounter[address] = ipCounterN;
                downloadData[ipCounterN] = [];
                uploadData[ipCounterN] = [];
                downloadLabels[ipCounterN] = {
                  label: "DOWN " + address,
                  markerOptions: {
                    style: 'square'
                  },
                  neighborThreshold: -1
                };
                uploadLabels[ipCounterN] = {
                  label: "UP " + address,
                  markerOptions: {
                    style: 'circle'
                  },
                  neighborThreshold: -1
                };
                ipCounterN++;
            }

            // How many hours in the past?
            var timediff = (timestamp - curtime) / 3600;

            // XXX must convert to Number or it does not plot
            counter = ipCounter[address];
            download = Number(utils.toMbitsPerSecondNumber(download));
            upload = Number(utils.toMbitsPerSecondNumber(upload));
            downloadData[counter].push([timediff, download]);
            uploadData[counter].push([timediff, upload]);
        }

        var min = Math.ceil((since - utils.getNow()) / (60 * 60 * 1000));

        // TODO We should use a larger font for axis labels

        mydata = downloadData.concat(uploadData);
        var plot = jQuery.jqplot("chartdiv1", mydata, {
          title: {
            text: "Download and upload rate"
          },
          axes: {
            xaxis: {
              label: "Hours ago",
              min: min,
              max: 0,
              showTickMarks: true
            },
            yaxis: {
              label: "Mbit/s",
              min: 0
            }
          },
          legend: {
            show: true,
            location: "e"
          },
          cursor: {
            showVerticalLine: false,
            showHorizontalLine: true,
            showCursorLegend: false,
            showTooltip: false,
            tooltipLocation: 'sw',
            zoom: true
          },
          highlighter: {
            show: false
          },
          series: downloadLabels.concat(uploadLabels)
        });

        plot.replot();

        // some additional CSS-magic
        jQuery('.jqplot-table-legend').css('top', '200');
    };

    return self;
})();

// Duplicated code. To be merged in some way with neubot.js.
function process_state(data) {
    var value;

    var actions = ['idle', 'rendezvous', 'negotiate', 'test', 'collect'];

    jQuery('#testResultsBox h4').text("Latest test details");
    jQuery('#next_rendezvous').text("");
    jQuery("#queueInfo").text("");

    if (data.update_version) {
        jQuery("#updateUrl").attr("href", data.update_uri);
        jQuery("#updateUrl").text(data.update_uri);
        jQuery("#updateVersion").text(data.update_version);
        setTimeout(function() { jQuery('#update').slideDown("slow"); }, 5000);
    }

    if (data.events.test_name) {
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

    if (in_array(data.current, actions)) {
        if (data.current == "test") {
            jQuery('#testResultsBox').qtip("show");
        }
        else {
            jQuery('#testResultsBox').qtip("hide");
        }
    }
}

jQuery(document).ready(function() {
    speedtest.get_recent_results([speedtest.results_formatter_table,
                                  speedtest.results_formatter_plot]);

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

    var confirm = function() {
        var n = Number(jQuery("#res_value").val());
        if (n == NaN) {
            alert("Please insert a valid number");
            return false;
        }
        var since = 0;
        switch (jQuery("#res_unit").val()) {
        case "d":
            var one_day_in_ms = 24 * 60 * 60 * 1000;
            since = utils.getNow() - one_day_in_ms * n;
            break;

        case "h":
            var one_hour_in_ms = 60 * 60 * 1000;
            since = utils.getNow() - one_hour_in_ms * n;
            break;
        }
        speedtest.get_results([speedtest.results_formatter_table,
                               speedtest.results_formatter_plot], since);
        return false;
    };

    jQuery("#res_value").keydown(function(event) {
        if (event.keyCode == 13) {
            return confirm();
        }
    });
    jQuery("#res_submit").click(confirm);

    tracker = state.tracker(process_state);
    tracker.start();
});
