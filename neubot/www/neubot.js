/* neubot/www/neubot.js */
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

function getcurstate(data) {
    var curtime = $(data).find("state").attr("t");
    var active = $.trim($(data).find("active").text());
    var current = "";
    var html = "";

    /*
     * Woah... either we are not talking with neubot or neubot
     * is down for some reason.  Wait for some time before trying
     * again.  Or we will overload the browser.
     */

    if (!curtime) {
        setTimeout(function() {
            $.get("/api/state?t=0", getcurstate);
        }, 5000);
        return;
    }

    /*
     * Update the program state
     */

    if (active == "true") {
        $("#daemon").html("<h2>Neubot is currently running.</h2>");
    } else {
        $("#daemon").html("<h2>Neubot is currently idle.</h2>");
    }

    /*
     * Available updates information
     */

    html = "";
    var update = $(data).find("update");
    if (update.text()) {
        html = "<h2>New version " + $(update).text() + " available at ";
        uri = update.attr("uri");
        html += '<a href="' + uri + '">' + uri + "</a>";
        html += "</h2>";
        $("#update").html($(html));
    }

    html = "";
    html += "<h2>Current Neubot state is</h2>";
    html += '<ul class="hlist gray">';
    $(data).find("activity").each(function() {
        var $entry = $(this);
        var id = "";
        var curr = $entry.attr("current");
        var txt = $.trim($entry.text());
        if (curr == "true") {
            id = 'id="active"';
            current = txt;
        }
        html += "<li " + id + " >" + txt + "</li>";
    });
    html += "</ul>";
    $("#state").html($(html));

    /*
     * Position in queue if we're negotiating
     */

    html = "";
    var details = $(data).find("negotiate");
    if (details) {
        $(details).find("queuePos").each(function() {
            var $entry = $(this);
            html += "<h2>Position in queue: " + $.trim($entry.text()) + "/";
        });
        $(details).find("queueLen").each(function() {
            var $entry = $(this);
            html += $.trim($entry.text()) + "</h2>";
        });
        $("#detail").html($(html));
    }

    /*
     * Get details of the current/latest test
     */

    html = "";
    var details = $(data).find("test");
    if (details && current != "negotiate") {
        var name = $.trim($(details).find("name").text());
        var results = new Array();
        if (active == "true") {
            html = "<h2>Details on current test: ";
        } else {
            html = "<h2>Details on latest test: ";
        }
        html += '<span id="testname">' + name + "</span>";
        html += "</h2>";
        html += '<ul class="projectseven-uberlist">';
        $(details).find("result").each(function() {
            var $entry = $(this);
            var tag = $entry.attr("tag");
            var txt = $.trim($entry.text());
            results[tag] = txt + " " + $entry.attr("unit");
        });
        $(details).find("task").each(function() {
            var $entry = $(this);
            var state = $entry.attr("state");
            var tag = $.trim($entry.text());
            html += '<li id="' + state + '">' + tag + " test " + state;
            if (results[tag]) {
                html += ": " + results[tag];
            }
            html += "</li>";
        });
        html += "</ul>";
        $("#detail").html($(html));
    }

    /*
     * Request the state again, long-polling style
     */

    $.get("/api/state?t=" + curtime, getcurstate);
}

/*
 * A little delay before starting long polling.  This way
 * Google Chrome tab icon does not keep spinning.  For more
 * info see http://bit.ly/a4x7Ct (stackoverflow.com).
 */

function getstate() {
    $.get("/api/state?t=0", getcurstate);
}

$(document).ready(function() {
    setTimeout(getstate, 100);
});
