/* Cat++ Learn Mode — bài tập tương tác */
(function() {
  'use strict';

  var STORAGE = 'catpp:learn:progress';

  var LESSONS = [
    { id: 'l01', title: 'In ra màn hình', cat: 'Cơ bản',
      desc: 'Dùng <code>meow</code> để in ra dòng chữ <code>Hello, Cat++!</code>',
      starter: '# Viết code ở đây\n',
      expected: 'Hello, Cat++!',
      hint: 'meow "Hello, Cat++!"' },

    { id: 'l02', title: 'Biến và số', cat: 'Cơ bản',
      desc: 'Khai báo <code>x = 10</code> và <code>y = 20</code>, in ra tổng của chúng.',
      starter: '# Khai báo x và y\n# In tổng\n',
      expected: '30',
      hint: 'paw x = 10\npaw y = 20\nmeow x + y' },

    { id: 'l03', title: 'Nối chuỗi', cat: 'Cơ bản',
      desc: 'Khai báo <code>name = "Tom"</code>, in ra <code>Xin chào, Tom!</code>',
      starter: 'paw name = "Tom"\n',
      expected: 'Xin chào, Tom!',
      hint: 'meow "Xin chào, " + name + "!"' },

    { id: 'l04', title: 'Điều kiện', cat: 'Điều khiển',
      desc: 'Cho <code>x = 8</code>. Nếu x chẵn in <code>chan</code>, ngược lại in <code>le</code>.',
      starter: 'paw x = 8\n',
      expected: 'chan',
      hint: 'sniff x % 2 == 0\n    meow "chan"\nswat\n    meow "le"' },

    { id: 'l05', title: 'Vòng lặp', cat: 'Điều khiển',
      desc: 'In các số từ 1 đến 5, mỗi số một dòng.',
      starter: 'paw i = 1\n',
      expected: '1\n2\n3\n4\n5',
      hint: 'knead i <= 5\n    meow i\n    i++' },

    { id: 'l06', title: 'Hàm', cat: 'Hàm',
      desc: 'Viết hàm <code>double(x)</code> trả về <code>x * 2</code>. In kết quả <code>double(21)</code>.',
      starter: 'purr double(x)\n    # viết code\n',
      expected: '42',
      hint: 'purr double(x)\n    give x * 2\nmeow double(21)' },

    { id: 'l07', title: 'Đệ quy', cat: 'Hàm',
      desc: 'Tính giai thừa <code>5!</code> = 120 bằng đệ quy.',
      starter: 'purr fact(n)\n    # viết code\n',
      expected: '120',
      hint: 'sniff n <= 1\n    give 1\ngive n * fact(n - 1)' },

    { id: 'l08', title: 'Danh sách', cat: 'Cấu trúc',
      desc: 'Tính tổng danh sách <code>[10, 20, 30, 40]</code>.',
      starter: 'paw arr = [10, 20, 30, 40]\n',
      expected: '100',
      hint: 'meow pile(arr)' },

    { id: 'l09', title: 'Chuỗi', cat: 'Cấu trúc',
      desc: 'In <code>"hello"</code> chuyển sang chữ HOA.',
      starter: '# Viết code\n',
      expected: 'HELLO',
      hint: 'meow "hello".upper()' },

    { id: 'l10', title: 'Class', cat: 'OOP',
      desc: 'Viết class <code>Point</code> với 2 trường <code>x</code>, <code>y</code>. Tạo <code>Point(3, 4)</code> và in <code>x</code>.',
      starter: 'cat Point\n    paw x\n    paw y\n    # viết new\n',
      expected: '3',
      hint: 'purr new(a, b)\n    me.x = a\n    me.y = b\npaw p = Point(3, 4)\nmeow p.x' }
  ];

  var state = { idx: 0, done: {} };

  function loadProgress() {
    try {
      var saved = JSON.parse(localStorage.getItem(STORAGE) || '{}');
      if (saved && typeof saved === 'object') state.done = saved;
    } catch (e) {}
  }
  function saveProgress() {
    try { localStorage.setItem(STORAGE, JSON.stringify(state.done)); } catch (e) {}
  }

  var overlay = null;

  function ensureUI() {
    if (overlay) return;
    overlay = document.createElement('div');
    overlay.className = 'ln-overlay';
    overlay.innerHTML =
      '<div class="ln-wrap">' +
        '<div class="ln-header">' +
          '<h2>🐱 Học Cat++</h2>' +
          '<div class="ln-progress" id="ln-progress"></div>' +
          '<button class="ln-close" id="ln-close">Đóng (Esc)</button>' +
        '</div>' +
        '<div class="ln-body">' +
          '<div class="ln-sidebar" id="ln-sidebar"></div>' +
          '<div class="ln-main">' +
            '<div class="ln-task" id="ln-task"></div>' +
            '<div class="ln-editor">' +
              '<div class="ln-editor-head">' +
                '<span>Editor</span>' +
                '<button class="ln-btn" id="ln-check"><i class="fas fa-play"></i> Chạy & Kiểm tra</button>' +
                '<button class="ln-btn secondary" id="ln-hint">💡 Gợi ý</button>' +
                '<button class="ln-btn secondary" id="ln-reset">↺ Reset</button>' +
                '<button class="ln-btn secondary" id="ln-next" style="margin-left:auto">Bài tiếp →</button>' +
              '</div>' +
              '<textarea class="ln-textarea" id="ln-textarea" spellcheck="false"></textarea>' +
              '<div class="ln-output" id="ln-output">Nhấn ▶ Chạy & Kiểm tra để xem kết quả...</div>' +
            '</div>' +
          '</div>' +
        '</div>' +
      '</div>';
    document.body.appendChild(overlay);

    overlay.addEventListener('click', function(e) { if (e.target === overlay) close(); });
    document.getElementById('ln-close').addEventListener('click', close);
    document.getElementById('ln-check').addEventListener('click', check);
    document.getElementById('ln-hint').addEventListener('click', toggleHint);
    document.getElementById('ln-reset').addEventListener('click', reset);
    document.getElementById('ln-next').addEventListener('click', next);

    document.addEventListener('keydown', function(e) {
      if (!overlay.classList.contains('open')) return;
      if (e.key === 'Escape') close();
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') { e.preventDefault(); check(); }
    });
  }

  function renderSidebar() {
    var sb = document.getElementById('ln-sidebar');
    var cats = {};
    LESSONS.forEach(function(l) {
      if (!cats[l.cat]) cats[l.cat] = [];
      cats[l.cat].push(l);
    });
    var html = '';
    Object.keys(cats).forEach(function(cat) {
      html += '<div style="padding:8px 20px 4px;font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#888">' + cat + '</div>';
      cats[cat].forEach(function(l) {
        var idx = LESSONS.indexOf(l);
        var done = state.done[l.id];
        html += '<div class="ln-item' + (idx === state.idx ? ' active' : '') + (done ? ' done' : '') + '" data-idx="' + idx + '">' +
          '<div class="ln-num">' + (idx + 1) + '</div>' +
          '<div>' + l.title + '</div>' +
          '<span class="ln-check">' + (done ? '✓' : '') + '</span>' +
        '</div>';
      });
    });
    sb.innerHTML = html;
    var items = sb.querySelectorAll('.ln-item');
    for (var i = 0; i < items.length; i++) {
      (function(el) {
        el.addEventListener('click', function() {
          state.idx = parseInt(el.getAttribute('data-idx'), 10);
          render();
        });
      })(items[i]);
    }
    var doneCount = Object.keys(state.done).length;
    document.getElementById('ln-progress').textContent = doneCount + '/' + LESSONS.length + ' bài';
  }

  function render() {
    var l = LESSONS[state.idx];
    document.getElementById('ln-task').innerHTML =
      '<h3>' + l.title + '</h3>' +
      '<p>' + l.desc + '</p>' +
      '<div class="ln-hint" id="ln-hint-box">💡 <b>Gợi ý:</b> <code>' + l.hint.replace(/\n/g, ' ⏎ ') + '</code></div>';
    var ta = document.getElementById('ln-textarea');
    if (ta.dataset.lesson !== l.id) {
      ta.value = l.starter;
      ta.dataset.lesson = l.id;
    }
    document.getElementById('ln-output').textContent = 'Nhấn ▶ Chạy & Kiểm tra...';
    document.getElementById('ln-output').className = 'ln-output';
    renderSidebar();
  }

  function toggleHint() {
    var h = document.getElementById('ln-hint-box');
    if (h) h.classList.toggle('show');
  }

  function reset() {
    var l = LESSONS[state.idx];
    var ta = document.getElementById('ln-textarea');
    ta.value = l.starter;
    ta.dataset.lesson = l.id;
    document.getElementById('ln-output').textContent = 'Nhấn ▶ Chạy & Kiểm tra...';
    document.getElementById('ln-output').className = 'ln-output';
  }

  function next() {
    if (state.idx < LESSONS.length - 1) {
      state.idx++;
      render();
    }
  }

  function check() {
    var l = LESSONS[state.idx];
    var code = document.getElementById('ln-textarea').value;
    var out = document.getElementById('ln-output');
    out.className = 'ln-output';
    out.innerHTML = '<span class="ln-status">⏳ Đang chạy...</span>';

    fetch('/api/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: code })
    }).then(function(r) { return r.json(); }).then(function(data) {
      var got = (data.output || '').trim();
      var exp = l.expected.trim();
      if (got === exp) {
        out.className = 'ln-output ok';
        out.innerHTML = '<span class="ln-status ok">✓ Chính xác!</span>\n\n' + got.replace(/</g,'&lt;');
        state.done[l.id] = true;
        saveProgress();
        renderSidebar();
      } else {
        out.className = 'ln-output fail';
        var msg = '<span class="ln-status fail">✗ Chưa đúng</span>\n\n';
        msg += 'Mong đợi:\n' + exp.replace(/</g,'&lt;') + '\n\n';
        msg += 'Nhận được:\n' + got.replace(/</g,'&lt;');
        out.innerHTML = msg;
      }
    }).catch(function(e) {
      out.className = 'ln-output fail';
      out.textContent = 'Lỗi kết nối: ' + e.message;
    });
  }

  function open() {
    ensureUI();
    loadProgress();
    overlay.classList.add('open');
    render();
  }
  function close() {
    if (overlay) overlay.classList.remove('open');
  }

  // Nút trên activity bar — chèn vào khi DOM ready
  document.addEventListener('DOMContentLoaded', function() {
    // Tìm activitybar
    var ab = document.querySelector('.activitybar');
    if (ab && !document.getElementById('ln-btn-bar')) {
      var btn = document.createElement('div');
      btn.id = 'ln-btn-bar';
      btn.className = 'act-icon';
      btn.title = 'Học Cat++';
      btn.innerHTML = '<i class="fas fa-graduation-cap"></i>';
      btn.addEventListener('click', open);
      // Chèn sau act-icon đầu tiên
      var first = ab.querySelector('.act-icon');
      if (first && first.nextSibling) {
        ab.insertBefore(btn, first.nextSibling);
      } else {
        ab.appendChild(btn);
      }
    }

    // Nút trong drawer
    var drawerBody = document.getElementById('drawer-body');
    if (drawerBody && !document.getElementById('ln-drawer-btn')) {
      var sec = drawerBody.querySelector('.drawer-section');
      if (sec) {
        var btn2 = document.createElement('a');
        btn2.id = 'ln-drawer-btn';
        btn2.className = 'drawer-item';
        btn2.innerHTML = '<i class="fas fa-graduation-cap"></i> Học Cat++';
        btn2.addEventListener('click', function() {
          if (window.closeDrawer) window.closeDrawer();
          open();
        });
        var firstSection = drawerBody.querySelector('.drawer-section');
        if (firstSection) firstSection.insertBefore(btn2, firstSection.firstChild.nextSibling);
      }
    }
  });

  window.catLearn = { open: open, close: close };
  console.log('[Cat++] Learn Mode loaded — 10 bài tập');
})();
