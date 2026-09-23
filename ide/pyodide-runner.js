/* Cat++ in-browser runner via Pyodide */
(function () {
  'use strict';
  var CDN = 'https://cdn.jsdelivr.net/pyodide/v0.26.2/full/pyodide.js';
  var FILES = ['interpreter.py', 'catpp_pycompiler.py', 'catpp_vm.py'];
  var pyodide = null;
  var loading = null;

  function inject(src) {
    return new Promise(function (res, rej) {
      var s = document.createElement('script');
      s.src = src;
      s.onload = res;
      s.onerror = function () { rej(new Error('Failed to load ' + src)); };
      document.head.appendChild(s);
    });
  }

  async function init() {
    if (pyodide) return pyodide;
    if (loading) return loading;

    loading = (async function () {
      console.log('[Cat++] step 1: load pyodide from CDN');
      await inject(CDN);
      console.log('[Cat++] step 2: init pyodide');
      pyodide = await window.loadPyodide({
        indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.26.2/full/'
      });
      console.log('[Cat++] pyodide ready, version:', pyodide.version);

      console.log('[Cat++] step 3: fetch python files');
      for (var i = 0; i < FILES.length; i++) {
        var name = FILES[i];
        try {
          var r = await fetch('py/' + name);
          if (!r.ok) {
            console.error('[Cat++] HTTP ' + r.status + ' for py/' + name);
            continue;
          }
          var code = await r.text();
          pyodide.FS.writeFile('/home/pyodide/' + name, code);
          console.log('[Cat++] wrote ' + name + ' (' + code.length + ' bytes)');
        } catch (e) {
          console.error('[Cat++] fetch ' + name + ' failed:', e);
        }
      }

      console.log('[Cat++] step 4: setup cwd + sys.path');
      pyodide.runPython("import os; os.chdir('/home/pyodide')");
      pyodide.runPython("import sys; sys.path.insert(0, '/home/pyodide')");

      console.log('[Cat++] step 5: define _catpp_run');
      try {
        pyodide.runPython([
          'import sys, io',
          '',
          'def _catpp_run(code, engine="pyc"):',
          '    old = sys.stdout',
          '    buf = io.StringIO()',
          '    sys.stdout = buf',
          '    try:',
          '        if engine == "vm":',
          '            import catpp_vm',
          '            return catpp_vm.run_catpp_vm(code)',
          '        elif engine == "interp":',
          '            import interpreter',
          '            return interpreter.run_catpp(code)',
          '        else:',
          '            import catpp_pycompiler',
          '            return catpp_pycompiler.run_catpp_py(code)',
          '    finally:',
          '        sys.stdout = old',
          '',
          'print("[Cat++/Pyodide] _catpp_run defined OK")'
        ].join('\n'));
      } catch (e) {
        console.error('[Cat++] FAILED to define _catpp_run:', e);
        throw e;
      }

      // Quick smoke test
      try {
        var test = pyodide.runPython('_catpp_run(\'meow "ok"\', "interp")');
        console.log('[Cat++] smoke test:', test);
      } catch (e) {
        console.error('[Cat++] smoke test failed:', e);
      }

      console.log('[Cat++] ready');
      return pyodide;
    })();

    return loading;
  }

  async function runCatpp(code, engine) {
    engine = engine || 'pyc';
    try {
      var py = await init();
      var result = py.runPython('_catpp_run(' + JSON.stringify(code) + ',' + JSON.stringify(engine) + ')');
      return { ok: true, output: result == null ? '' : String(result) };
    } catch (err) {
      var msg = err.message || String(err);
      if (err.type) msg = err.type + ': ' + msg;
      console.error('[Cat++] run error:', msg);
      return { ok: false, output: msg };
    }
  }

  window.runCatppBrowser = runCatpp;
  window.runCatppBrowserReady = function () {
    return init().then(function () { return true; }).catch(function (e) { console.error(e); return false; });
  };
  console.log('[Cat++] runner loaded');
})();
