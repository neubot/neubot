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
    return id.replace(/\./gi, '-');
}

function settingIdDesanitize(id) {
    return id.replace(/-/gi, '.');
}

function configError(jqXHR, textStatus, errorThrown) {
    alert(jqXHR.statusText + "\nNo setting saved");
    window.location.reload();
}

function configSuccess() {
    alert("Settings successfully updated");
    window.location.reload();
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
        utils.setConfigVars(changed, configSuccess, configError);
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

function getConfigRow(fieldname, value, label, filter) {
    value = htmlspecialchars(value, 'ENT_QUOTES');
    var fieldnameok = settingIdSanitize(fieldname);

    if (filter) {
        html = "<tr><td width='20%'>" + fieldname + "</td><td width='60%'><small>" + label + "</small></td><td width='20%'><strong>" + value + "</strong></td></tr>";
    }
    else {
        html = "<tr><td width='20%'>" + fieldname + "</td><td width='60%'><small>" + label + "</small></td><td width='20%'><input type='text' id='setting_" +
            fieldnameok + "' value='" + value + "' onchange='return changeHidden(this);' /><input type='hidden' value='0' id='setting_" + fieldnameok +
            "_changed' /></td></tr>";
    }

    return html;
}

function process_state(data) {
    if (data.events.config) {
        for (c in data.events.config) {
            var myinput = '#setting_' + settingIdSanitize(c);
            // If user change the setting, maybe it is better to lock that feature (?)
            // if (jQuery(myinput + '_changed').val() == 0) {
                jQuery(myinput).val(data.events.config[c]);
            // }
        }
    }
    return false;
}

function settings_init() {
    utils.setActiveTab("settings");

    jQuery.ajax({
        url: 'api/config?labels=1',
        dataType: 'json',
        success: function(data) {
            labels = data;
            jQuery.ajax({
                url: 'api/config',
                dataType: 'json',
                success: function(data) {
                    filtered = Array();
                    filtered[0] = "agent.api";
                    filtered[1] = "version";
                    filtered[2] = "uuid";
                    filtered[3] = "agent.daemonize";

                    var html = "";
                    html += "<table width='100%' id='table_settings'>";
                    for (var config_var in labels) {
                        html += getConfigRow(config_var, data[config_var], labels[config_var], in_array(config_var, filtered));
                    }
                    html += "</table>";
                    jQuery('#configdiv').html(html);
                    jQuery('#table_settings tr:even').addClass('coloured');
                    jQuery('#table_settings tr:odd').addClass('less-coloured');
                    return false;
                }
            });
        }
    });

    tracker = state.tracker(process_state);
    tracker.start();
};

jQuery(document).ready(function() {
    i18n.translate(settings_init);
});
