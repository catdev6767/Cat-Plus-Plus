/* Cat++ IDE — Extras (Command Palette, Search, Format, Rename) */
(function() {
  'use strict';

  function toast(msg, ms) {
    var t = document.getElementById('cat-toast');
    if (!t) {
      t = document.createElement('div');
      t.id = 'cat-toast';
      t.className = 'cat-toast';
      document.body.appendChild(t);
    }
    t.textContent = msg;
    t.classList.add('show');
    setTimeout(function() { t.classList.remove('show'); }, ms || 1800);
  }

  function getEditor() { return window.editor || null; }
  function getFiles() { return window.files || {}; }
  function getActiveTab() { return window.activeTab || null; }
  function setFiles(f) { window.files = f; if (window.saveFiles) window.saveFiles(); }
  function setActiveTab(t) { window.activeTab = t; }
  function openFile(name) {
    if (window.openFile) window.openFile(name);
  }
  function runCode() { if (window.runCode) window.runCode(); }

  // ============ 1. COMMAND PALETTE ============
  var paletteOverlay = null;
  var paletteInput = null;
  var paletteList = null;
  var currentCommands = [];
  var selectedIndex = 0;

  function getCommands() {
    return [
      { cat: 'Chạy', label: 'Chạy code', kbd: 'Ctrl+Enter', fn: runCode },
      { cat: 'Chạy', label: 'Xóa terminal', kbd: '', fn: function() {
        if (window.term) window.term.clear();
      }},
      { cat: 'File', label: 'Tạo file mới', kbd: 'Ctrl+N', fn: function() {
        if (window.newFile) window.newFile();
      }},
      { cat: 'File', label: 'Xuất dự án (.catpp)', kbd: '', fn: function() {
        if (window.exportProject) window.exportProject();
      }},
      { cat: 'File', label: 'Nhập dự án (.catpp)', kbd: '', fn: function() {
        if (window.importProject) window.importProject();
      }},
      { cat: 'File', label: 'Tải file về', kbd: '', fn: function() {
        if (window.downloadFile) window.downloadFile();
      }},
      { cat: 'File', label: 'Chia sẻ link', kbd: '', fn: function() {
        if (window.shareLink) window.shareLink();
      }},
      { cat: 'Dự án', label: 'Tạo dự án mới', kbd: '', fn: function() {
        if (window.createProject) window.createProject();
      }},
      { cat: 'Dự án', label: 'Đổi tên dự án', kbd: '', fn: function() {
        if (window.renameProject) window.renameProject();
      }},
      { cat: 'Dự án', label: 'Xóa dự án', kbd: '', fn: function() {
        if (window.deleteProject) window.deleteProject();
      }},
      { cat: 'Định dạng', label: 'Format code (căn thụt lề)', kbd: 'Ctrl+Shift+I', fn: formatCode },
      { cat: 'Định dạng', label: 'Đổi tên biến', kbd: 'F2', fn: renameSymbol },
      { cat: 'Tìm kiếm', label: 'Tìm trong toàn dự án', kbd: 'Ctrl+Shift+F', fn: openSearch },
      { cat: 'Tìm kiếm', label: 'Tìm trong file', kbd: 'Ctrl+F', fn: function() {
        var e = getEditor();
        if (e) e.getAction('actions.find').run();
      }},
      { cat: 'Xem', label: 'Đổi theme sáng/tối', kbd: '', fn: function() {
        if (window.toggleTheme) window.toggleTheme();
      }},
      { cat: 'Xem', label: 'Đổi theme mèo', kbd: '', fn: function() {
        if (window.toggleCatTheme) window.toggleCatTheme();
      }},
      { cat: 'Xem', label: 'Đổi ngôn ngữ VI/EN', kbd: '', fn: function() {
        if (window.setLang) window.setLang((window.LANG || 'vi') === 'vi' ? 'en' : 'vi');
      }},
      { cat: 'Xem', label: 'Zen mode (ẩn hết)', kbd: 'Ctrl+K Z', fn: function() {
        document.body.classList.toggle('zen');
      }},
      { cat: 'Xem', label: 'Ẩn/hiện sidebar', kbd: 'Ctrl+Shift+E', fn: function() {
        var e = document.getElementById('main-body');
        if (e) e.classList.toggle('hide-sidebar');
      }},
      { cat: 'Xem', label: 'Ẩn/hiện terminal', kbd: 'Ctrl+`', fn: function() {
        var e = document.getElementById('main-col');
        if (e) e.classList.toggle('hide-panel');
      }},
      { cat: 'Tài liệu', label: 'Mở tài liệu VI', kbd: '', fn: function() {
        window.open('/docs/vi/', '_blank');
      }},
      { cat: 'Tài liệu', label: 'Mở tài liệu EN', kbd: '', fn: function() {
        window.open('/docs/en/', '_blank');
      }},
      { cat: 'Ví dụ', label: 'Mở thư viện ví dụ', kbd: '', fn: function() {
        var el = document.querySelector('[data-menu="examples"]');
        if (el) el.click();
      }},
      { cat: 'Ví dụ', label: 'Mở cheatsheet', kbd: '', fn: function() {
        var el = document.querySelector('[data-menu="cheatsheet"]');
        if (el) el.click();
      }},
    ];
  }

  function ensurePalette() {
    if (paletteOverlay) return;
    paletteOverlay = document.createElement('div');
    paletteOverlay.className = 'cp-overlay';
    paletteOverlay.innerHTML = '<div class="cp-box"><input class="cp-input" placeholder="Gõ lệnh... (Esc để đóng)"><div class="cp-list"></div></div>';
    document.body.appendChild(paletteOverlay);
    paletteInput = paletteOverlay.querySelector('.cp-input');
    paletteList = paletteOverlay.querySelector('.cp-list');

    paletteOverlay.addEventListener('click', function(e) {
      if (e.target === paletteOverlay) closePalette();
    });
    paletteInput.addEventListener('input', function() { renderPalette(this.value); });
    paletteInput.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') { e.preventDefault(); closePalette(); }
      else if (e.key === 'Enter') {
        e.preventDefault();
        var items = paletteList.querySelectorAll('.cp-item');
        if (items[selectedIndex]) items[selectedIndex].click();
      }
      else if (e.key === 'ArrowDown') {
        e.preventDefault();
        selectedIndex = Math.min(selectedIndex + 1, currentCommands.length - 1);
        renderPalette(paletteInput.value);
      }
      else if (e.key === 'ArrowUp') {
        e.preventDefault();
        selectedIndex = Math.max(selectedIndex - 1, 0);
        renderPalette(paletteInput.value);
      }
    });
  }

  function openPalette() {
    ensurePalette();
    paletteOverlay.classList.add('open');
    paletteInput.value = '';
    selectedIndex = 0;
    renderPalette('');
    setTimeout(function() { paletteInput.focus(); }, 50);
  }
  function closePalette() {
    if (paletteOverlay) paletteOverlay.classList.remove('open');
  }

  function renderPalette(q) {
    var cmds = getCommands();
    var query = (q || '').toLowerCase().trim();
    if (query) {
      cmds = cmds.filter(function(c) {
        return c.label.toLowerCase().indexOf(query) >= 0 ||
               c.cat.toLowerCase().indexOf(query) >= 0;
      });
    }
    currentCommands = cmds;
    if (selectedIndex >= cmds.length) selectedIndex = cmds.length - 1;
    if (selectedIndex < 0) selectedIndex = 0;

    if (!cmds.length) {
      paletteList.innerHTML = '<div class="cp-empty">Không có lệnh nào khớp</div>';
      return;
    }
    var html = '';
    for (var i = 0; i < cmds.length; i++) {
      var c = cmds[i];
      html += '<div class="cp-item' + (i === selectedIndex ? ' active' : '') + '" data-idx="' + i + '">' +
        '<div><div>' + c.label + '</div><div class="cp-cat">' + c.cat + '</div></div>' +
        (c.kbd ? '<span class="cp-kbd">' + c.kbd + '</span>' : '') +
        '</div>';
    }
    paletteList.innerHTML = html;

    var items = paletteList.querySelectorAll('.cp-item');
    for (var j = 0; j < items.length; j++) {
      (function(el) {
        el.addEventListener('click', function() {
          var idx = parseInt(el.getAttribute('data-idx'), 10);
          closePalette();
          setTimeout(function() { cmds[idx].fn(); }, 50);
        });
      })(items[j]);
    }
    var active = paletteList.querySelector('.cp-item.active');
    if (active) active.scrollIntoView({ block: 'nearest' });
  }

  // ============ 2. SEARCH ============
  var searchOverlay = null;
  var searchInput = null;
  var searchList = null;
  var searchInfo = null;

  function ensureSearch() {
    if (searchOverlay) return;
    searchOverlay = document.createElement('div');
    searchOverlay.className = 'sr-overlay';
    searchOverlay.innerHTML = '<div class="sr-box">' +
      '<input class="sr-input" placeholder="Tìm trong toàn dự án... (Esc để đóng)">' +
      '<div class="sr-info"></div>' +
      '<div class="sr-list"></div>' +
      '</div>';
    document.body.appendChild(searchOverlay);
    searchInput = searchOverlay.querySelector('.sr-input');
    searchList = searchOverlay.querySelector('.sr-list');
    searchInfo = searchOverlay.querySelector('.sr-info');

    searchOverlay.addEventListener('click', function(e) {
      if (e.target === searchOverlay) closeSearch();
    });
    searchInput.addEventListener('input', function() { runSearch(this.value); });
    searchInput.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') { e.preventDefault(); closeSearch(); }
    });
  }

  function openSearch() {
    ensureSearch();
    searchOverlay.classList.add('open');
    searchInput.value = '';
    searchList.innerHTML = '';
    searchInfo.textContent = 'Gõ từ khóa để tìm...';
    setTimeout(function() { searchInput.focus(); }, 50);
  }
  function closeSearch() {
    if (searchOverlay) searchOverlay.classList.remove('open');
  }

  function escHtml(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function runSearch(q) {
    var query = (q || '').trim();
    if (!query) {
      searchList.innerHTML = '';
      searchInfo.textContent = 'Gõ từ khóa để tìm...';
      return;
    }
    var files = getFiles();
    var names = Object.keys(files).sort();
    var html = '';
    var total = 0;
    var qLow = query.toLowerCase();
    for (var i = 0; i < names.length; i++) {
      var name = names[i];
      var content = files[name] || '';
      var lines = content.split('\n');
      var fileMatches = [];
      for (var ln = 0; ln < lines.length; ln++) {
        var line = lines[ln];
        var idx = line.toLowerCase().indexOf(qLow);
        if (idx >= 0) {
          fileMatches.push({ ln: ln + 1, text: line, idx: idx });
        }
      }
      if (fileMatches.length) {
        html += '<div class="sr-file">📄 ' + escHtml(name) + ' (' + fileMatches.length + ')</div>';
        for (var k = 0; k < fileMatches.length && k < 20; k++) {
          var m = fileMatches[k];
          var before = escHtml(m.text.slice(0, m.idx));
          var match = escHtml(m.text.slice(m.idx, m.idx + query.length));
          var after = escHtml(m.text.slice(m.idx + query.length));
          html += '<div class="sr-match" data-file="' + escHtml(name) + '" data-line="' + m.ln + '">' +
            '<span class="sr-line-num">' + m.ln + '</span>' +
            '<span class="sr-line-text">' + before + '<span class="sr-highlight">' + match + '</span>' + after + '</span>' +
            '</div>';
          total++;
        }
        if (fileMatches.length > 20) {
          html += '<div class="sr-match" style="opacity:.5">... và ' + (fileMatches.length - 20) + ' kết quả nữa</div>';
        }
      }
    }
    searchList.innerHTML = html || '<div class="cp-empty">Không tìm thấy</div>';
    searchInfo.textContent = 'Tìm thấy ' + total + ' kết quả trong ' + names.length + ' file';

    var matches = searchList.querySelectorAll('.sr-match');
    for (var j = 0; j < matches.length; j++) {
      (function(el) {
        el.addEventListener('click', function() {
          var f = el.getAttribute('data-file');
          var l = parseInt(el.getAttribute('data-line'), 10);
          closeSearch();
          jumpTo(f, l);
        });
      })(matches[j]);
    }
  }

  function jumpTo(name, line) {
    openFile(name);
    setTimeout(function() {
      var e = getEditor();
      if (e) {
        e.revealLineInCenter(line);
        e.setPosition({ lineNumber: line, column: 1 });
        e.focus();
      }
    }, 200);
  }

  // ============ 3. FORMAT CODE ============
  function formatCode() {
    var e = getEditor();
    if (!e) { toast('Không có editor'); return; }
    var code = e.getValue();
    var lines = code.split('\n');
    var out = [];
    var indentLevel = 0;
    var INDENT = '    '; // 4 spaces

    var increaseRe = /^\s*(purr|sniff|swat|knead|groom|tap|hiss|cat|litter)\b.*$/;

    for (var i = 0; i < lines.length; i++) {
      var raw = lines[i];
      var trimmed = raw.replace(/^\s+/, '');
      if (!trimmed) { out.push(''); continue; }

      // Nếu là swat/hiss → giảm 1 cấp trước khi ghi
      if (/^(swat|hiss)\b/.test(trimmed)) {
        indentLevel = Math.max(0, indentLevel - 1);
      }

      out.push(INDENT.repeat(indentLevel) + trimmed);

      // Nếu dòng này mở block → tăng 1 cấp
      if (increaseRe.test(trimmed) && !/^(swat|hiss)\b/.test(trimmed)) {
        // Nhưng nếu sau đó là swat/hiss ngay → cấp sẽ giảm
        indentLevel++;
      }
    }

    var formatted = out.join('\n');
    if (formatted === code) {
      toast('Code đã được format sẵn');
      return;
    }
    e.setValue(formatted);
    toast('✓ Đã format code');
  }

  // ============ 4. RENAME SYMBOL ============
  function renameSymbol() {
    var e = getEditor();
    if (!e) { toast('Không có editor'); return; }
    var sel = e.getSelection();
    var model = e.getModel();
    var word = model.getValueInRange(sel).trim();
    if (!word) {
      var wordAtPos = model.getWordAtPosition(e.getPosition());
      if (wordAtPos) word = wordAtPos.word;
    }
    if (!word) { toast('Đặt con trỏ vào biến để đổi tên'); return; }

    var newName = prompt('Đổi tên "' + word + '" thành:', word);
    if (!newName || newName === word) return;
    if (!/^[a-zA-Z_]\w*$/.test(newName)) {
      toast('Tên không hợp lệ');
      return;
    }

    // Chỉ đổi trong file hiện tại
    var content = model.getValue();
    var re = new RegExp('\\b' + word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b', 'g');
    var count = (content.match(re) || []).length;
    if (count === 0) { toast('Không tìm thấy'); return; }
    if (!confirm('Đổi ' + count + ' chỗ trong file này?')) return;

    var newContent = content.replace(re, newName);
    e.setValue(newContent);
    toast('✓ Đã đổi ' + count + ' chỗ');
  }

  // ============ KEYBOARD SHORTCUTS ============
  document.addEventListener('keydown', function(e) {
    var mod = e.ctrlKey || e.metaKey;
    if (!mod) {
      if (e.key === 'F2') { e.preventDefault(); renameSymbol(); }
      return;
    }
    // Ctrl+Shift+P
    if (e.shiftKey && e.key.toLowerCase() === 'p') {
      e.preventDefault();
      openPalette();
      return;
    }
    // Ctrl+Shift+F
    if (e.shiftKey && e.key.toLowerCase() === 'f') {
      e.preventDefault();
      openSearch();
      return;
    }
    // Ctrl+Shift+I
    if (e.shiftKey && e.key.toLowerCase() === 'i') {
      e.preventDefault();
      formatCode();
      return;
    }
  });

  // Expose để dùng từ console
  window.catExtras = {
    palette: openPalette,
    search: openSearch,
    format: formatCode,
    rename: renameSymbol,
    toast: toast
  };

  // Thêm nút vào drawer (nếu có)
  document.addEventListener('DOMContentLoaded', function() {
    var drawer = document.getElementById('drawer-body');
    if (drawer && !document.getElementById('extras-section')) {
      var sec = document.createElement('div');
      sec.id = 'extras-section';
      sec.className = 'drawer-section';
      sec.innerHTML = '<div class="drawer-section-title">Nâng cao</div>' +
        '<a class="drawer-item" id="ext-palette"><i class="fas fa-terminal"></i> Command Palette (Ctrl+Shift+P)</a>' +
        '<a class="drawer-item" id="ext-search"><i class="fas fa-search"></i> Tìm toàn dự án (Ctrl+Shift+F)</a>' +
        '<a class="drawer-item" id="ext-format"><i class="fas fa-magic"></i> Format code (Ctrl+Shift+I)</a>' +
        '<a class="drawer-item" id="ext-rename"><i class="fas fa-i-cursor"></i> Đổi tên biến (F2)</a>';
      drawer.appendChild(sec);
      document.getElementById('ext-palette').addEventListener('click', function() {
        if (window.closeDrawer) window.closeDrawer();
        openPalette();
      });
      document.getElementById('ext-search').addEventListener('click', function() {
        if (window.closeDrawer) window.closeDrawer();
        openSearch();
      });
      document.getElementById('ext-format').addEventListener('click', function() {
        if (window.closeDrawer) window.closeDrawer();
        formatCode();
      });
      document.getElementById('ext-rename').addEventListener('click', function() {
        if (window.closeDrawer) window.closeDrawer();
        renameSymbol();
      });
    }
  });

  console.log('[Cat++] Extras loaded — Ctrl+Shift+P để mở Command Palette');
})();
