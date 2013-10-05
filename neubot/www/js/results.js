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
// Last-jslint: Sun Mar 17 20:41:06 CET 2013
//

var results = (function () {
    /*"use strict";*/  // Only when running jslint

    var self = {};

    self.one_day_in_ms = 24 * 60 * 60 * 1000;
    self.one_hour_in_ms = 60 * 60 * 1000;
    self.one_min_in_ms = 60 * 1000;

    function eval_recipe(code, result) {

        function must_be_array(target) {
            if (jQuery.type(target) !== "array") {
                throw "must_be_array: not an array";
            }
            return target;
        }

        function must_be_number(target) {
            if (jQuery.type(target) !== "number") {
                throw "must_be_number: not a number";
            }
            return target;
        }

        function must_be_string(target) {
            if (jQuery.type(target) !== "string") {
                throw "must_be_string: not a string";
            }
            return target;
        }

        function must_not_be_undefined(target) {
            if (target === undefined) {
                throw "must_not_be_undefined: passed undefined value";
            }
            return target;
        }

        function apply_append(left, right) {
            return must_be_string(left) + must_be_string(right);
        }

        function apply_divide(left, right) {
            return must_be_number(left) / must_be_number(right);
        }

        function apply_map_select(selector, target) {
            var i, tmp = [];

            must_be_string(selector);
            must_be_array(target);

            for (i = 0; i < target.length; i += 1) {
                tmp.push(target[i][selector]);
            }

            return tmp;
        }

        function apply_parse_json(target) {
            return jQuery.parseJSON(must_be_string(target));
        }

        function apply_reduce_avg(target) {
            var i, tmp = 0.0;

            must_be_array(target);

            for (i = 0; i < target.length; i += 1) {
                tmp += target[i];
            }
            if (target.length > 0) {
                tmp /= target.length;
            }

            return tmp;
        }

        function apply_select(selector, target) {

            if (jQuery.type(selector) === "string") {
                return must_not_be_undefined(target[selector]);
            }

            if (jQuery.type(selector) === "number"
                    && jQuery.type(target) === "array") {
                if (selector < 0) {
                    selector += target.length;  /* Pythonism */
                }
                return must_not_be_undefined(target[selector]);
            }

            throw "apply_select: invalid arguments";
        }

        function apply_to_datetime(target) {
            return utils.getTimeFromSeconds(must_be_number(target), true);
        }

        function apply_to_fixed(target) {
            return utils.toFixed(must_be_number(target));
        }

        function apply_to_millisecond(target) {
            return utils.toMsNumber(must_be_number(target));
        }

        function apply_to_millisecond_string(target) {
            return utils.toMs(must_be_number(target));
        }

        function apply_to_speed(target) {
            return utils.toMbitsPerSecondNumber(must_be_number(target));
        }

        function apply_to_speed_string(target) {
            return utils.toMbitsPerSecond(must_be_number(target));
        }

        function apply_to_string(target) {
            return target.toString();
        }

        function do_eval(curcode) {

            function eval_target(target) {
                if (jQuery.type(target) === "array") {
                    return do_eval(target);         /* XXX recursion */
                }
                if (target === "result") {
                    return result;
                }
                if (jQuery.type(target) === "string") {
                    return target;
                }
                throw "eval_target: invalid target";
            }

            // append string string
            if (curcode[0] === "append") {
                if (curcode.length !== 3) {
                    throw "do_eval: append: invalid curcode length";
                }
                return apply_append(eval_target(curcode[1]),
                                    eval_target(curcode[2]));
            }

            // divide left right
            if (curcode[0] === "divide") {
                if (curcode.length !== 3) {
                    throw "do_eval: divide: invalid curcode length";
                }
                return apply_divide(eval_target(curcode[1]),
                                    eval_target(curcode[2]));
            }

            // map-select key target
            if (curcode[0] === "map-select") {
                if (curcode.length !== 3) {
                    throw "do_eval: map-select: invalid curcode length";
                }
                return apply_map_select(curcode[1], eval_target(curcode[2]));
            }

            // parse-json target
            if (curcode[0] === "parse-json") {
                if (curcode.length !== 2) {
                    throw "do_eval: parse-json: invalid curcode length";
                }
                return apply_parse_json(eval_target(curcode[1]));
            }

            // reduce-avg target
            if (curcode[0] === "reduce-avg") {
                if (curcode.length !== 2) {
                    throw "do_eval: reduce-avg: invalid curcode length";
                }
                return apply_reduce_avg(eval_target(curcode[1]));
            }

            // select key target
            if (curcode[0] === "select") {
                if (curcode.length !== 3) {
                    throw "do_eval: select: invalid curcode length";
                }
                return apply_select(curcode[1], eval_target(curcode[2]));
            }

            // to-datetime target
            if (curcode[0] === "to-datetime") {
                if (curcode.length !== 2) {
                    throw "do_eval: to-datetime: invalid curcode length";
                }
                return apply_to_datetime(eval_target(curcode[1]));
            }

            // to-fixed target
            if (curcode[0] === "to-fixed") {
                if (curcode.length !== 2) {
                    throw "do_eval: to-fixed: invalid curcode length";
                }
                return apply_to_fixed(eval_target(curcode[1]));
            }

            // to-millisecond target
            if (curcode[0] === "to-millisecond") {
                if (curcode.length !== 2) {
                    throw "do_eval: to-millisecond: invalid curcode length";
                }
                return apply_to_millisecond(eval_target(curcode[1]));
            }

            // to-millisecond-string target
            if (curcode[0] === "to-millisecond-string") {
                if (curcode.length !== 2) {
                    throw "do_eval: to-millisecond-string: "
                          + "invalid curcode length";
                }
                return apply_to_millisecond_string(eval_target(curcode[1]));
            }

            // to-speed target
            if (curcode[0] === "to-speed") {
                if (curcode.length !== 2) {
                    throw "do_eval: to-speed: invalid curcode length";
                }
                return apply_to_speed(eval_target(curcode[1]));
            }

            // to-speed-string target
            if (curcode[0] === "to-speed-string") {
                if (curcode.length !== 2) {
                    throw "do_eval: to-speed-string: invalid curcode length";
                }
                return apply_to_speed_string(eval_target(curcode[1]));
            }

            // to-string target
            if (curcode[0] === "to-string") {
                if (curcode.length !== 2) {
                    throw "do_eval: to-string: invalid curcode length";
                }
                return apply_to_string(eval_target(curcode[1]));
            }

            throw "do_eval: invalid curcode[0]";  /* Catches undefined too */
        }

        var retval;

        try {
            retval = do_eval(must_be_array(code));
        } catch (error) {
            /*console.log("eval_recipe failed: " + error);*/
            retval = undefined;
        }

        return retval;
    }

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
                location: "nw",
                predraw: 1,
                show: 1
            },
            cursor: {
                showVerticalLine: false,
                showHorizontalLine: true,
                showCursorLegend: false,
                showTooltip: true,
                tooltipLocation: 'se',
                zoom: true
            },
            highlighter: {
                sizeAdjust: 7.5,
                show: true
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

        // Not yet
        //self.set_ylogscale = function (value) {
        //    self.params.axes.yaxis.renderer = jQuery.jqplot.LogAxisRenderer;
        //};

        self.push_data = function (value) {
            self.data.push(value);
        };

        self.set_div = function (value) {
            self.div = value;
        };

        self.push_options = function (value) {
            self.params.series.push(value);
        };

        self.show_hide_legend = function (value) {
            self.params.legend.show = value;
        };

        self.plot = function (container) {
            var message, html;

            html = "<div class='chartdiv' id='" + self.div + "'></div>";
            jQuery(container).append(html);
            if (self.data === undefined || self.data.length <= 0) {
                jQuery.jqplot(self.div, [[null]], undefined).replot();
            } else {
                jQuery.jqplot(self.div, self.data, self.params).replot();
            }
        };

        return self;
    }

    function build_vector(result, recipe) {
        var dataset, k, timestamp, value;

        dataset = [];
        for (k = 0; k < result.length; k += 1) {
            timestamp = result[k].timestamp * 1000;  // To millisec
            value = eval_recipe(recipe, result[k]);
            if (value !== undefined) {
                dataset.push([timestamp, value]);
            }
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

    function mkplot(info, dataset, result, plotter) {
        var address, data_by_ip, i, label, marker, recipe;

        recipe = dataset.recipe;
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
            if (vector.length > 0) {
                vector = build_vector(vector, recipe);
                if (vector.length > 0) {
                    plotter.push_data(vector);
                    plotter.push_options(build_per_serie_options(label,
                                         address, marker));
                }
            }
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
        if (hours <= 4) {
            xfmt = '%H:%M';
        } else if (hours <= 120) {
            xfmt = '%b %#d, h %H';
        } else {
            xfmt = '%b %#d';
        }

        return xfmt;
    }

    function formatter_plot(info, result, since, until) {
        var i, j, plotter;

        for (i = 0; i < info.plots.length; i += 1) {
            plotter = jqplot_plotter();
            plotter.set_div("chartdiv" + (i + 1));
            plotter.set_title(info.plots[i].title);
            plotter.set_xlabel(info.plots[i].xlabel);
            plotter.set_ylabel(info.plots[i].ylabel);
            plotter.set_xmin(compute_xmin(result, since));
            plotter.set_xfmt(compute_xfmt(since));
            options = [];
            for (j = 0; j < info.plots[i].datasets.length; j += 1) {
                mkplot(info, info.plots[i].datasets[j], result, plotter);
            }
            plotter.show_hide_legend(!info.www_no_legend);
            plotter.plot("#charts");
        }
    }

    function formatter_table(info, data, since, until) {
        var html = "", i, j, recipe, value;

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
                recipe = info.table[j].recipe;
                value = eval_recipe(recipe, data[i]);
                if (value !== undefined) {
                    html += "<td>" + value + "</td>";
                }
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
        case "min":
            since = utils.getNow() - self.one_min_in_ms * since;
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
