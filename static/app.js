var _cachedPublicUrl = null;
var _publicUrlFetched = false;

function getPublicUrl(callback) {
  if (_publicUrlFetched) {
    callback(_cachedPublicUrl);
    return;
  }
  var host = location.hostname;
  var isLocal = (host === 'localhost' || host === '127.0.0.1' ||
                 host === '0.0.0.0' || host === '' ||
                 host.startsWith('192.168.') || host.startsWith('10.') ||
                 host.startsWith('172.'));
  if (!isLocal) {
    _cachedPublicUrl = location.origin;
    _publicUrlFetched = true;
    callback(_cachedPublicUrl);
    return;
  }
  fetch('/api/public-url').then(function(r){ return r.json(); }).then(function(d){
    _cachedPublicUrl = d.url || null;
    _publicUrlFetched = true;
    callback(_cachedPublicUrl);
  }).catch(function(){
    _cachedPublicUrl = null;
    _publicUrlFetched = true;
    callback(null);
  });
}

function shareLink() {
  if (!activeTab || !editor) return;
  try {
    var enc = btoa(unescape(encodeURIComponent(editor.getValue())));
    getPublicUrl(function(publicUrl) {
      var base = publicUrl || location.origin;
      var url = base.replace(/\/+$/, '') + '/ide/#' + enc;
      var note = '';
      if (!publicUrl) {
        note = '\n\n⚠ No public tunnel.\n' +
               'This link works only on your machine.\n\n' +
               'To share with others:\n' +
               '  cd ~/catpp && ./share.sh';
      } else {
        note = '\n\n✓ Public link — anyone can open.';
      }
      if (navigator.clipboard) {
        navigator.clipboard.writeText(url).then(function(){
          alert('Copied link:\n\n' + url + note);
        }).catch(function(){
          prompt('Link (Ctrl+C to copy):', url);
        });
      } else {
        prompt('Link (Ctrl+C to copy):', url);
      }
    });
  } catch (e) {
    alert('Error creating link: ' + e.message);
  }
}
/* Cat++ IDE v2.0 — complete app.js */
