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
