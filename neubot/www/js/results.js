/* neubot/www/js/results.js */

/*-
 * Copyright (c) 2010, 2013
 *     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
 *     and Simone Basso <bassosimone@gmail.com>
 *
 * Copyright (c) 2011-2012
 *     Alessio Palmero Aprosio <alessio@apnetwork.it>
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
// Documented-by: doc/results.js.{dia,png,svg}
// Last-jslint: Wed Mar 13 16:24:50 CET 2013
//

var results = (function () {
    /*"use strict";*/  // Only when running jslint

    var self = {};

    self.one_day_in_ms = 24 * 60 * 60 * 1000;
    self.one_hour_in_ms = 60 * 60 * 1000;

    function jqplot_plotter() {

        var self = {};

        self.params = {
            title: {
                text: "",
                fontSize: "16pt"
            },
            axes: {
                xaxis: {
                    labelRenderer: jQuery.jqplot.CanvasAxisLabelRenderer,
                    renderer: jQuery.jqplot.DateAxisRenderer,
                    label: "",
                    showTickMarks: true,
                    tickOptions: {}
                },
                yaxis: {
                    labelRenderer: jQuery.jqplot.CanvasAxisLabelRenderer,
                    label: "",
                    min: 0
                }
            },
            legend: {
                show: 1,
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
            series: []
        };

        self.data = [];
        self.div = "";

        self.set_title = function (title) {
            self.params.title.text = title;
        };

        self.set_xmin = function (value) {
            self.params.axes.xaxis.min = value;
        };

        self.set_xfmt = function (value) {
            self.params.axes.xaxis.tickOptions.formatString = value;
        };

        self.set_xlabel = function (value) {
            self.params.axes.xaxis.label = value;
        };

        self.set_ylabel = function (value) {
            self.params.axes.yaxis.label = value;
        };

        self.set_data = function (value) {
            self.data = value;
        };

        self.set_div = function (value) {
            self.div = value;
        };

        self.set_per_serie_options = function (value) {
            self.params.series = value;
        };

        self.show_hide_legend = function (value) {
            self.params.legend.show = value;
        };

        self.plot = function (container) {
            var message, html;

            html = "<div class='chartdiv' id='" + self.div + "'></div>";
            jQuery(container).append(html);
            if (self.data === undefined || self.data.length <= 0) {
                message = i18n.get("No results");
                jQuery(self.div).html("<span>" + message + "</span>");
                return;
            }
            jQuery.jqplot(self.div, self.data, self.params).replot();
            jQuery('.jqplot-table-legend').css('top', '200');  // Magik
        };

        return self;
    }

    function build_vector(result, key, formatter) {
        var dataset, k, timestamp, value;

        dataset = [];
        for (k = 0; k < result.length; k += 1) {
            timestamp = result[k].timestamp * 1000;  // To millisec
            value = result[k][key];
            switch (formatter) {
            case "time":
                value = utils.toMsNumber(value);
                break;
            case "speed":
                value = utils.toMbitsPerSecondNumber(value);
                break;
            default:
                /* nothing */
                break;
            }
            dataset.push([timestamp, value]);
        }

        return dataset;
    }

    function build_per_serie_options(label, address, marker) {
        var dictionary;

        if (address !== "") {
            label += " (" + address + ")";
        }
        dictionary = {
            label: label,
            markerOptions: {
                style: marker
            },
            neighborThreshold: -1
        };

        return dictionary;
    }

    function mkplot(info, dataset, result, data, options) {
        var address, data_by_ip, formatter, i, key, label, marker;

        formatter = dataset.formatter;
        key = dataset.key;
        label = dataset.label;
        marker = dataset.marker;

        data_by_ip = {};
        if (!info.www_no_split_by_ip) {
            for (i = 0; i < result.length; i += 1) {
                address = result[i].real_address;
                if (data_by_ip[address] === undefined) {
                    data_by_ip[address] = [];
                }
                data_by_ip[address].push(result[i]);
            }
        } else {
            data_by_ip[""] = result;
        }

        jQuery.each(data_by_ip, function (address, vector) {
            data.push(build_vector(vector, key, formatter));
            options.push(build_per_serie_options(label, address, marker));
        });
    }

    // We added this function in 2012, to workaround a jqplot bug. It makes
    // sense to check whether this is still needed with newer jqplots.
    function compute_xmin(result, since) {
        var k, list, timestamp, xmin;

        list = [];
        for (k = 0; k < result.length; k += 1) {                /* XXX */
            timestamp = result[k].timestamp * 1000;
            list.push(timestamp);
        }
        if (list.length > 0) {
            xmin = Math.min.apply(null, list) - 300000;
        } else {
            xmin = since;
        }

        return xmin;
    }

    function compute_xfmt(since) {
        var hours, xfmt;

        hours = Math.abs(Math.round((since - utils.getNow()) /
                      (1000 * 60 * 60)));
        if (hours <= 120) {
            xfmt = '%b %#d, h %H';
        } else {
            xfmt = '%b %#d';
        }

        return xfmt;
    }

    function formatter_plot(info, result, since, until) {
        var data, i, j, options, plotter;

        for (i = 0; i < info.plots.length; i += 1) {
            plotter = jqplot_plotter();
            plotter.set_div("chartdiv" + (i + 1));
            plotter.set_title(info.plots[i].title);
            plotter.set_xlabel(info.plots[i].xlabel);
            plotter.set_ylabel(info.plots[i].ylabel);
            plotter.set_xmin(compute_xmin(result, since));
            plotter.set_xfmt(compute_xfmt(since));
            data = [];
            options = [];
            for (j = 0; j < info.plots[i].datasets.length; j += 1) {
                mkplot(info, info.plots[i].datasets[j], result, data, options);
            }
            plotter.set_data(data);
            plotter.set_per_serie_options(options);
            plotter.show_hide_legend(!info.www_no_legend);
            plotter.plot("#charts");
        }
    }

    function formatter_table(info, data, since, until) {
        var html = "", i, j, key, value;

        html += '<center><table id="results_table">';
        html += "<thead><tr>";
        for (j = 0; j < info.table.length; j += 1) {
            html += '<th>' + info.table[j].label + '</th>';
        }
        html += "</tr></thead>";
        html += "<tbody>";

        for (i = 0; i < data.length; i += 1) {
            html += "<tr>";
            for (j = 0; j < info.table.length; j += 1) {
                key = info.table[j].key;
                value = data[i][key];
                switch (info.table[j].formatter) {
                case "time":
                    value = utils.toMs(value);
                    break;
                case "speed":
                    value = utils.toMbitsPerSecond(value);
                    break;
                case "datetime":
                    value = utils.getTimeFromSeconds(value, true);
                    break;
                default:
                    /* nothing */
                    break;
                }
                html += "<td>" + value + "</td>";
            }
            html += "</tr>";
        }

        html += "</tbody></table></center>";
        jQuery("#results").html(html);
    }

    function get_data(info, since, until) {
        var data;

        data = {
            'test': info.selected_test
        };
        if (since !== undefined) {
            data.since = Math.ceil(since / 1000);
        }
        if (until !== undefined) {
            data.until = Math.ceil(until / 1000);
        }
        jQuery.ajax({
            url: '/api/data',
            data: data,
            success: function (data) {
                jQuery("#charts").html("");
                jQuery("#results").html("");
                if (!info.www_no_plot) {
                    formatter_plot(info, data, since, until);
                }
                if (!info.www_no_table) {
                    formatter_table(info, data, since, until);
                }
            },
            dataType: "json"
        });
    }

    /*
     * This function processes the JSON returned by /api/results. The JSON is
     * a dictionary that describes how to construct the plots and the table
     * of the selected test (plus a list of existing tests). This information
     * is not hardcoded somewhere in this file because we want users (and
     * especially power users) to be able to change the appearance of plots
     * and tables in a simpler way (i.e., by editing the corresponding files
     * in WWWDIR/test).
     *
     * To better understand this function, it helps to read the output
     * of `curl http://127.0.0.1:9774/api/results?debug=1`.
     */
    function handle_api_results(info) {
        var html, i, since;

        // Dynamically populate the list of available tests
        html = "";
        for (i = 0; i < info.available_tests.length; i += 1) {
            html += '<option value="';
            html += info.available_tests[i];
            html += '"';
            if (info.selected_test === info.available_tests[i]) {
                html += ' selected="selected"';
            }
            html += '>' + info.available_tests[i] + '</option>\n';
        }
        jQuery("#res_type_value").html(html);

        if (!info.www_no_description) {
            //
            // Emulate what happens when we load the page: write the description
            // of the test and then run the i18n engine.
            //
            jQuery(".i18n").css("visibility", "hidden");
            jQuery("#results_description").html(info.description);
            i18n.translate_page("", /^(i18n_results_[a-z0-9_]+)$/i);
            jQuery(".i18n").css("visibility", "visible");
        }
        if (!info.www_no_title) {
            jQuery("#results_title").html(i18n.get(info.title));
        }

        /*
         * TODO Validation of input should probably be performed
         * before we invoke /api/results API.
         */
        since = Number(jQuery("#res_value").val());
        if (isNaN(since)) {
            alert(i18n.get("Please insert a valid number"));  /* XXX */
            return;
        }
        switch (jQuery("#res_unit").val()) {
        case "d":
            since = utils.getNow() - self.one_day_in_ms * since;
            break;
        case "h":
            since = utils.getNow() - self.one_hour_in_ms * since;
            break;
        default:
            /* nothing */
            break;
        }

        get_data(info, since);
    }

    function call_api_results(data) {
        jQuery.ajax({
            url: "/api/results",
            data: data,
            dataType: 'json',
            success: handle_api_results
        });
    }

    function confirm_test() {
        call_api_results({
            'test': jQuery("#res_type_value").val()
        });
        return false;
    }

    self.init = function () {
        jQuery.jqplot.config.enablePlugins = true;
        utils.setActiveTab("results");
        state.tracker().start();
        jQuery("#res_value").keydown(function (event) {
            if (event.keyCode === 13) {
                return confirm_test();
            }
            return true;
        });
        jQuery("#res_type_submit").click(confirm_test);
        // By passing no parameter we tell api_results.py to show the results
        // of the default test (i.e., the one indicated by the setting named
        // `www_default_test_to_show` - see neubot/config.py).
        call_api_results();
    };

    return self;

}());

jQuery(document).ready(function () {
    /*"use strict";*/  // Only when running jslint
    i18n.translate(results.init);
});
