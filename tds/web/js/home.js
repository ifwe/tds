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
