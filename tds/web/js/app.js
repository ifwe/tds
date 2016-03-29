// tds/web/js/home.js
var SEARCH_BAR_HTML = `
<div style="padding: 0px;" class="col-sm-3 col-md-4 pull-right">
  <form id="tds-search-bar" class="navbar-form" role="search"
    style="padding-left: 5px; padding-right: 5px;">
    <div class="input-group">
      <input type="search" class="form-control search-query" name="name" placeholder="Application Name">
      <span class="input-group-btn">
        <button type="submit" class="btn btn-info">
          <span class="glyphicon glyphicon-search"></span>
        </button>
      </span>
    </div> <!-- .input-group -->
  </form>
</div> <!-- .col-sm-3 -->
`

function set_home_html() {
    update_html('#tds-search-placeholder', SEARCH_BAR_HTML);

    $('#tds-search-bar').submit(function(event) {
        var search_form = $('#tds-search-bar');
        var json = serialize_form(search_form);
        tds_search('applications', json);
        event.preventDefault();
    })
}
// tds/web/js/login.js
var LOGIN_HTML = `
<div id="tds-login-form-div">
  <h1 class="tds-title">Login</h1>
  <hr class="tds-divider-line" />
  <div id="tds-alert"></div>
  <form id='tds-login-form'>
    <div class="form-group">
      <label>Username</label>
      <input name='username' id='tds-login-form-username' placeholder='Username'
        class="form-control" required>
    </div> <!-- .form-group -->
    <div class="form-group">
      <label>Password</label>
      <input name='password' id='tds-login-form-password' placeholder='Password'
        class="form-control" type='password' required>
    </div> <!-- .form-group -->
    <div class="form-group">
      <div class="text-center">
        <button type="submit" class="btn btn btn-success" style="min-width: 50%;"><span class="glyphicon glyphicon-lock"></span>Enter</button>
      </div> <!-- .text-center -->
    </div> <!-- .form-group -->
  </form>
</div> <!-- #tds-login-form-div -->
`;

function set_login_html() {
    update_html('#tds-fluid-body', LOGIN_HTML);

    $("#tds-login-form").submit(function(event) {
        var login_form = $('#tds-login-form');
        login_form.validate();
        if (login_form.valid()) {
            login(login_form);
        } else {
            update_html(
                '#tds-alert',
                '<div class="alert alert-danger alert-dismissible" role="alert" id="tds-login-error"></div>'
            );
            update_html(
                '#tds-login-error',
                '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>Required field missing.'
            )
        }
        event.preventDefault();
    });
}

function login(form) {
    var json = serialize_form(form);
    $.postJSON(ROOT_URL + '/login', json, function(data, textStatus, jqXHR) {
        alert(jqXHR.getResponseHeader('Set-Cookie'));
        set_home_html();
    }).fail(function(jqxhr, textStatus, error) {
        update_html(
            '#tds-alert',
            '<div class="alert alert-danger alert-dismissible" role="alert" id="tds-login-error"></div>'
        );
        update_html(
            '#tds-login-error',
            '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>' + error
        );
    });
}
// tds/web/js/index.js
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
