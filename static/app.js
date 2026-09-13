/* Cat++ IDE v2.0 — app.js hoàn chỉnh */

// ============ CONSTANTS ============
var KW = ['paw','meow','purr','give','hiss','tap','sit','leap','listen','sniff',
  'swat','knead','groom','of','nod','shake','hungry','with','either','never',
  'cat','me','kin','kit','litter'];

var BI = ['tail','puff','melt','nip','bolt','kitten','lion','scratch','flop',
  'perch','say','tally','drip','collar','kits','seek','shred','weave','swap',
  'lick','hunt','stash','snatch','line','flip','head','rear','pile','walk',
  'chase','sift','curl','sway','wave','slant','grow','bound','wander','dice'];

var EXAMPLES = {};
EXAMPLES['hello.cat'] = '# Chào mừng đến Cat++\nmeow "Meow! Hello, Cat++!"\n\npaw x = 10\npaw name = "Whiskers"\n\npurr add(a, b)\n    give a + b\n\nmeow add(x, 5)\nmeow "Name: " + name\n\nsniff x > 5\n    meow "mèo lớn"\nswat\n    meow "mèo con"\n\npaw i = 1\nknead i <= 5\n    meow i\n    paw i = i + 1\n';
EXAMPLES['fizzcat.cat'] = 'purr fizzcat(n)\n    sniff n % 15 == 0\n        give "FizzCat"\n    sniff n % 3 == 0\n        give "Fizz"\n    sniff n % 5 == 0\n        give "Cat"\n    give n\n\npaw i = 1\nknead i <= 20\n    meow fizzcat(i)\n    paw i = i + 1\n';
EXAMPLES['fibonacci.cat'] = 'purr fib(n)\n    sniff n <= 1\n        give n\n    give fib(n - 1) + fib(n - 2)\n\npaw i = 0\nknead i < 20\n    meow fib(i)\n    paw i = i + 1\n';
EXAMPLES['class.cat'] = 'cat Point\n    paw x\n    paw y\n    purr new(a, b)\n        me.x = a\n        me.y = b\n    purr dist()\n        give scratch(me.x * me.x + me.y * me.y)\n\npaw p = Point(3, 4)\nmeow p.dist()\n';
EXAMPLES['kit.cat'] = 'paw double = kit(x) => x * 2\nmeow double(21)\n\npaw nums = [1, 2, 3, 4, 5]\nmeow chase(nums, kit(x) => x * x)\nmeow sift(nums, kit(x) => x % 2 == 0)\n';

// ============ STATE ============
var LANG = 'vi';
var STORAGE_PROJECTS = 'catpp:projects';
var STORAGE_ACTIVE = 'catpp:active-project';
var STORAGE_LANG = 'catpp:lang';
var STORAGE_THEME = 'catpp:theme';
var STORAGE_CAT = 'catpp:cattheme';

var projects = {};
var activeProject = 'default';
var files = {};
var openTabs = [];
var activeTab = null;
var editor = null;
var term = null;
var currentFontSize = 14;
var showMinimap = true;

// ============ i18n ============
function T(path) {
  var parts = path.split('.');
  var cur = (window.I18N && window.I18N[LANG]) || {};
  for (var i = 0; i < parts.length; i++) {
    if (cur == null) return path;
    cur = cur[parts[i]];
  }
  return cur || path;
}
function applyLang() {
  var els = document.querySelectorAll('[data-i18n]');
  for (var i = 0; i < els.length; i++) {
    els[i].textContent = T(els[i].getAttribute('data-i18n'));
  }
  var flag = document.getElementById('lang-flag');
  if (flag && window.I18N && window.I18N[LANG]) {
    flag.textContent = window.I18N[LANG].flag;
  }
}
function setLang(code) {
  LANG = code;
  try { localStorage.setItem(STORAGE_LANG, code); } catch (e) {}
  applyLang();
  if (term) term.writeln('\x1b[90mLanguage: ' + (window.I18N[code] ? window.I18N[code].name : code) + '\x1b[0m');
}

// ============ PROJECTS ============
function loadProjects() {
  try {
    var saved = JSON.parse(localStorage.getItem(STORAGE_PROJECTS) || 'null');
    if (saved && typeof saved === 'object' && Object.keys(saved).length) {
      projects = saved;
    } else {
      var oldFiles = null;
      try { oldFiles = JSON.parse(localStorage.getItem('catpp:cat2:files') || 'null'); } catch (e) {}
      if (oldFiles && Object.keys(oldFiles).length) {
        projects = { 'default': { files: oldFiles } };
      } else {
        var d = {};
        for (var k in EXAMPLES) d[k] = EXAMPLES[k];
        projects = { 'default': { files: d } };
      }
    }
    activeProject = localStorage.getItem(STORAGE_ACTIVE) || 'default';
    if (!projects[activeProject]) activeProject = Object.keys(projects)[0];
  } catch (e) {
    var d2 = {};
    for (var k2 in EXAMPLES) d2[k2] = EXAMPLES[k2];
    projects = { 'default': { files: d2 } };
    activeProject = 'default';
  }
}
function saveProjects() {
  try {
    localStorage.setItem(STORAGE_PROJECTS, JSON.stringify(projects));
    localStorage.setItem(STORAGE_ACTIVE, activeProject);
  } catch (e) {}
}
function getActiveFiles() {
  if (!projects[activeProject]) projects[activeProject] = { files: {} };
  return projects[activeProject].files;
}
function setActiveFiles(f) {
  if (!projects[activeProject]) projects[activeProject] = { files: {} };
  projects[activeProject].files = f;
  saveProjects();
}
function renderProjectSelector() {
  var el = document.getElementById('project-selector');
  if (!el) return;
  el.innerHTML = '';
  var names = Object.keys(projects).sort();
  for (var i = 0; i < names.length; i++) {
    var opt = document.createElement('option');
    opt.value = names[i];
    opt.textContent = names[i];
    if (names[i] === activeProject) opt.selected = true;
    el.appendChild(opt);
  }
}
function switchProject(name) {
  if (!projects[name]) return;
  saveFiles();
  activeProject = name;
  files = getActiveFiles();
  openTabs = [];
  activeTab = null;
  if (editor) editor.setValue('');
  saveProjects();
  renderFileTree();
  renderTabs();
  renderProjectSelector();
  var keys = Object.keys(files);
  if (keys.length) openFile(keys[0]);
}
function createProject() {
  var name = prompt('Tên dự án mới:', 'project-' + (Object.keys(projects).length + 1));
  if (!name) return;
  name = name.trim().replace(/[^a-zA-Z0-9_-]/g, '-');
  if (!name) return;
  if (projects[name]) { alert('Dự án đã tồn tại!'); return; }
  projects[name] = { files: {} };
  saveProjects();
  activeProject = name;
  files = {};
  openTabs = [];
  activeTab = null;
  files['main.cat'] = '# Dự án ' + name + '\nmeow "Xin chào từ ' + name + '!"\n';
  saveFiles();
  renderFileTree();
  renderTabs();
  renderProjectSelector();
  openFile('main.cat');
}
function renameProject() {
  var oldName = activeProject;
  var newName = prompt('Đổi tên dự án:', oldName);
  if (!newName || newName === oldName) return;
  newName = newName.trim().replace(/[^a-zA-Z0-9_-]/g, '-');
  if (!newName || projects[newName]) { alert('Tên không hợp lệ hoặc đã tồn tại'); return; }
  projects[newName] = projects[oldName];
  delete projects[oldName];
  activeProject = newName;
  saveProjects();
  renderProjectSelector();
}
function deleteProject() {
  if (Object.keys(projects).length <= 1) { alert('Không thể xóa dự án cuối cùng'); return; }
  if (!confirm('Xóa dự án "' + activeProject + '" và TẤT CẢ file?')) return;
  delete projects[activeProject];
  activeProject = Object.keys(projects)[0];
  files = getActiveFiles();
  openTabs = [];
  activeTab = null;
  if (editor) editor.setValue('');
  saveProjects();
  renderFileTree();
  renderTabs();
  renderProjectSelector();
  var keys = Object.keys(files);
  if (keys.length) openFile(keys[0]);
}

// ============ FILES ============
function loadFiles() {
  loadProjects();
  files = getActiveFiles();
}
function saveFiles() {
  setActiveFiles(files);
}
function renderFileTree() {
  var tree = document.getElementById('file-tree');
  if (!tree) return;
  tree.innerHTML = '<div class="folder">CATPP</div>';
  var names = Object.keys(files).sort();
  for (var i = 0; i < names.length; i++) {
    (function(name) {
      var div = document.createElement('div');
      div.className = 'file' + (name === activeTab ? ' active' : '');
      div.innerHTML = '<span>' + name + '</span>';
      var del = document.createElement('span');
      del.className = 'del';
      del.innerHTML = '<i class="fas fa-times"></i>';
      del.onclick = function(e) { e.stopPropagation(); deleteFile(name); };
      div.appendChild(del);
      div.onclick = function() { openFile(name); };
      tree.appendChild(div);
    })(names[i]);
  }
}
function renderTabs() {
  var el = document.getElementById('tabs');
  if (!el) return;
  el.innerHTML = '';
  for (var i = 0; i < openTabs.length; i++) {
    (function(name) {
      var div = document.createElement('div');
      div.className = 'tab' + (name === activeTab ? ' active' : '');
      div.innerHTML = '<span>' + name + '</span>';
      var x = document.createElement('span');
      x.className = 'x';
      x.innerHTML = '<i class="fas fa-times"></i>';
      x.onclick = function(e) { e.stopPropagation(); closeTab(name); };
      div.appendChild(x);
      div.onclick = function() { openFile(name); };
      el.appendChild(div);
    })(openTabs[i]);
  }
}
function openFile(name) {
  if (!editor) { setTimeout(function() { openFile(name); }, 200); return; }
  if (!(name in files)) return;
  if (openTabs.indexOf(name) === -1) openTabs.push(name);
  activeTab = name;
  editor.setValue(files[name]);
  renderTabs();
  renderFileTree();
  try { localStorage.setItem('catpp:last-file', name); } catch (e) {}
  if (editor.getModel()) {
    monaco.editor.setModelMarkers(editor.getModel(), 'catpp', []);
  }
}
function closeTab(name) {
  openTabs = openTabs.filter(function(n) { return n !== name; });
  if (activeTab === name) {
    if (openTabs.length) openFile(openTabs[openTabs.length - 1]);
    else { activeTab = null; if (editor) editor.setValue(''); }
  }
  renderTabs();
  renderFileTree();
}
function deleteFile(name) {
  if (!confirm('Xóa "' + name + '"?')) return;
  delete files[name];
  openTabs = openTabs.filter(function(n) { return n !== name; });
  saveFiles();
  if (activeTab === name) {
    if (openTabs.length) openFile(openTabs[openTabs.length - 1]);
    else { activeTab = null; if (editor) editor.setValue(''); }
  }
  renderTabs();
  renderFileTree();
}
function newFile() {
  var name = prompt('Tên file:', 'untitled' + Object.keys(files).length + '.cat');
  if (!name || files[name]) return;
  files[name] = '# File mới\nmeow "Xin chào!"\n';
  saveFiles();
  renderFileTree();
  openFile(name);
}

// ============ EXPORT / IMPORT ============
function exportProject() {
  var data = {
    version: '2.0',
    exported: new Date().toISOString(),
    project: activeProject,
    files: files
  };
  var json = JSON.stringify(data, null, 2);
  var blob = new Blob([json], { type: 'application/json' });
  var a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  var ts = new Date().toISOString().slice(0,19).replace(/[:T]/g, '-');
  a.download = 'catpp-' + activeProject + '-' + ts + '.catpp';
  a.click();
  URL.revokeObjectURL(a.href);
  if (term) term.writeln('\x1b[32m✓ Đã xuất ' + Object.keys(files).length + ' file\x1b[0m');
}
function importProject() {
  var input = document.getElementById('file-import-input');
  if (input) input.click();
}
function handleImportFile(evt) {
  var f = evt.target.files[0];
  if (!f) return;
  var reader = new FileReader();
  reader.onload = function(e) {
    try {
      var data = JSON.parse(e.target.result);
      if (!data.files) { alert('File không hợp lệ'); return; }
      var count = Object.keys(data.files).length;
      var overwrite = confirm('Nhập ' + count + ' file?\n\nOK = GHI ĐÈ (mất hết file hiện tại)\nCancel = GỘP (thêm vào)');
      if (overwrite) { files = data.files; }
      else {
        for (var k in data.files) files[k] = data.files[k];
      }
      saveFiles();
      renderFileTree();
      var keys = Object.keys(files);
      if (keys.length) openFile(keys[0]);
      if (term) term.writeln('\x1b[32m✓ Đã nhập ' + count + ' file\x1b[0m');
    } catch (err) {
      alert('Lỗi đọc file: ' + err.message);
    }
    evt.target.value = '';
  };
  reader.readAsText(f);
}

// ============ UI HELPERS ============
function openDrawer() {
  var d = document.getElementById('drawer');
  var b = document.getElementById('drawer-backdrop');
  if (d) d.classList.add('open');
  if (b) b.classList.add('open');
}
function closeDrawer() {
  var d = document.getElementById('drawer');
  var b = document.getElementById('drawer-backdrop');
  if (d) d.classList.remove('open');
  if (b) b.classList.remove('open');
}
function openModal(title, html) {
  var t = document.getElementById('modal-title');
  var b = document.getElementById('modal-body');
  var m = document.getElementById('modal-backdrop');
  if (t) t.textContent = title;
  if (b) b.innerHTML = html;
  if (m) m.classList.add('open');
  closeDrawer();
}
function closeModal() {
  var m = document.getElementById('modal-backdrop');
  if (m) m.classList.remove('open');
}

function examplesHtml() {
  var html = '<h1>' + T('modal.examples') + '</h1><p>' + T('modal.click') + '</p>';
  var names = Object.keys(EXAMPLES);
  for (var i = 0; i < names.length; i++) {
    var name = names[i];
    html += '<div style="display:flex;justify-content:space-between;align-items:center;padding:12px;border:1px solid var(--border);border-radius:4px;margin:8px 0;background:var(--bg-side)">' +
      '<b style="color:var(--accent)">' + name + '</b>' +
      '<button class="try-btn" onclick="loadExample(\'' + name + '\')">' + T('modal.open') + '</button></div>';
  }
  return html;
}
function cheatsheetHtml() {
  return '<h1>' + T('modal.cheatsheet') + '</h1>' +
    '<h2>' + T('cheat.syntax') + '</h2>' +
    '<pre><code>meow "in ra"\npaw x = 10\npurr add(a, b)\n    give a + b\n\nsniff x > 5\n    meow "lớn"\nswat\n    meow "nhỏ"\n\npaw i = 0\nknead i < 5\n    meow i\n    paw i = i + 1</code></pre>' +
    '<h2>' + T('cheat.keyword') + '</h2>' +
    '<table><tr><th>' + T('cheat.cat') + '</th><th>' + T('cheat.meaning') + '</th></tr>' +
    '<tr><td><code>meow</code></td><td>' + T('cheat.in') + '</td></tr>' +
    '<tr><td><code>paw</code></td><td>' + T('cheat.var') + '</td></tr>' +
    '<tr><td><code>purr / give</code></td><td>' + T('cheat.fn') + '</td></tr>' +
    '<tr><td><code>sniff / swat</code></td><td>' + T('cheat.if') + '</td></tr>' +
    '<tr><td><code>knead</code></td><td>' + T('cheat.while') + '</td></tr>' +
    '<tr><td><code>groom ... of</code></td><td>' + T('cheat.each') + '</td></tr>' +
    '<tr><td><code>tap / hiss</code></td><td>' + T('cheat.try') + '</td></tr>' +
    '<tr><td><code>cat / me / kin</code></td><td>' + T('cheat.oop') + '</td></tr>' +
    '</table>';
}
function shortcutsHtml() {
  return '<h1>' + T('modal.shortcuts') + '</h1><table>' +
    '<tr><th>Key</th><th>Action</th></tr>' +
    '<tr><td><code>Ctrl+Enter</code></td><td>' + T('shortcuts.run') + '</td></tr>' +
    '<tr><td><code>Ctrl+B</code></td><td>' + T('shortcuts.drawer') + '</td></tr>' +
    '<tr><td><code>Ctrl+`</code></td><td>' + T('shortcuts.term') + '</td></tr>' +
    '<tr><td><code>Ctrl+Shift+E</code></td><td>' + T('shortcuts.sidebar') + '</td></tr>' +
    '<tr><td><code>Ctrl+N</code></td><td>' + T('shortcuts.newFile') + '</td></tr>' +
    '<tr><td><code>Esc</code></td><td>' + T('shortcuts.esc') + '</td></tr>' +
    '</table>';
}
window.loadExample = function(name) {
  if (!editor || !(name in EXAMPLES)) return;
  if (!(name in files)) {
    files[name] = EXAMPLES[name];
    saveFiles();
  }
  openFile(name);
  closeModal();
  setTimeout(runCode, 300);
};
function handleMenu(name) {
  if (name === 'examples') openModal(T('modal.examples'), examplesHtml());
  else if (name === 'cheatsheet') openModal(T('modal.cheatsheet'), cheatsheetHtml());
  else if (name === 'shortcuts') openModal(T('modal.shortcuts'), shortcutsHtml());
}

// ============ THEME ============
function applyTheme(mode) {
  document.body.classList.toggle('theme-dark', mode === 'dark' && !document.body.classList.contains('cat-theme'));
  document.body.classList.toggle('theme-light', mode === 'light' && !document.body.classList.contains('cat-theme'));
  if (editor && monaco.editor.getTheme) {
    var themeName = document.body.classList.contains('cat-theme') ? 'catpp-cat' :
                    (mode === 'dark' ? 'catpp-dark' : 'catpp-light');
    monaco.editor.setTheme(themeName);
  }
  if (term) {
    if (document.body.classList.contains('cat-theme')) {
      term.options.theme = { background:'#0a0e1a', foreground:'#e2e8f0', cursor:'#f97316' };
    } else {
      term.options.theme = mode === 'dark'
        ? { background:'#1e1e1e', foreground:'#cccccc' }
        : { background:'#f8f8f8', foreground:'#333333' };
    }
  }
  try { localStorage.setItem(STORAGE_THEME, mode); } catch (e) {}
}
function toggleTheme() {
  var cur = 'dark';
  try { cur = localStorage.getItem(STORAGE_THEME) || 'dark'; } catch (e) {}
  applyTheme(cur === 'dark' ? 'light' : 'dark');
}
function applyCatTheme(on) {
  document.body.classList.toggle('cat-theme', on);
  if (on) {
    document.body.classList.remove('theme-dark');
    document.body.classList.remove('theme-light');
    if (editor) monaco.editor.setTheme('catpp-cat');
    if (term) term.options.theme = { background:'#0a0e1a', foreground:'#e2e8f0', cursor:'#f97316' };
  } else {
    var mode = 'dark';
    try { mode = localStorage.getItem(STORAGE_THEME) || 'dark'; } catch (e) {}
    applyTheme(mode);
  }
  try { localStorage.setItem(STORAGE_CAT, on ? '1' : '0'); } catch (e) {}
}
function toggleCatTheme() {
  applyCatTheme(!document.body.classList.contains('cat-theme'));
}

// ============ EDITOR ============
function initTerminal() {
  if (typeof Terminal === 'undefined') {
    console.error('xterm.js chưa load');
    return;
  }
  term = new Terminal({
    theme: { background:'#1e1e1e', foreground:'#cccccc', cursor:'#007acc' },
    fontSize: 13,
    fontFamily: 'Consolas, "Ubuntu Mono", monospace'
  });
  var el = document.getElementById('terminal');
  if (el) {
    term.open(el);
    term.writeln('\x1b[90mCat++ Terminal — Ctrl+Enter để chạy.\x1b[0m');
    term.writeln('');
  }
}

function initMonaco() {
  return new Promise(function(resolve, reject) {
    if (typeof require === 'undefined') { reject('require chưa load'); return; }
    require.config({ paths: { vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.45.0/min/vs' } });
    require(['vs/editor/editor.main'], function() {
      monaco.languages.register({ id: 'catpp' });
      monaco.languages.setLanguageConfiguration('catpp', {
        comments: { lineComment: '#' },
        brackets: [['(',')'], ['[',']'], ['{','}']],
        autoClosingPairs: [
          {open:'"',close:'"'},{open:'(',close:')'},
          {open:'[',close:']'},{open:'{',close:'}'}
        ],
        indentationRules: {
          increaseIndentPattern: /^\s*(purr|sniff|swat|knead|groom|tap|hiss|cat|litter)\b.*$/
        }
      });
      monaco.languages.setMonarchTokensProvider('catpp', {
        keywords: KW,
        builtins: BI,
        tokenizer: {
          root: [
            [/[a-zA-Z_]\w*/, { cases: {
              '@keywords': 'keyword',
              '@builtins': 'type',
              '@default': 'identifier'
            }}],
            [/\d+(\.\d+)?/, 'number'],
            [/"([^"\\]|\\.)*"/, 'string'],
            [/#.*$/, 'comment'],
            [/[+\-*\/%=<>!]+/, 'operator'],
            [/[()\[\]{},.:]/, 'delimiter']
          ]
        }
      });
      monaco.languages.registerCompletionItemProvider('catpp', {
        provideCompletionItems: function(model, position) {
          var word = model.getWordUntilPosition(position);
          var range = {
            startLineNumber: position.lineNumber,
            endLineNumber: position.lineNumber,
            startColumn: word.startColumn,
            endColumn: word.endColumn
          };
          var snippets = {
            'paw': 'paw ${1:name} = ${2:value}',
            'meow': 'meow ${1:"text"}',
            'purr': 'purr ${1:name}(${2:args})\n    ${3:give ${4:value}}',
            'give': 'give ${1:value}',
            'sniff': 'sniff ${1:condition}\n    ${2:meow "yes"}\nswat\n    ${3:meow "no"}',
            'knead': 'knead ${1:condition}\n    ${2:body}',
            'groom': 'groom ${1:item} of ${2:list}\n    ${3:meow ${1:item}}',
            'tap': 'tap\n    ${1:code}\nhiss ${2:e}\n    meow ${2:e}',
            'cat': 'cat ${1:Name}\n    paw ${2:field}\n    purr new(${3:args})\n        me.${2:field} = ${4:value}'
          };
          var suggestions = [];
          for (var k in snippets) {
            suggestions.push({
              label: k,
              kind: monaco.languages.CompletionItemKind.Snippet,
              insertText: snippets[k],
              insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
              range: range,
              documentation: 'Cat++: ' + k
            });
          }
          for (var i = 0; i < BI.length; i++) {
            suggestions.push({
              label: BI[i],
              kind: monaco.languages.CompletionItemKind.Function,
              insertText: BI[i] + '($0)',
              insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
              range: range,
              documentation: 'Cat++ builtin'
            });
          }
          return { suggestions: suggestions };
        }
      });

      monaco.editor.defineTheme('catpp-dark', {
        base: 'vs-dark',
        inherit: true,
        rules: [
          { token:'keyword', foreground:'c586c0', fontStyle:'bold' },
          { token:'string', foreground:'ce9178' },
          { token:'number', foreground:'b5cea8' },
          { token:'comment', foreground:'6a9955', fontStyle:'italic' },
          { token:'identifier', foreground:'9cdcfe' },
          { token:'type', foreground:'4ec9b0' }
        ],
        colors: { 'editor.background':'#1e1e1e' }
      });
      monaco.editor.defineTheme('catpp-light', {
        base: 'vs',
        inherit: true,
        rules: [
          { token:'keyword', foreground:'af00db', fontStyle:'bold' },
          { token:'string', foreground:'a31515' },
          { token:'number', foreground:'098658' },
          { token:'comment', foreground:'008000', fontStyle:'italic' },
          { token:'identifier', foreground:'001080' },
          { token:'type', foreground:'267f99' }
        ],
        colors: { 'editor.background':'#ffffff' }
      });
      monaco.editor.defineTheme('catpp-cat', {
        base: 'vs-dark',
        inherit: true,
        rules: [
          { token:'keyword', foreground:'f97316', fontStyle:'bold' },
          { token:'string', foreground:'fbbf24' },
          { token:'number', foreground:'22d3ee' },
          { token:'comment', foreground:'64748b', fontStyle:'italic' },
          { token:'identifier', foreground:'e2e8f0' },
          { token:'type', foreground:'4ade80' },
          { token:'operator', foreground:'f472b6' }
        ],
        colors: {
          'editor.background': '#0a0e1a',
          'editor.foreground': '#e2e8f0',
          'editorLineNumber.foreground': '#475569',
          'editorLineNumber.activeForeground': '#f97316',
          'editorCursor.foreground': '#f97316',
          'editor.selectionBackground': '#f9731666',
          'editor.lineHighlightBackground': '#0d1220'
        }
      });

      var el = document.getElementById('editor');
      if (!el) { reject('Không có #editor'); return; }
      editor = monaco.editor.create(el, {
        value: '',
        language: 'catpp',
        theme: 'catpp-dark',
        automaticLayout: true,
        fontSize: currentFontSize,
        fontFamily: 'Consolas, "Ubuntu Mono", monospace',
        minimap: { enabled: showMinimap },
        scrollBeyondLastLine: false
      });
      editor.onDidChangeCursorPosition(function(e) {
        var cp = document.getElementById('cursor-pos');
        if (cp) cp.textContent = 'Ln ' + e.position.lineNumber + ', Col ' + e.position.column;
      });
      editor.onDidChangeModelContent(function() {
        if (!activeTab) return;
        files[activeTab] = editor.getValue();
        saveFiles();
      });

      // Apply theme
      try {
        var catOn = localStorage.getItem(STORAGE_CAT) === '1';
        if (catOn) applyCatTheme(true);
        else {
          var mode = localStorage.getItem(STORAGE_THEME) || 'dark';
          applyTheme(mode);
        }
      } catch (e) {}

      // Open first file
      var keys = Object.keys(files);
      var last = null;
      try { last = localStorage.getItem('catpp:last-file'); } catch (e) {}
      openFile(last && last in files ? last : (keys[0] || 'hello.cat'));

      resolve();
    });
  });
}

function runCode() {
  if (!editor || !activeTab) return;
  if (!term) { console.error('terminal chưa khởi tạo'); return; }
  var code = editor.getValue();
  term.clear();
  term.writeln('\x1b[90m> Đang chạy ' + activeTab + '...\x1b[0m\r\n');
  var st = document.getElementById('status');
  if (st) st.textContent = 'Running...';
  if (editor.getModel()) monaco.editor.setModelMarkers(editor.getModel(), 'catpp', []);

  fetch('/api/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code: code })
  })
  .then(function(r) { return r.json(); })
  .then(function(data) {
    if (data.output) term.writeln(data.output.replace(/\n/g, '\r\n'));
    if (data.ok) {
      term.writeln('\r\n\x1b[32mOK\x1b[0m');
      if (st) st.textContent = 'Ready';
    } else {
      term.writeln('\r\n\x1b[31mERROR\x1b[0m');
      if (st) st.textContent = 'Error';
      if (data.line && editor.getModel()) {
        monaco.editor.setModelMarkers(editor.getModel(), 'catpp', [{
          startLineNumber: data.line, startColumn: 1,
          endLineNumber: data.line, endColumn: 999,
          message: data.output,
          severity: monaco.MarkerSeverity.Error
        }]);
        editor.revealLineInCenter(data.line);
      }
    }
  })
  .catch(function(e) {
    term.writeln('\x1b[31mLỗi kết nối: ' + e.message + '\x1b[0m');
  });
}

function downloadFile() {
  if (!activeTab || !editor) return;
  var blob = new Blob([editor.getValue()], { type: 'text/plain' });
  var a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = activeTab;
  a.click();
  URL.revokeObjectURL(a.href);
}
function uploadFile() {
  var input = document.getElementById('file-input');
  if (input) input.click();
}
function shareLink() {
  if (!activeTab || !editor) return;
  try {
    var enc = btoa(unescape(encodeURIComponent(editor.getValue())));
    var url = location.origin + '/#' + enc;
    if (navigator.clipboard) {
      navigator.clipboard.writeText(url).then(function() { alert('Đã copy link!'); })
        .catch(function() { prompt('Link:', url); });
    } else {
      prompt('Link:', url);
    }
  } catch (e) { alert('Không tạo được link'); }
}

// ============ BIND EVENTS ============
function bindEvents() {
  function on(id, evt, fn) {
    var el = document.getElementById(id);
    if (el) el.addEventListener(evt, fn);
  }

  on('hamburger', 'click', openDrawer);
  on('drawer-close', 'click', closeDrawer);
  on('drawer-backdrop', 'click', closeDrawer);
  on('modal-close', 'click', closeModal);
  on('modal-backdrop', 'click', function(e) {
    if (e.target === this) closeModal();
  });
  on('theme-btn', 'click', toggleTheme);
  on('zen-btn', 'click', function() { document.body.classList.toggle('zen'); });
  on('cat-btn', 'click', toggleCatTheme);
  on('lang-btn', 'click', function() { setLang(LANG === 'vi' ? 'en' : 'vi'); });
  on('run-btn', 'click', runCode);
  on('clear-btn', 'click', function() { if (term) term.clear(); });

  // Menu items
  var menuEls = document.querySelectorAll('[data-menu]');
  for (var i = 0; i < menuEls.length; i++) {
    (function(el) {
      el.addEventListener('click', function() { handleMenu(el.getAttribute('data-menu')); });
    })(menuEls[i]);
  }

  // Drawer actions
  on('act-new', 'click', newFile);
  on('act-download', 'click', downloadFile);
  on('act-upload', 'click', uploadFile);
  on('act-share', 'click', shareLink);
  on('act-export', 'click', exportProject);
  on('act-import', 'click', importProject);
  on('act-run', 'click', function() { closeDrawer(); runCode(); });
  on('act-clear', 'click', function() { closeDrawer(); if (term) term.clear(); });
  on('act-theme', 'click', function() { toggleTheme(); closeDrawer(); });
  on('act-sidebar', 'click', function() {
    var el = document.getElementById('main-body');
    if (el) el.classList.toggle('hide-sidebar');
    closeDrawer();
  });
  on('act-terminal', 'click', function() {
    var el = document.getElementById('main-col');
    if (el) el.classList.toggle('hide-panel');
    closeDrawer();
  });
  on('act-minimap', 'click', function() {
    showMinimap = !showMinimap;
    if (editor) editor.updateOptions({ minimap: { enabled: showMinimap } });
    closeDrawer();
  });

  // Project buttons
  on('project-new', 'click', function(e) { e.preventDefault(); createProject(); });
  on('project-rename', 'click', function(e) { e.preventDefault(); renameProject(); });
  on('project-delete', 'click', function(e) { e.preventDefault(); deleteProject(); });
  var sel = document.getElementById('project-selector');
  if (sel) {
    sel.addEventListener('change', function() { switchProject(this.value); });
  }

  // File input (import)
  var fi = document.getElementById('file-import-input');
  if (fi) fi.addEventListener('change', handleImportFile);

  // File input (upload)
  var fu = document.getElementById('file-input');
  if (fu) fu.addEventListener('change', function(e) {
    var file = e.target.files[0];
    if (!file) return;
    var reader = new FileReader();
    reader.onload = function() {
      var name = file.name.endsWith('.cat') ? file.name : file.name + '.cat';
      files[name] = reader.result;
      saveFiles();
      renderFileTree();
      openFile(name);
    };
    reader.readAsText(file);
    e.target.value = '';
  });

  // Keyboard
  document.addEventListener('keydown', function(e) {
    var mod = e.ctrlKey || e.metaKey;
    if (mod && e.key === 'Enter') { e.preventDefault(); runCode(); }
    else if (mod && e.key.toLowerCase() === 'b') {
      e.preventDefault();
      var d = document.getElementById('drawer');
      if (d && d.classList.contains('open')) closeDrawer(); else openDrawer();
    }
    else if (mod && e.key === '`') {
      e.preventDefault();
      var mc = document.getElementById('main-col');
      if (mc) mc.classList.toggle('hide-panel');
    }
    else if (mod && e.shiftKey && e.key.toLowerCase() === 'e') {
      e.preventDefault();
      var mb = document.getElementById('main-body');
      if (mb) mb.classList.toggle('hide-sidebar');
    }
    else if (mod && e.key.toLowerCase() === 'n') { e.preventDefault(); newFile(); }
    else if (e.key === 'Escape') {
      var m = document.getElementById('modal-backdrop');
      var d2 = document.getElementById('drawer');
      if (m && m.classList.contains('open')) closeModal();
      else if (d2 && d2.classList.contains('open')) closeDrawer();
    }
  });
}

// ============ BOOT ============
function boot() {
  console.log('[Cat++] Booting...');

  // i18n
  try {
    LANG = localStorage.getItem(STORAGE_LANG) || 'vi';
    applyLang();
  } catch (e) { console.error('i18n:', e); }

  // Cat theme
  try {
    if (localStorage.getItem(STORAGE_CAT) === '1') {
      document.body.classList.add('cat-theme');
      document.body.classList.remove('theme-dark', 'theme-light');
    }
  } catch (e) {}

  // Terminal
  try { initTerminal(); } catch (e) { console.error('initTerminal:', e); }

  // Events
  try { bindEvents(); } catch (e) { console.error('bindEvents:', e); }

  // Load projects + files
  try {
    loadFiles();
    renderProjectSelector();
    renderFileTree();
    renderTabs();
  } catch (e) { console.error('loadFiles:', e); }

  // Monaco (async)
  initMonaco().then(function() {
    console.log('[Cat++] Monaco ready');
  }).catch(function(e) {
    console.error('[Cat++] Monaco lỗi:', e);
  });

  console.log('[Cat++] Boot done');
}

// Chạy khi DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', boot);
} else {
  boot();
}
