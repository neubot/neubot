/* neubot/www/js/speedtest.js */
/*
 * Copyright (c) 2011-2012 Alessio Palmero Aprosio <alessio@apnetwork.it>,
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

var results = (function() {
    var self = {};
    self.request = {};

    self.result_fields = [];
    self.result_titles = [];

    self.init = function(request) {
        self.request = request;

        jQuery("#results_title").html(i18n.get(self.request.title));
        jQuery("#results_description").html(i18n.get(self.request.description));

        self.result_fields = [];
        self.result_titles = [];

        jQuery.each(request.table_fields, function(i, v) {
            self.result_fields.push(i);
            self.result_titles.push(v);
        });
    }

    self.get_results = function(callbacks, since, unit, until) {
        var res = new Array();
        if (!since) {
            since = 0;
        }
        since_s = Math.ceil(since / 1000);
        var url = "/api/data?test=" + self.request.selected_test + "&since=" + since_s;
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

    self.formatter_table = function(data, since, unit, until) {
        var i;
        var html = "";

        html += '<center><table id="results_table">';
        html += "<thead><tr>";
        for (i = 0; i < self.result_fields.length; i++) {
            html += '<th>' + self.result_titles[i] + '</th>';
        }
        html += "</tr></thead>";
        html += "<tbody>";

        for (i = 0; i < data.length; i++) {
            var result = data[i];

            html += "<tr>";
            jQuery.each(self.request.table_fields, function(i, v) {
                var formatted = result[i];
                switch (self.request.table_types[i]) {
                    case "ms":
                    formatted = utils.toMs(formatted);
                    break;
                    case "mbits":
                    formatted = utils.toMbitsPerSecond(formatted);
                    break;
                    case "datetime":
                    formatted = utils.getTimeFromSeconds(formatted, true);
                    break;
                }
                html += "<td>" + formatted + "</td>";
            });
            html += "</tr>";
        }

        html += "</tbody></table></center>";

        jQuery("#results").html(html);
        return html;
    };

    self.formatter_plot = function(data, since, unit, until) {

        var num_of_plots = self.request.axis_labels.length;

        var dataType = [];
        var dataTypeLabels = [];
        var dataTypeShape = [];
        var dataType_no = [];

        var j = 0;
        for (var i = 0; i < num_of_plots; i++) {
            dataType_no[i] = [];
            jQuery.each(self.request.datasets[i][0], function(index, value) {
                dataType_no[i].push(index);
                dataType.push(index);
                dataTypeLabels.push(value);

                // Not good!
                if (++j % 2) {
                    dataTypeShape.push("square");
                }
                else {
                    dataTypeShape.push("circle");
                }
            })
        }

        var ipCounter = [];
        var ipCounterN = 0;
        var myData = [];
        var labels = [];

        var timestamps = [];
        var minx = 0;

        for (var j = 0; j < dataType.length; j++) {
            myData[dataType[j]] = [];
            labels[dataType[j]] = [];
        }

        for (i = 0; i < data.length; i++) {
            var result = data[i];
            var address = result["real_address"];
            var timestamp = result["timestamp"];

            if (ipCounter[address] == undefined) {      // XXX
                ipCounter[address] = ipCounterN;

                for (var j = 0; j < dataType.length; j++) {
                    myData[dataType[j]][ipCounterN] = []
                    labels[dataType[j]][ipCounterN] = {
                        label: dataTypeLabels[j] + " " + address,
                        markerOptions: {
                          style: dataTypeShape[j]
                        },
                        neighborThreshold: -1
                    };

                }
                ipCounterN++;
            }

            counter = ipCounter[address];
            timestamp *= 1000;

            for (var j = 0; j < dataType.length; j++) {
                switch (self.request.table_types[dataType[j]]) {
                    case "mbits":
                    myData[dataType[j]][counter].push([timestamp, Number(utils.toMbitsPerSecondNumber(result[dataType[j]]))]);
                    break;
                    case "ms":
                    myData[dataType[j]][counter].push([timestamp, 1000 * result[dataType[j]]]);
                    break;
                }
            }

            timestamps.push(timestamp);
        }

        // Do not waste plot estate without a good reason
        if (timestamps.length) {
            minx = Math.min.apply(null, timestamps) - 300000;
        }
        else {
            minx = since;
        }

        var xaxis = {
            labelRenderer: jQuery.jqplot.CanvasAxisLabelRenderer,
            renderer: jQuery.jqplot.DateAxisRenderer,
            showTickMarks: true,
            min: minx
        };

        var hours = Math.abs(Math.round((since - utils.getNow()) / (1000 * 60 * 60)));

        if (hours <= 120) {
            xaxis.tickOptions = {
              formatString:'%b %#d, h %H'
            };
        }
        else {
            xaxis.tickOptions = {
              formatString:'%b %#d'
            };
        }

        jQuery("#charts").html("");

        for (var i = 0; i < num_of_plots; i++) {
            jQuery("#charts").append("<div class='chartdiv' id='chartdiv" + (i + 1) + "'></div>");

            if (myData[dataType_no[i][1]]) {
                mydata = myData[dataType_no[i][0]].concat(myData[dataType_no[i][1]]);
            }
            else {
                mydata = myData[dataType_no[i][0]];
            }

            if (mydata.length) {
                xaxis.label = self.request.axis_labels[i][0];
                var plot = jQuery.jqplot("chartdiv" + (i + 1), mydata, {
                  title: {
                    text: i18n.get("Your speedtest download and upload speed"),
                    fontSize: "16pt"
                  },
                  axes: {
                    xaxis: xaxis,
                    yaxis: {
                      labelRenderer: jQuery.jqplot.CanvasAxisLabelRenderer,
                      label: self.request.axis_labels[i][1],
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
                  series: labels[dataType_no[i][0]].concat(labels[dataType_no[i][1]])
                });

                plot.replot();
            }
            else {
                jQuery("#chartdiv" + (i + 1)).html("<span>" + i18n.get("No results") + "</span>");
            }
        }

        // some additional CSS-magic
        jQuery('.jqplot-table-legend').css('top', '200');
    };

    return self;
})();

function results_init() {
    utils.setActiveTab("results");

    jQuery.jqplot.config.enablePlugins = true;

    var confirm_test = function() {
        var testname = jQuery("#res_type_value").val();

        jQuery.ajax({
            url: "/api/results",
            data: {
                'test': testname
            },
            dataType: 'json',
            success: function(myrequest) {
                results.init(myrequest);

                var n = Number(jQuery("#res_value").val());
                if (n == NaN) {
                    alert(i18n.get("Please insert a valid number"));
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

                results.get_results([results.formatter_table, results.formatter_plot], since);
            }
        });
    }

    jQuery("#res_value").keydown(function(event) {
        if (event.keyCode == 13) {
            return confirm_test();
        }
    });
    jQuery("#res_type_submit").click(confirm_test);
    confirm_test();

    tracker = state.tracker();
    tracker.start();
};

jQuery(document).ready(function() {
    i18n.translate(results_init);
});
