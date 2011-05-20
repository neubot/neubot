/* neubot/www/js/contrib.js */
/*-
 * Copyright (c) individual contributors.
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

 function htmlspecialchars (string, quote_style, charset, double_encode) {
     // http://kevin.vanzonneveld.net
     // +   original by: Mirek Slugen
     // +   improved by: Kevin van Zonneveld (http://kevin.vanzonneveld.net)
     // +   bugfixed by: Nathan
     // +   bugfixed by: Arno
     // +    revised by: Kevin van Zonneveld (http://kevin.vanzonneveld.net)
     // +    bugfixed by: Brett Zamir (http://brett-zamir.me)
     // +      input by: Ratheous
     // +      input by: Mailfaker (http://www.weedem.fr/)
     // +      reimplemented by: Brett Zamir (http://brett-zamir.me)
     // +      input by: felix
     // +    bugfixed by: Brett Zamir (http://brett-zamir.me)
     // %        note 1: charset argument not supported
     // *     example 1: htmlspecialchars("<a href='test'>Test</a>", 'ENT_QUOTES');
     // *     returns 1: '&lt;a href=&#039;test&#039;&gt;Test&lt;/a&gt;'
     // *     example 2: htmlspecialchars("ab\"c'd", ['ENT_NOQUOTES', 'ENT_QUOTES']);
     // *     returns 2: 'ab"c&#039;d'
     // *     example 3: htmlspecialchars("my "&entity;" is still here", null, null, false);
     // *     returns 3: 'my &quot;&entity;&quot; is still here'
     var optTemp = 0,
         i = 0,
         noquotes = false;
     if (typeof quote_style === 'undefined' || quote_style === null) {
         quote_style = 2;
     }
     string = string.toString();
     if (double_encode !== false) { // Put this first to avoid double-encoding
         string = string.replace(/&/g, '&amp;');
     }
     string = string.replace(/</g, '&lt;').replace(/>/g, '&gt;');

     var OPTS = {
         'ENT_NOQUOTES': 0,
         'ENT_HTML_QUOTE_SINGLE': 1,
         'ENT_HTML_QUOTE_DOUBLE': 2,
         'ENT_COMPAT': 2,
         'ENT_QUOTES': 3,
         'ENT_IGNORE': 4
     };
     if (quote_style === 0) {
         noquotes = true;
     }
     if (typeof quote_style !== 'number') { // Allow for a single string or an array of string flags
         quote_style = [].concat(quote_style);
         for (i = 0; i < quote_style.length; i++) {
             // Resolve string input to bitwise e.g. 'ENT_IGNORE' becomes 4
             if (OPTS[quote_style[i]] === 0) {
                 noquotes = true;
             }
             else if (OPTS[quote_style[i]]) {
                 optTemp = optTemp | OPTS[quote_style[i]];
             }
         }
         quote_style = optTemp;
     }
     if (quote_style & OPTS.ENT_HTML_QUOTE_SINGLE) {
         string = string.replace(/'/g, '&#039;');
     }
     if (!noquotes) {
         string = string.replace(/"/g, '&quot;');
     }

     return string;
 }

/* !No description available for echo. @php.js developers: Please update the function summary text file.
 *
 * version: 1102.614
 * discuss at: http://phpjs.org/functions/echo
 * +   original by: Philip Peterson
 * +   improved by: echo is bad
 * +   improved by: Nate
 * +    revised by: Der Simon (http://innerdom.sourceforge.net/)
 * +   improved by: Brett Zamir (http://brett-zamir.me)
 * +   bugfixed by: Eugene Bulkin (http://doubleaw.com/)
 * +   input by: JB
 * +   improved by: Brett Zamir (http://brett-zamir.me)
 * +   bugfixed by: Brett Zamir (http://brett-zamir.me)
 * +   bugfixed by: Brett Zamir (http://brett-zamir.me)
 * +   bugfixed by: EdorFaus
 * +   improved by: Brett Zamir (http://brett-zamir.me)
 * %        note 1: If browsers start to support DOM Level 3 Load and Save (parsing/serializing),
 * %        note 1: we wouldn't need any such long code (even most of the code below). See
 * %        note 1: link below for a cross-browser implementation in JavaScript. HTML5 might
 * %        note 1: possibly support DOMParser, but that is not presently a standard.
 * %        note 2: Although innerHTML is widely used and may become standard as of HTML5, it is also not ideal for
 * %        note 2: use with a temporary holder before appending to the DOM (as is our last resort below),
 * %        note 2: since it may not work in an XML context
 * %        note 3: Using innerHTML to directly add to the BODY is very dangerous because it will
 * %        note 3: break all pre-existing references to HTMLElements.
 * Fix: This function really needs to allow non-XHTML input (unless in true XHTML mode) as in jQuery
 */
function echo () {
 var arg = '',
     argc = arguments.length,
     argv = arguments,
     i = 0,
     holder, win = this.window,
     d = win.document,
     ns_xhtml = 'http://www.w3.org/1999/xhtml',
     ns_xul = 'http://www.mozilla.org/keymaster/gatekeeper/there.is.only.xul'; // If we're in a XUL context
 var stringToDOM = function (str, parent, ns, container) {
     var extraNSs = '';
     if (ns === ns_xul) {
         extraNSs = ' xmlns:html="' + ns_xhtml + '"';
     }
     var stringContainer = '<' + container + ' xmlns="' + ns + '"' + extraNSs + '>' + str + '</' + container + '>';
     var dils = win.DOMImplementationLS,
         dp = win.DOMParser,
         ax = win.ActiveXObject;
     if (dils && dils.createLSInput && dils.createLSParser) {
         // Follows the DOM 3 Load and Save standard, but not
         // implemented in browsers at present; HTML5 is to standardize on innerHTML, but not for XML (though
         // possibly will also standardize with DOMParser); in the meantime, to ensure fullest browser support, could
         // attach http://svn2.assembla.com/svn/brettz9/DOMToString/DOM3.js (see http://svn2.assembla.com/svn/brettz9/DOMToString/DOM3.xhtml for a simple test file)
         var lsInput = dils.createLSInput();
         // If we're in XHTML, we'll try to allow the XHTML namespace to be available by default
         lsInput.stringData = stringContainer;
         var lsParser = dils.createLSParser(1, null); // synchronous, no schema type
         return lsParser.parse(lsInput).firstChild;
     } else if (dp) {
         // If we're in XHTML, we'll try to allow the XHTML namespace to be available by default
         try {
             var fc = new dp().parseFromString(stringContainer, 'text/xml');
             if (fc && fc.documentElement && fc.documentElement.localName !== 'parsererror' && fc.documentElement.namespaceURI !== 'http://www.mozilla.org/newlayout/xml/parsererror.xml') {
                 return fc.documentElement.firstChild;
             }
             // If there's a parsing error, we just continue on
         } catch (e) {
             // If there's a parsing error, we just continue on
         }
     } else if (ax) { // We don't bother with a holder in Explorer as it doesn't support namespaces
         var axo = new ax('MSXML2.DOMDocument');
         axo.loadXML(str);
         return axo.documentElement;
     }
/*else if (win.XMLHttpRequest) { // Supposed to work in older Safari
         var req = new win.XMLHttpRequest;
         req.open('GET', 'data:application/xml;charset=utf-8,'+encodeURIComponent(str), false);
         if (req.overrideMimeType) {
             req.overrideMimeType('application/xml');
         }
         req.send(null);
         return req.responseXML;
     }*/
     // Document fragment did not work with innerHTML, so we create a temporary element holder
     // If we're in XHTML, we'll try to allow the XHTML namespace to be available by default
     //if (d.createElementNS && (d.contentType && d.contentType !== 'text/html')) { // Don't create namespaced elements if we're being served as HTML (currently only Mozilla supports this detection in true XHTML-supporting browsers, but Safari and Opera should work with the above DOMParser anyways, and IE doesn't support createElementNS anyways)
     if (d.createElementNS && // Browser supports the method
     (d.documentElement.namespaceURI || // We can use if the document is using a namespace
     d.documentElement.nodeName.toLowerCase() !== 'html' || // We know it's not HTML4 or less, if the tag is not HTML (even if the root namespace is null)
     (d.contentType && d.contentType !== 'text/html') // We know it's not regular HTML4 or less if this is Mozilla (only browser supporting the attribute) and the content type is something other than text/html; other HTML5 roots (like svg) still have a namespace
     )) { // Don't create namespaced elements if we're being served as HTML (currently only Mozilla supports this detection in true XHTML-supporting browsers, but Safari and Opera should work with the above DOMParser anyways, and IE doesn't support createElementNS anyways); last test is for the sake of being in a pure XML document
         holder = d.createElementNS(ns, container);
     } else {
         holder = d.createElement(container); // Document fragment did not work with innerHTML
     }
     holder.innerHTML = str;
     while (holder.firstChild) {
         parent.appendChild(holder.firstChild);
     }
     return false;
     // throw 'Your browser does not support DOM parsing as required by echo()';
 };


 var ieFix = function (node) {
     if (node.nodeType === 1) {
         var newNode = d.createElement(node.nodeName);
         var i, len;
         if (node.attributes && node.attributes.length > 0) {
             for (i = 0, len = node.attributes.length; i < len; i++) {
                 newNode.setAttribute(node.attributes[i].nodeName, node.getAttribute(node.attributes[i].nodeName));
             }
         }
         if (node.childNodes && node.childNodes.length > 0) {
             for (i = 0, len = node.childNodes.length; i < len; i++) {
                 newNode.appendChild(ieFix(node.childNodes[i]));
             }
         }
         return newNode;
     } else {
         return d.createTextNode(node.nodeValue);
     }
 };

 var replacer = function (s, m1, m2) {
     // We assume for now that embedded variables do not have dollar sign; to add a dollar sign, you currently must use {$$var} (We might change this, however.)
     // Doesn't cover all cases yet: see http://php.net/manual/en/language.types.string.php#language.types.string.syntax.double
     if (m1 !== '\\') {
         return m1 + eval(m2);
     } else {
         return s;
     }
 };

 this.php_js = this.php_js || {};
 var phpjs = this.php_js,
     ini = phpjs.ini,
     obs = phpjs.obs;
 for (i = 0; i < argc; i++) {
     arg = argv[i];
     if (ini && ini['phpjs.echo_embedded_vars']) {
         arg = arg.replace(/(.?)\{?\$(\w*?\}|\w*)/g, replacer);
     }

     if (!phpjs.flushing && obs && obs.length) { // If flushing we output, but otherwise presence of a buffer means caching output
         obs[obs.length - 1].buffer += arg;
         continue;
     }

     if (d.appendChild) {
         if (d.body) {
             if (win.navigator.appName === 'Microsoft Internet Explorer') { // We unfortunately cannot use feature detection, since this is an IE bug with cloneNode nodes being appended
                 d.body.appendChild(stringToDOM(ieFix(arg)));
             } else {
                 var unappendedLeft = stringToDOM(arg, d.body, ns_xhtml, 'div').cloneNode(true); // We will not actually append the div tag (just using for providing XHTML namespace by default)
                 if (unappendedLeft) {
                     d.body.appendChild(unappendedLeft);
                 }
             }
         } else {
             d.documentElement.appendChild(stringToDOM(arg, d.documentElement, ns_xul, 'description')); // We will not actually append the description tag (just using for providing XUL namespace by default)
         }
     } else if (d.write) {
         d.write(arg);
     }
/* else { // This could recurse if we ever add print!
         print(arg);
     }*/
 }
}

/* Checks if the given value exists in the array
 * version: 1102.614
 * discuss at: http://phpjs.org/functions/in_array
 * +   original by: Kevin van Zonneveld (http://kevin.vanzonneveld.net)
 * +   improved by: vlado houba
 * +   input by: Billy
 * +   bugfixed by: Brett Zamir (http://brett-zamir.me)
 */
function in_array (needle, haystack, argStrict) {
    var key = '',
        strict = !! argStrict;
    if (strict) {
        for (key in haystack) {
            if (haystack[key] === needle) {
                return true;
            }
        }
    } else {
        for (key in haystack) {
            if (haystack[key] == needle) {
                return true;
            }
        }
    }
    return false;
}

/* Prints out or returns information about the specified variable
 * version: 1102.614
 * discuss at: http://phpjs.org/functions/print_r
 * +   original by: Michael White (http://getsprink.com)
 * +   improved by: Ben Bryan
 * +      input by: Brett Zamir (http://brett-zamir.me)
 * +      improved by: Brett Zamir (http://brett-zamir.me)
 * +   improved by: Kevin van Zonneveld (http://kevin.vanzonneveld.net)
 * -    depends on: echo
 */
function print_r (array, return_val) {
    var output = "",
        pad_char = " ",
        pad_val = 4,
        d = this.window.document;
    var getFuncName = function (fn) {
        var name = (/\W*function\s+([\w\$]+)\s*\(/).exec(fn);
        if (!name) {
            return '(Anonymous)';
        }
        return name[1];
    };

    var repeat_char = function (len, pad_char) {
        var str = "";
        for (var i = 0; i < len; i++) {
            str += pad_char;
        }
        return str;
    };

    var formatArray = function (obj, cur_depth, pad_val, pad_char) {
        if (cur_depth > 0) {
            cur_depth++;
        }

        var base_pad = repeat_char(pad_val * cur_depth, pad_char);
        var thick_pad = repeat_char(pad_val * (cur_depth + 1), pad_char);
        var str = "";

        if (typeof obj === 'object' && obj !== null && obj.constructor && getFuncName(obj.constructor) !== 'PHPJS_Resource') {
            str += "Array\n" + base_pad + "(\n";
            for (var key in obj) {
                if (obj[key] instanceof Array) {
                    str += thick_pad + "[" + key + "] => " + formatArray(obj[key], cur_depth + 1, pad_val, pad_char);
                } else {
                    str += thick_pad + "[" + key + "] => " + obj[key] + "\n";
                }
            }
            str += base_pad + ")\n";
        } else if (obj === null || obj === undefined) {
            str = '';
        } else { // for our "resource" class
            str = obj.toString();
        }

        return str;
    };

    output = formatArray(array, 0, pad_val, pad_char);

    if (return_val !== true) {
        if (d.body) {
            this.echo(output);
        } else {
            try {
                d = XULDocument; // We're in XUL, so appending as plain text won't work; trigger an error out of XUL
                this.echo('<pre xmlns="http://www.w3.org/1999/xhtml" style="white-space:pre;">' + output + '</pre>');
            } catch (e) {
                this.echo(output); // Outputting as plain text may work in some plain XML
            }
        }
        return true;
    } else {
        return output;
    }
}