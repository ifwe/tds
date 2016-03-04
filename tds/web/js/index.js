var ROOT_URL = "https://deploybeta.tagged.com/v1"
var COOKIES = {};

function set_cookies() {
    var all_cookies = document.cookie.split("; ");
    for (var i=0; i < all_cookies.length; i++) {
        var split = all_cookies[i].split('=');
        var key = split[0];
        var val_array = split.slice(1);
        var val = val_array.join("=");
        COOKIES[key] = val;
    }
}

function update_html(element_id, html_string) {
    if ($(element_id).html() != html_string) {
        $(element_id).html(html_string);
    }
}

function update_page(element_names, data_dict) {
    for (var i=0; i<element_names.length; i++) {
        if (data_dict.hasOwnProperty(element_names[i])) {
            update_html('#' + element_names[i], data_dict[element_names[i]]);
        }
    }
}

$.postJSON = function(url, data, callback) {
    return jQuery.ajax({
        'type': 'POST',
        'url': url,
        'contentType': 'application/json',
        'data': JSON.stringify(data),
        'dataType': 'json',
        'success': callback,
        'xhrFields': {
            withCredentials: true
        },
        'crossDomain': true
    });
};

function serialize_form(form) {
    var data = form.serializeArray();
    var json = {};
    for (i = 0; i < data.length; i++) {
        json[data[i]['name']] = data[i]['value'];
    }
    return json;
}

function get_response(url) {
    url = ROOT_URL + url;
    var obj = {};
    $.getJSON(url, function(data, textStatus, jqxhr) {
        obj['response_code'] = textStatus;
        obj['data'] = data;
    }).fail(function(jqxhr, textStatus, error) {
        obj['response_code'] = textStatus;
        obj['errors'] = error;
    });
}

function set_initial_html() {
    var valid_cookie = false;
    if ('session' in COOKIES) {
        document.session_cookie = COOKIES['session'];
        var response_code = get_response('/projects/1')['response_code'];
        if (response_code.indexOf("200") != -1) {
            valid_cookie = true;
        }
    }
    if (valid_cookie) {
        set_home_html();
    } else {
        set_login_html();
    }
}

$(document).ready(function() {
    set_cookies();
    set_initial_html();
});
