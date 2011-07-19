/* neubot/www/js/log.js */
/*-
 * Copyright (c) 2011 Alessio Palmero Aprosio <alessio@apnetwork.it>,
 *  Universita' degli Studi di Milano
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

function log_init() {
    utils.setActiveTab("log");

    jQuery.ajax({
        url: 'api/log',
        dataType: 'json',
        success: function(data) {
            var html = "";

            html += '<center><table>';

            html += "<thead><tr>";
            html += "<th width='130'>Date/time</th>";
            html += "<th width='60'>Priority</th>";
            html += "<th>Description</th>";
            html += "</tr></thead>";

            html += "<tbody>";

            for (i = 0; i < data.length; i++) {
                var result = data[i];
                var bgcolor = 'transparent';
                switch (result["severity"]) {
                    case "ERROR": bgcolor = '#ff9977'; break;
                    case "WARNING": bgcolor = '#ffff55'; break;
                    case "INFO": bgcolor = '#bbffff'; break;
                }
                html += "<tr style='background-color: " + bgcolor + ";'>";
                html += "<td><small>" + utils.getTimeFromSeconds(result["timestamp"], true, true) + "</small></td>";
                html += "<td>" + result["severity"] + "</td>";
                html += "<td><small>" + result["message"] + "</small></td>";
                html += "</tr>";
            }

            html += "</tbody></table></center>";

            jQuery("#results").html(html);
            return false;
        }
    });

    tracker = state.tracker();
    tracker.start();
};

jQuery(document).ready(function() {
    i18n.translate(log_init)
});
