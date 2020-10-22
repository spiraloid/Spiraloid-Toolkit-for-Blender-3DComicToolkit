(function () {
  'use strict';
  /*globals location, XMLHttpRequest, setTimeout*/
  var loc     = location;
  var host    = loc.hostname + (loc.port ? ':' + loc.port : '');
  var timeout = setTimeout;
  var ref, check, xhr, lastModified, time;
  if (loc.host === host) {
    ref = new Date().getTime();
    check = function () {
      xhr = new XMLHttpRequest();
      xhr.onload = function () {
        lastModified = this.getResponseHeader('Last-Modified');
        time = new Date(lastModified).getTime();
        if (time > ref) {
          loc.reload(true);
        } else {
          timeout(check, 1000);
        }
      };
      xhr.open('HEAD', loc.href + '?t=' + new Date().getTime(), true);
      xhr.setRequestHeader('pragma', 'no-cache');
      xhr.send();
    };
    timeout(check, 5000);
  }
}());