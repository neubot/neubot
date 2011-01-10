/* neubot/www/libneubot.js */
/*
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

var neubot = (function() {
    var self = {};

    // get results

    self.get_recent_results = function(callback, delay) {
        var now = self.unix_time();
        var one_day_in_seconds = 86400;
        var since = now - one_day_in_seconds;
        self.get_results(callback, since, delay);
    }

    self.get_results = function(callback, since, delay) {
        if (!since)
            since = 0;
        var params = {
            url: "/api/results2?since=" + since,
            success: callback,
            //error: get_results_error,                 // no need to handle
            dataType: "xml"
        };
        var closure = function() {
            $.ajax(params);
        };
        if (delay) {
            setTimeout(closure, delay);
            return;
        }
        closure();
    }

    self.unix_time = function() {
        var date = new Date();
        var seconds = date.getTime() / 1000;
        seconds = Math.round(seconds);
        return seconds;
    }

    // process results

    self.result_fields = ["timestamp", "internalAddress", "realAddress",
     "remoteAddress", "connectTime", "latency", "downloadSpeed", "uploadSpeed"];

    self.result_titles = ["Timestamp", "Internal Address", "Real Address",
     "Remote Address", "Connect Time", "Latency", "Download Speed",
     "Upload Speed"];

    self.results_processor = function(callback) {
        var my = {};

        my.process_results = function(data) {
            $(data).find("SpeedtestCollect").each(function() {
                var result = {};
                var entry = $(this);
                for (i = 0; i < self.result_fields.length; i++) {
                    var field = self.result_fields[i];
                    // XXX Assume everything is OK
                    var text = $(entry).children(field).text();
                    result[field] = text;
                }
                callback(result);
            });
            // notify we have finished
            callback(undefined);
        }

        return my;
    };

    // results formatter

    self.results_formatter_table = function() {
        var my = {};

        var needinit = true;
        var odd = true;
        var html = "";

        function init() {
            var i;
            html += '<center><table id="speedtest">';
            html += "<thead>";
            for (i = 0; i < self.result_fields.length; i++) {
                html += '<th>' + self.result_titles[i] + '</th>';
            }
            html += "</thead>";
        }

        function finish() {
            html += "</tbody></table></center>";
            $("#results").html($(html));
        }

        function to_date(x) {
            date = self.timestamp_to_date(x)
            fmt = self.format_date(date);
            return (fmt);
        }

        function to_msec(x) {
            return (1000 * x).toFixed(0) + " ms";
        }

        function to_Mbit(x) {
            return (x * 8/1024/1024).toFixed(2) + " Mbit/s";
        }

        my.format_result = function(result) {
            if (needinit) {
                needinit = false;
                init();
            }
            if (!result) {
                finish();
                return;
            }
            html += (odd) ? '<tr class="odd">' : '<tr class="even">';
            odd = !odd;

            // XXX Make sure we match self.result_titles' order (above)
            html += "<td>" + to_date(result["timestamp"]) + "</td>";
            html += "<td>" + result["internalAddress"] + "</td>";
            html += "<td>" + result["realAddress"] + "</td>";
            html += "<td>" + result["remoteAddress"] + "</td>";
            html += "<td>" + to_msec(result["connectTime"]) + "</td>";
            html += "<td>" + to_msec(result["latency"]) + "</td>";
            html += "<td>" + to_Mbit(result["downloadSpeed"]) + "</td>";
            html += "<td>" + to_Mbit(result["uploadSpeed"]) + "</td>";

            html += "</tr>";
        }

        return my;
    };

    self.results_formatter_plot = function() {
        var my = {};

        var ipCounter = {};
        var ipCounterN = 0;
        var downloadData = [];
        var uploadData = [];
        var downloadLabels = [];
        var uploadLabels = [];

        var curtime = self.unix_time();

        function to_Mbit(x) {
            return (x * 8/1024/1024).toFixed(2);
        }

        my.format_result = function(result) {
            if (!result) {
                do_plot();
                return;
            }

            var address = result["realAddress"];
            var timestamp = result["timestamp"];
            var download = result["downloadSpeed"];
            var upload = result["uploadSpeed"];

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
            download = Number(to_Mbit(download));
            upload = Number(to_Mbit(upload));
            downloadData[counter].push([timediff, download]);
            uploadData[counter].push([timediff, upload]);
        }

        function do_plot() {
            data = downloadData.concat(uploadData);
            var plot = $.jqplot("chartdiv1", data, {
              title: {
                text: "Download and upload rate"
              },
              axes: {
                xaxis: {
                  label: "Hours ago",
                  min: -24,
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
            $('.jqplot-table-legend').css('top', '200');
        }

        return my;
    };

    // get state

    self.state_tracker = function(callback) {
        var my = {};
        var curtime = 0;

        // In case of error keep trying because it might just
        // be that the user is restarting neubot, but also add
        // a significant delay to let the browser breathe

        function get_state_error() {
            setTimeout(get_state, 5000);
        }

        // If we fail to find the top-level XML tag treat
        // that as an error and keep trying softly
        // setTimeout(..., 0) is to give the browser some
        // time to breathe and possibly re-draw the page

        function get_state_success(data) {
            var state = $(data).children("state");
            if (state == undefined) {
                setTimeout(get_state, 5000);
                return;
            }
            var t = $(state).attr("t");
            if (curtime == undefined) {
                setTimeout(get_state, 5000);
                return;
            }
            curtime = t;
            // Pass data to ease integration with existing code
            callback(data);
            setTimeout(get_state, 0);
        }

        function get_state() {
            var params = {
                url: "/api/state?t=" + curtime,
                error: get_state_error,
                success: get_state_success,
                dataType: "xml"
            };
            $.ajax(params);
        }

        // Google Chrome tab icon will keep spinning unless we
        // delay the first get_state a bit

        my.start = function() {
            setTimeout(get_state, 100);
        }

        return my;
    }

    // top-level wrappers

    self.update_results_table = function(delay) {
        formatter = self.results_formatter_table();
        processor = self.results_processor(formatter.format_result);
        self.get_recent_results(processor.process_results, delay);
    }

    self.update_results_plot = function(delay) {
        formatter = self.results_formatter_plot();
        processor = self.results_processor(formatter.format_result);
        self.get_recent_results(processor.process_results, delay);
    }

    // utils

    self.XML_text = function(selector, data) {
        var text = $(selector, data).text();
        if (text == "")
            return (text);
        text = $.trim(text);
        return (text);
    }

    self.XML_number = function(selector, data) {
        var text = self.XML_text(selector, data);
        if (text == "")
            return (text);
        var number = Number(text);
        return (number);
    }

    self.XML_timestamp = function(selector, data) {
        return (self.XML_number(selector, data));
    }

    self.timestamp_to_minutes = function(t) {
        return (Math.ceil(t / 60));
    }

    self.format_minutes = function(t) {
        if (t > 1)
            s = t + " minutes";
        else
            s = t + " minute";
        return (s);
    }

    self.timestamp_to_date = function(t) {
        t = t * 1000;
        var date = new Date(t);
        return (date);
    }

    self.format_date = function(date) {
        function pad(n) {
            return n < 10 ? '0' + n : n
        }
        return date.getFullYear() + '-' + pad(date.getMonth() + 1)
          + '-' + pad(date.getDate()) + '\n' + pad(date.getHours()) + ':'
          + pad(date.getMinutes());
    }

    // closure

    return self;
})();
