/* Cat++ Learn Mode — bài tập tương tác */
(function() {
  'use strict';

  var STORAGE = 'catpp:learn:progress';

  var LESSONS = [
    // ═════════════════════════════════════════
    // PHẦN 1: CƠ BẢN (1-10)
    // ═════════════════════════════════════════
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

    { id: 'l04', title: 'Điều kiện', cat: 'Cơ bản',
      desc: 'Cho <code>x = 8</code>. Nếu x chẵn in <code>chan</code>, ngược lại in <code>le</code>.',
      starter: 'paw x = 8\n',
      expected: 'chan',
      hint: 'sniff x % 2 == 0\n    meow "chan"\nswat\n    meow "le"' },

    { id: 'l05', title: 'Vòng lặp', cat: 'Cơ bản',
      desc: 'In các số từ 1 đến 5, mỗi số một dòng.',
      starter: 'paw i = 1\n',
      expected: '1\n2\n3\n4\n5',
      hint: 'knead i <= 5\n    meow i\n    i++' },

    { id: 'l06', title: 'Hàm', cat: 'Cơ bản',
      desc: 'Viết hàm <code>double(x)</code> trả về <code>x * 2</code>. In <code>double(21)</code>.',
      starter: 'purr double(x)\n    # viết code\n',
      expected: '42',
      hint: 'purr double(x)\n    give x * 2\nmeow double(21)' },

    { id: 'l07', title: 'Đệ quy', cat: 'Cơ bản',
      desc: 'Tính giai thừa <code>5!</code> = 120 bằng đệ quy.',
      starter: 'purr fact(n)\n    # viết code\n',
      expected: '120',
      hint: 'sniff n <= 1\n    give 1\ngive n * fact(n - 1)' },

    { id: 'l08', title: 'Danh sách', cat: 'Cơ bản',
      desc: 'Tính tổng danh sách <code>[10, 20, 30, 40]</code>.',
      starter: 'paw arr = [10, 20, 30, 40]\n',
      expected: '100',
      hint: 'meow pile(arr)' },

    { id: 'l09', title: 'Chuỗi', cat: 'Cơ bản',
      desc: 'In <code>"hello"</code> chuyển sang chữ HOA.',
      starter: '# Viết code\n',
      expected: 'HELLO',
      hint: 'meow "hello".upper()' },

    { id: 'l10', title: 'Class', cat: 'Cơ bản',
      desc: 'Viết class <code>Point</code> với 2 trường <code>x</code>, <code>y</code>. Tạo <code>Point(3, 4)</code> và in <code>x</code>.',
      starter: 'cat Point\n    paw x\n    paw y\n    # viết new\n',
      expected: '3',
      hint: 'purr new(a, b)\n    me.x = a\n    me.y = b\npaw p = Point(3, 4)\nmeow p.x' },

    // ═════════════════════════════════════════
    // PHẦN 2: NÂNG CAO (11-20)
    // ═════════════════════════════════════════
    { id: 'l11', title: 'Default params', cat: 'Nâng cao',
      desc: 'Viết hàm <code>greet(name, greeting="Hello")</code>. In <code>greet("Tom")</code>.',
      starter: 'purr greet(name, greeting = "Hello")\n    give greeting + ", " + name\n',
      expected: 'Hello, Tom',
      hint: 'meow greet("Tom")' },

    { id: 'l12', title: 'Lambda', cat: 'Nâng cao',
      desc: 'Tạo lambda <code>double</code> nhân đôi. Gọi <code>double(21)</code>.',
      starter: '# Viết code\n',
      expected: '42',
      hint: 'paw double = kit(x) => x * 2\nmeow double(21)' },

    { id: 'l13', title: 'Map / Filter', cat: 'Nâng cao',
      desc: 'Cho <code>[1, 2, 3, 4]</code>. In bình phương của số chẵn.',
      starter: 'paw nums = [1, 2, 3, 4]\n',
      expected: '[4, 16]',
      hint: 'paw evens = sift(nums, kit(x) => x % 2 == 0)\nmeow chase(evens, kit(x) => x * x)' },

    { id: 'l14', title: 'Reduce', cat: 'Nâng cao',
      desc: 'Dùng <code>curl</code> tính tổng <code>[1, 2, 3, 4, 5]</code>.',
      starter: 'paw nums = [1, 2, 3, 4, 5]\n',
      expected: '15',
      hint: 'meow curl(nums, kit(a, b) => a + b, 0)' },

    { id: 'l15', title: 'Regex cơ bản', cat: 'Nâng cao',
      desc: 'Kiểm tra <code>"abc123"</code> có chứa chữ số không. In <code>yes</code> nếu có.',
      starter: '',
      expected: 'yes',
      hint: 'sniff match("[0-9]", "abc123")\n    meow "yes"' },

    { id: 'l16', title: 'Regex nâng cao', cat: 'Nâng cao',
      desc: 'Trích xuất tất cả số từ <code>"a1b2c3"</code>.',
      starter: '',
      expected: '[1, 2, 3]',
      hint: 'meow find_all("[0-9]", "a1b2c3")' },

    { id: 'l17', title: 'match/case', cat: 'Nâng cao',
      desc: 'Dùng <code>match</code> để in "hai" khi x = 2.',
      starter: 'paw x = 2\n',
      expected: 'hai',
      hint: 'match x\n    case 1\n        meow "mot"\n    case 2\n        meow "hai"' },

    { id: 'l18', title: 'Dict', cat: 'Nâng cao',
      desc: 'Tạo dict có key <code>"name"</code> giá trị <code>"Tom"</code>. In giá trị.',
      starter: 'paw person = {"name": "Tom"}\n',
      expected: 'Tom',
      hint: 'meow person["name"]' },

    { id: 'l19', title: 'Set', cat: 'Nâng cao',
      desc: 'Loại phần tử trùng trong <code>[1, 2, 2, 3, 3, 3]</code>.',
      starter: 'paw arr = [1, 2, 2, 3, 3, 3]\n',
      expected: '[1, 2, 3]',
      hint: 'meow unique(arr)' },

    { id: 'l20', title: 'Try / catch', cat: 'Nâng cao',
      desc: 'Bắt lỗi chia cho 0, in <code>caught</code>.',
      starter: 'tap\n    paw x = 1 / 0\nhiss e\n    # in caught\n',
      expected: 'caught',
      hint: 'tap\n    paw x = 1 / 0\nhiss e\n    meow "caught"' },

    // ═════════════════════════════════════════
    // PHẦN 3: HỆ THỐNG (21-30)
    // ═════════════════════════════════════════
    { id: 'l21', title: 'File I/O', cat: 'Hệ thống',
      desc: 'Ghi <code>"hello"</code> vào <code>/tmp/cat1.txt</code> rồi đọc lại.',
      starter: '# Viết code\n',
      expected: 'hello',
      hint: 'write_file("/tmp/cat1.txt", "hello")\nmeow read_file("/tmp/cat1.txt")' },

    { id: 'l22', title: 'Đọc dòng', cat: 'Hệ thống',
      desc: 'Đọc <code>/tmp/cat2.txt</code> có 3 dòng, in dòng thứ 2.',
      starter: 'write_file("/tmp/cat2.txt", "mot\\nhai\\nba\\n")\n',
      expected: 'hai',
      hint: 'paw lines = read_lines("/tmp/cat2.txt")\nmeow lines[1]' },

    { id: 'l23', title: 'List files', cat: 'Hệ thống',
      desc: 'Đếm số file trong <code>/tmp</code> > 0. In <code>nod</code> nếu có ít nhất 1 file.',
      starter: '',
      expected: 'nod',
      hint: 'paw files = list_dir("/tmp")\nsniff len(files) > 0\n    meow "nod"' },

    { id: 'l24', title: 'Bytecode VM', cat: 'VM',
      desc: 'Cat++ có 3 engine. Chạy loop 1000 lần tính tổng. In tổng.',
      starter: 'paw s = 0\npaw i = 0\nknead i < 1000\n    s += i\n    i++\nmeow s\n',
      expected: '499500',
      hint: 'Code chạy tự động qua PyCompiler — nhanh nhất' },

    { id: 'l25', title: 'PyCompiler tốc độ', cat: 'VM',
      desc: 'Tính Fibonacci thứ 15 bằng đệ quy.',
      starter: 'purr fib(n)\n    sniff n <= 1\n        give n\n    give fib(n - 1) + fib(n - 2)\n',
      expected: '610',
      hint: 'meow fib(15)' },

    { id: 'l26', title: 'Felis OS — giới thiệu', cat: 'Felis OS',
      desc: 'In ra <code>Felis OS v0.2</code> — tên hệ điều hành nhỏ viết bằng C + Cat++ runtime.',
      starter: '',
      expected: 'Felis OS v0.2',
      hint: 'meow "Felis OS v0.2"' },

    { id: 'l27', title: 'Felis OS — commands', cat: 'Felis OS',
      desc: 'Felis OS có 23 shell commands. In số 23 dạng chuỗi.',
      starter: '',
      expected: '23',
      hint: 'meow "23"' },

    { id: 'l28', title: 'Felis OS — filesystem', cat: 'Felis OS',
      desc: 'Mô phỏng RAM filesystem: tạo list <code>["readme.txt", "notes.txt"]</code>, in phần tử đầu.',
      starter: '',
      expected: 'readme.txt',
      hint: 'paw files = ["readme.txt", "notes.txt"]\nmeow files[0]' },

    { id: 'l29', title: 'Felis OS — boot flow', cat: 'Felis OS',
      desc: 'Mô phỏng chuỗi boot: <code>["GRUB", "kernel", "shell", "cat>"]</code>. In phần tử cuối.',
      starter: '',
      expected: 'cat>',
      hint: 'paw steps = ["GRUB", "kernel", "shell", "cat>"]\nmeow steps[3]' },

    { id: 'l30', title: 'Đồ án cuối — tổng hợp', cat: 'Felis OS',
      desc: 'Viết hàm <code>fib</code> đệ quy, tính fib(10). In kết quả.',
      starter: 'purr fib(n)\n    # viết code\n',
      expected: '55',
      hint: 'sniff n <= 1\n    give n\ngive fib(n - 1) + fib(n - 2)\nmeow fib(10)' }
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
