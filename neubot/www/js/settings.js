/* neubot/www/js/settings.js */
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

function settingIdSanitize(id) {
    return id.replace('.', '-');
}

function settingIdDesanitize(id) {
    return id.replace('-', '.');
}

function configError(jqXHR, textStatus, errorThrown) {
    alert(jqXHR.statusText + "\nNo setting saved");
}

function configSuccess() {
    alert("Settings successfully updated");
}

function submitConfig() {
    var myreg = /^setting_(.+)_changed$/i;
    var numchanged = 0;
    var changed = {};
    jQuery("#configdiv input[type='hidden']").each(function(index, myinput) {
        if (jQuery(myinput).val() == 1) {
            if (myreg.test(myinput.id)) {
                numchanged++;
                results = myreg.exec(myinput.id);
                changed[settingIdDesanitize(results[1])] = jQuery('#setting_' + results[1]).val();
            }
        }
    });
    if (numchanged) {
        setConfigVars(changed, configSuccess, configError);
    }
    else {
        alert("Nothing changed, so no need to save anything");
    }
    return false;
}

function changeHidden(myinput) {
    var idok = settingIdSanitize(myinput.id);
    jQuery("#" + idok + "_changed").val(1);
    return false;
}

function getConfigRow(fieldname, value) {
    value = htmlspecialchars(value, 'ENT_QUOTES');
    var fieldnameok = settingIdSanitize(fieldname);
    return "<tr><td width='50%'>" + fieldname + "</td><td width='50%'><input type='text' id='setting_" +
        fieldnameok + "' value='" + value + "' onchange='return changeHidden(this);' /><input type='hidden' value='0' id='setting_" + fieldnameok +
        "_changed' /></td></tr>";
}

jQuery(document).ready(function() {
    utils.setActiveTab("settings");

    jQuery.ajax({
        url: 'api/config',
        dataType: 'json',
        success: function(data) {
            var html = "";
            html += "<table width='100%'>";
            for (var config_var in data) {
                html += getConfigRow(config_var, data[config_var]);
            }
            html += "</table>";
            jQuery('#configdiv').html(html);
            return false;
        }
    });

    tracker = state.tracker();
    tracker.start();
});
