/*-
 * neubot/www/results.js
 * Copyright (c) 2010 NEXA Center for Internet & Society
 * License: GNU GPLv3
 */

function getresults(data){
    var html = "";
    var fields = ["timestamp", "internalAddress", "realAddress",
                  "remoteAddress", "connectTime", "latency",
                  "downloadSpeed", "uploadSpeed"];
    var titles = ["Timestamp", "Internal Address", "Real Address",
                  "Remote Address", "Connect Time", "Latency",
                  "Download Speed", "Upload Speed"];
    var i, n = document.getElementById("step").range[0];

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
         * Fill the row.  XXX We should scale the unit depending
         * on the actual speed, latency.
         */

        for (i = 0; i < fields.length; i++) {
            val = $entry.find(fields[i]).text();
            switch(fields[i]) {
                case 'timestamp':
                    var timestamp = new Date(val*1000);
                    var rg = new RegExp("GMT");
                    /*
                     * XXX We might want to add a field with
                     * the sample number.
                     * XXX IIUIC here we use GMT which could
                     * be a bit misleading for users.
                     */
                    txt = n++ + " " + timestamp.toString().replace(/GMT.*$/,"");
                    break;
                case 'connectTime':
                case 'latency':
                    txt = (val * 1000).toFixed(0) + " ms";
                    break;
                case 'downloadSpeed':
                case 'uploadSpeed':
                    txt = (val * 8/1024/1024).toFixed(3) + " Mb/s";
                    break;
                default:
                    txt = val;
                    break;
            }
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
}

$(document).ready(function() {
    /* XXX */
    $("#content").prepend('<center><h2>Speedtest results - <a id="prev" href="#">&lt;&lt;</a>&nbsp;<input id="step" type="text" value="20" size="1" style="text-align: center"/>&nbsp;<a id="next" href="#">&gt;&gt;</a></h2></center><br>');

    var elm = document.getElementById("step");
    var inc = Number($('#step').val());
    var start = 0, stop = start + inc;

    elm.range = [ start, stop ];
    $.get("/api/results?start=" + start + "&stop=" + stop, getresults);

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
