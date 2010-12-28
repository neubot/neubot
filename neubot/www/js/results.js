/* neubot/www/results.js */
/*
 * Copyright (c) 2010 Antonio Servetti <antonio.servetti@polito.it>,
 *  Politecnico di Torino
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

/* use a function for the exact format desired... */
function LocaleDateString(d){
    function pad(n) {
        return n < 10 ? '0' + n : n
    }
    return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-'
      + pad(d.getDate()) + '\n' + pad(d.getHours()) + ':'
      + pad(d.getMinutes());
}

function getresults(data){
    var html = "";
    var fields = ["timestamp", "internalAddress", "realAddress",
                  "remoteAddress", "connectTime", "latency",
                  "downloadSpeed", "uploadSpeed"];
    var titles = ["Timestamp", "Internal Address", "Real Address",
                  "Remote Address", "Connect Time", "Latency",
                  "Download Speed", "Upload Speed"];
    var i, nn, n = document.getElementById("step").range[0];

    var download = [], upload = [];
    var ipCounter = {}, ipCounterN = 0;
    var downloadLabels = [ ], uploadLabels = [];
    var plotTicks = [];

    nn = n;

    if (n == 0) {
        $('#prev').addClass("disabled");
    } else {
        $('#prev').removeClass("disabled");
    }

    /*
     * Make table header
     */

    html += '<center><table id="speedtest">';
    html += "<thead>";
    for (i = 0; i < fields.length; i++) {
        html += '<th>' + titles[i] + '</th>';
    }
    html += "</thead>";

    /*
     * Make table body
     */

    html += "<tbody>";
    $(data).find("SpeedtestCollect").each(function() {
        var $entry = $(this);
        var trclass;
        var val, txt;

        /*
         * Declare table row, and differentiate color
         * for even and odd lines.
         */

        if (n % 2) {
            trclass = "odd";
        } else {
            trclass = "even";
        }
        html += '<tr class="'+ trclass + '">';

        /*
         * Fill the row and gather data for the plot.
         * XXX We should scale the unit depending on the actual
         * speed, latency.
         */

        for (i = 0; i < fields.length; i++) {
            val = $entry.find(fields[i]).text();
            switch(fields[i]) {
                case 'realAddress':
                    var address = val;
                    if (ipCounter[address] == undefined) {
                        ipCounter[address] = ipCounterN;
                        download[ipCounterN] = [];
                        upload[ipCounterN] = [];
                        downloadLabels[ipCounterN] = {
                          label: "DOWN " + address,
                          markerOptions: {style:'square'},
                          neighborThreshold: -1
                        };
                        uploadLabels[ipCounterN] = {
                          label: "UP " + address,
                          markerOptions:{style:'circle'},
                          neighborThreshold: -1
                        };
                        ipCounterN++;
                    }
                    txt = address;
                    break;
                case 'timestamp':
                    var timestamp = new Date(val*1000);
                    var rg = new RegExp("GMT");
                    /*
                     * XXX We might want to add a field with
                     * the sample number.
                     * XXX IIUIC here we use GMT which could
                     * be a bit misleading for users.
                     */
                    plotTicks.unshift([
                      Number(n-nn),
                      LocaleDateString(timestamp)
                    ]);
                    txt = n++ + " " + timestamp.toString().replace(/GMT.*$/,"");
                    break;
                case 'connectTime':
                case 'latency':
                    txt = (val * 1000).toFixed(0) + " ms";
                    break;
                case 'downloadSpeed':
                    txt = (val * 8/1024/1024).toFixed(3);
                    download[ipCounter[address]].unshift([
                      Number(n-nn-1),
                      Number(txt)
                    ]);
                    txt += " Mb/s";
                    break;
                case 'uploadSpeed':
                    txt = (val * 8/1024/1024).toFixed(3);
                    upload[ipCounter[address]].unshift([
                      Number(n-nn-1),
                      Number(txt)
                    ]);
                    txt += " Mb/s";
                    break;
                default:
                    txt = val;
                    break;
            }
            if (txt != "")
                html += '<td>' + txt + '</td>';
        }

        html += "</tr>"
    });

    html += "</tr>";
    html += "</tbody></table></center>";
    $("#results").html($(html));

    if(n != document.getElementById("step").range[1]) {
        $('#next').addClass("disabled");
        document.getElementById("step").range[1] = n;
    } else {
        $('#next').removeClass("disabled");
    }

    /*
     * Create and show the plot
     */

    var bandwidthPlot = $.jqplot(
      "chartdiv1",
      download.concat(upload), {
        axesDefaults: {
          tickRenderer: $.jqplot.CanvasAxisTickRenderer
        },
        title: {
          text: "Download and Upload Rate"
        },
        axes: {
          xaxis: {
            label: "Time",
            ticks: plotTicks,
            tickOptions: {
              angle: -90,
              fontSize: '10pt', showMark: true
            },
            showTickMarks: true
          },
          yaxis: {
            label: "Mb/s",
            min: 0
          }
        },
        legend: {
          show: true
        },
        cursor: {
          showVerticalLine:false,
          showHorizontalLine:true,
          showCursorLegend: false,
          showTooltip: false,
          tooltipLocation: 'sw',
          zoom: true
        },
        highlighter: {show: false},
        series: downloadLabels.concat(uploadLabels)
      });

    bandwidthPlot.replot();
}

$(document).ready(function() {
    $.jqplot.config.enablePlugins = true;

    var elm = document.getElementById("step");
    var inc = Number($('#step').val());
    var start = 0, stop = start + inc;

    elm.range = [ start, stop ];
    $.get("/api/results?start=" + start + "&stop=" + stop, getresults);

    /*
     * TODO The API to access results it way too low level, and it
     * would be much better to access time ranges, e.g. gimme all the
     * results in the last month.
     * TODO Another quirk is that the API just returns the cache but
     * we want to access the whole data set.
     */

    $("#step").keyup(function(event){
      if(event.keyCode == 13) {
        inc = Number(elm.value);
        stop = start + inc;
        elm.range = [ start, stop ];
        $.get("/api/results?start=" + start + "&stop=" + stop, getresults);
        return false;
      }
    });

    $('#prev').click(function() {
        inc = Number(elm.value);
        if (start > inc) {
            stop -= inc;
            start = stop - inc;
        } else {
            start = 0;
            stop = inc;
        }
        elm.range = [ start, stop ];
        $.get("/api/results?start=" + start + "&stop=" + stop, getresults);
        return false;
    });

    $('#next').click(function() {
        inc = Number(elm.value);
        if(stop != elm.range[1]) {
            /* nothing */ ;
        } else {
            start += inc;
            stop = start + inc;
        }
        elm.range = [ start, stop ];
        $.get("/api/results?start=" + start + "&stop=" + stop, getresults);
        return false;
    });
});
