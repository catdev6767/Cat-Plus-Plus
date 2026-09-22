/* Cat++ in-browser runner via Pyodide */
(function () {
  'use strict';

  const PYODIDE_CDN = 'https://cdn.jsdelivr.net/pyodide/v0.26.2/full/pyodide.js';
  const PY_FILES = ['interpreter.py', 'catpp_pycompiler.py', 'catpp_vm.py'];

  let pyodide = null;
  let loading = null;

  function injectScript(src) {
    return new Promise((resolve, reject) => {
      const s = document.createElement('script');
      s.src = src;
      s.onload = resolve;
      s.onerror = () => reject(new Error('Failed to load ' + src));
      document.head.appendChild(s);
    });
  }

  async function init() {
    if (pyodide) return pyodide;
    if (loading) return loading;

    loading = (async () => {
      console.log('[Cat++/Pyodide] loading pyodide...');
      await injectScript(PYODIDE_CDN);
      pyodide = await window.loadPyodide({
        indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.26.2/full/'
      });
      console.log('[Cat++/Pyodide] pyodide loaded');

      for (const name of PY_FILES) {
        const r = await fetch('py/' + name);
        if (!r.ok) {
          console.warn('[Cat++/Pyodide] missing ' + name);
          continue;
        }
        const code = await r.text();
        pyodide.FS.writeFile('/home/pyodide/' + name, code);
        console.log('[Cat++/Pyodide] loaded ' + name);
      }

      pyodide.runPython("import os; os.chdir('/home/pyodide')");

      pyodide.runPython(`
import sys, io
sys.path.insert(0, '/home/pyodide')

def _catpp_run(code, engine='pyc'):
    old_stdout = sys.stdout
    buf = io.StringIO()
    sys.stdout = buf
    try:
        if engine == 'pyc':
            import catpp_pycompiler
            return catpp_pycompiler.run_catpp_py(code)
        elif engine == 'vm':
            import catpp_vm
            return catpp_vm.run_catpp_vm(code)
        else:
            import interpreter
            return interpreter.run_catpp(code)
    finally:
        sys.stdout = old_stdout
`);

      console.log('[Cat++/Pyodide] ready');
      return pyodide;
    })();

    return loading;
  }

  async function runCatpp(code, engine) {
    engine = engine || 'pyc';
    const py = await init();
    try {
      const result = py.runPython('_catpp_run(' + JSON.stringify(code) + ', ' + JSON.stringify(engine) + ')');
      return { ok: true, output: result || '' };
    } catch (err) {
      let msg = err.message || String(err);
      if (err.type) msg = err.type + ': ' + msg;
      return { ok: false, output: msg };
    }
  }

  window.runCatppBrowser = runCatpp;
  window.runCatppBrowserReady = () => init().then(() => true).catch(() => false);
  console.log('[Cat++/Pyodide] runner loaded');
})();
