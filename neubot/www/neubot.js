/*-
 * neubot/www/neubot.js
 * Copyright (c) 2010 NEXA Center for Internet & Society
 * License: GNU GPLv3
 */

function getcurstate(data) {
    var curtime = $(data).find("state").attr("t") || 0;
    var active = $.trim($(data).find("active").text());
    var current = "";
    var html = "";

    if (active == "true") {
        $("#daemon").html("<h2>Neubot is currently running.</h2>");
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
        if(current == "test" || current == "collect") {         /* XXX */
            var details = $(data).find("test");
            var name = $.trim($(details).find("name").text());
            var results = new Array();
            html = "<h2>Details on current test: ";
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
    } else {
        $("#daemon").html("<h2>Neubot is currently idle.</h2>");
        $("#state").html($(""));
    }

    $.get("/api/state?t=" + curtime, getcurstate);
}

$(document).ready(function() {
    $.get("/api/state?t=0", getcurstate);
});
