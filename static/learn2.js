/* Cat++ Learn 2 — Quiz, Dashboard, Certificate, Gallery */
(function() {
  'use strict';

  var QUIZ_STORE = 'catpp:learn:quiz';
  var GALLERY_STORE = 'catpp:gallery';
  var NAME_STORE = 'catpp:user:name';

  // ============ QUIZ DATA ============
  var QUIZZES = {
    l01: { q: 'Từ khóa nào dùng để in ra màn hình?', opts: ['paw', 'meow', 'purr', 'give'], a: 1 },
    l02: { q: 'Khai báo biến dùng từ khóa nào?', opts: ['let', 'var', 'paw', 'set'], a: 2 },
    l03: { q: 'Nối chuỗi bằng toán tử nào?', opts: ['&', '.', '+', ','], a: 2 },
    l04: { q: 'Điều kiện dùng từ khóa nào?', opts: ['if', 'when', 'sniff', 'check'], a: 2 },
    l05: { q: 'Vòng lặp while trong Cat++ là gì?', opts: ['while', 'loop', 'knead', 'repeat'], a: 2 },
    l06: { q: 'Hàm trả về giá trị bằng từ khóa nào?', opts: ['return', 'give', 'back', 'yield'], a: 1 },
    l07: { q: 'Đệ quy là gì?', opts: ['Hàm gọi chính nó', 'Vòng lặp vô tận', 'Hàm có tham số', 'Hàm không có give'], a: 0 },
    l08: { q: 'Hàm tính tổng danh sách là gì?', opts: ['sum()', 'total()', 'pile()', 'add()'], a: 2 },
    l09: { q: 'Chuyển chuỗi sang chữ HOA bằng gì?', opts: ['upper()', 'puff()', 'caps()', 'big()'], a: 1 },
    l10: { q: 'Class trong Cat++ dùng từ khóa nào?', opts: ['class', 'cat', 'type', 'struct'], a: 1 },
    'l11': { q: 'Default param viết thế nào?', opts: ["f(a)", "f(a=10)", "f(a:10)", "f(a:10=)"], a: 1 },
    'l12': { q: 'Lambda dùng từ khóa nào?', opts: ["fn", "lambda", "kit", "arrow"], a: 2 },
    'l13': { q: 'Hàm map trong Cat++ là?', opts: ["map", "chase", "apply", "each"], a: 1 },
    'l14': { q: 'Hàm reduce trong Cat++ là?', opts: ["reduce", "fold", "curl", "sum"], a: 2 },
    'l15': { q: 'Regex pattern cho chữ số là?', opts: ["\\w", "\\d", "\\s", "[a-z]"], a: 1 },
    'l16': { q: 'Trích xuất tất cả dùng hàm nào?', opts: ["match", "find_all", "extract", "grep"], a: 1 },
    'l17': { q: 'Wildcard trong match/case là?', opts: ["*", "_", "?", "any"], a: 1 },
    'l18': { q: 'Dict truy cập bằng cách nào?', opts: ["d.key", "d['key']", "d->key", "both d.key and d['key']"], a: 3 },
    'l19': { q: 'Loại phần tử trùng dùng hàm nào?', opts: ["unique", "dedupe", "set", "clean"], a: 0 },
    'l20': { q: 'Bắt lỗi bằng từ khóa nào?', opts: ["catch", "except", "hiss", "handle"], a: 2 },
    'l21': { q: 'Ghi file dùng hàm nào?', opts: ["write", "save", "write_file", "put"], a: 2 },
    'l22': { q: 'Đọc file theo dòng dùng hàm nào?', opts: ["read_file", "read_lines", "readlines", "readline"], a: 1 },
    'l23': { q: 'Liệt kê thư mục dùng hàm nào?', opts: ["ls", "dir", "list_dir", "list"], a: 2 },
    'l24': { q: '3 engine của Cat++ là gì?', opts: ["Interpreter, VM, PyCompiler", "Fast, Slow, Medium", "Tree, Byte, Py", "A, B, C"], a: 0 },
    'l25': { q: 'PyCompiler nhanh hơn interpreter bao nhiêu lần?', opts: ["2x", "5x", "20-50x", "1000x"], a: 2 },
    'l26': { q: 'Felis OS viết bằng ngôn ngữ gì?', opts: ["Python", "C + assembly", "Rust", "JavaScript"], a: 1 },
    'l27': { q: 'Felis OS có bao nhiêu commands?', opts: ["10", "23", "50", "100"], a: 1 },
    'l28': { q: 'Felis OS lưu file ở đâu?', opts: ["Disk", "USB", "RAM", "Network"], a: 2 },
    'l29': { q: 'Boot loader của Felis OS là?', opts: ["BIOS", "GRUB", "LILO", "rEFInd"], a: 1 },
    'l30': { q: 'Số fib(10) là bao nhiêu?', opts: ["34", "55", "89", "144"], a: 1 },
  };

  // ============ STORAGE ============
  function getQuizProgress() {
    try { return JSON.parse(localStorage.getItem(QUIZ_STORE) || '{}'); } catch (e) { return {}; }
  }
  function setQuizProgress(p) {
    try { localStorage.setItem(QUIZ_STORE, JSON.stringify(p)); } catch (e) {}
  }
  function getGallery() {
    try { return JSON.parse(localStorage.getItem(GALLERY_STORE) || '[]'); } catch (e) { return []; }
  }
  function setGallery(g) {
    try { localStorage.setItem(GALLERY_STORE, JSON.stringify(g)); } catch (e) {}
  }
  function getUserName() {
    try { return localStorage.getItem(NAME_STORE) || ''; } catch (e) { return ''; }
  }
  function setUserName(n) {
    try { localStorage.setItem(NAME_STORE, n); } catch (e) {}
  }

  // ============ QUIZ UI ============
  function renderQuiz(lessonId) {
    var quiz = QUIZZES[lessonId];
    if (!quiz) return '';
    var prog = getQuizProgress();
    var answered = prog[lessonId];
    var html = '<div class="lq-quiz" data-lesson="' + lessonId + '">' +
      '<h4>📝 Câu hỏi kiểm tra</h4>' +
      '<div class="lq-q">' + quiz.q + '</div>' +
      '<div class="lq-opts">';
    for (var i = 0; i < quiz.opts.length; i++) {
      var cls = 'lq-opt';
      if (answered !== undefined && answered !== null) {
        if (i === quiz.a) cls += ' correct';
        else if (i === answered) cls += ' wrong';
      }
      html += '<button class="' + cls + '" data-idx="' + i + '"' + (answered !== undefined && answered !== null ? ' disabled' : '') + '>' +
        String.fromCharCode(65 + i) + '. ' + quiz.opts[i] + '</button>';
    }
    html += '</div></div>';
    return html;
  }

  function bindQuiz(container, lessonId) {
    var quiz = QUIZZES[lessonId];
    if (!quiz) return;
    var box = container.querySelector('.lq-quiz[data-lesson="' + lessonId + '"]');
    if (!box) return;
    var buttons = box.querySelectorAll('.lq-opt');
    for (var i = 0; i < buttons.length; i++) {
      (function(btn, idx) {
        btn.addEventListener('click', function() {
          var prog = getQuizProgress();
          prog[lessonId] = idx;
          setQuizProgress(prog);
          for (var j = 0; j < buttons.length; j++) {
            buttons[j].disabled = true;
            if (j === quiz.a) buttons[j].classList.add('correct');
            else if (j === idx) buttons[j].classList.add('wrong');
          }
        });
      })(buttons[i], i);
    }
  }

  // ============ DASHBOARD ============
  function openDashboard() {
    var overlay = document.getElementById('lq-dashboard');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = 'lq-dashboard';
      overlay.className = 'lq-overlay';
      overlay.innerHTML = '<div class="lq-modal" id="lq-modal-content"></div>';
      overlay.addEventListener('click', function(e) { if (e.target === overlay) overlay.classList.remove('open'); });
      document.body.appendChild(overlay);
    }
    renderDashboard();
    overlay.classList.add('open');
  }

  function renderDashboard() {
    var learnDone = {};
    try { learnDone = JSON.parse(localStorage.getItem('catpp:learn:progress') || '{}'); } catch (e) {}
    var quizDone = getQuizProgress();
    var gallery = getGallery();

    var totalLessons = 10;
    var lessonsDone = Object.keys(learnDone).length;
    var quizzesDone = Object.keys(quizDone).length;
    var correctQuizzes = 0;
    Object.keys(quizDone).forEach(function(k) {
      if (QUIZZES[k] && quizDone[k] === QUIZZES[k].a) correctQuizzes++;
    });

    var html = '<h2>📊 Tiến độ học tập</h2>';
    html += '<div class="lq-stats">';
    html += '<div class="lq-stat"><span class="num">' + lessonsDone + '/' + totalLessons + '</span><span class="label">Bài tập</span></div>';
    html += '<div class="lq-stat"><span class="num">' + quizzesDone + '/' + totalLessons + '</span><span class="label">Quiz</span></div>';
    html += '<div class="lq-stat"><span class="num">' + correctQuizzes + '</span><span class="label">Câu đúng</span></div>';
    html += '<div class="lq-stat"><span class="num">' + gallery.length + '</span><span class="label">Code hay</span></div>';
    html += '</div>';

    html += '<h3 style="color:#f97316;margin:20px 0 12px">Chi tiết bài học</h3>';
    html += '<div class="lq-bars">';
    var lessonNames = ['In màn hình','Biến','Nối chuỗi','Điều kiện','Vòng lặp','Hàm','Đệ quy','Danh sách','Chuỗi','Class'];
    for (var i = 0; i < totalLessons; i++) {
      var id = 'l0' + (i + 1);
      var done = learnDone[id] ? 100 : 0;
      var quiz = quizDone[id];
      var quizOk = quiz !== undefined && QUIZZES[id] && quiz === QUIZZES[id].a;
      var label = lessonNames[i];
      var status = done ? (quizOk ? '✓✓' : '✓') : '';
      html += '<div class="lq-bar">' +
        '<div class="lq-bar-name">Bài ' + (i+1) + ': ' + label + ' ' + status + '</div>' +
        '<div class="lq-bar-track"><div class="lq-bar-fill" style="width:' + (done ? (quizOk ? 100 : 60) : 0) + '%"></div></div>' +
        '</div>';
    }
    html += '</div>';

    if (lessonsDone >= totalLessons) {
      html += '<div style="margin-top:24px;padding:16px;background:rgba(126,231,135,.15);border-radius:8px;text-align:center">' +
        '<b style="color:#7ee787">🎉 Bạn đã hoàn thành tất cả bài học!</b>' +
        '<div style="margin-top:8px"><button class="lq-btn" onclick="window.catLearn2.certificate()">📜 Nhận chứng chỉ</button></div>' +
        '</div>';
    }

    html += '<div class="lq-actions">' +
      '<button class="lq-btn secondary" onclick="document.getElementById(\'lq-dashboard\').classList.remove(\'open\')">Đóng</button>' +
      '<button class="lq-btn secondary" onclick="window.catLearn2.gallery()">🖼️ Gallery</button>' +
      (lessonsDone >= totalLessons ? '<button class="lq-btn" onclick="window.catLearn2.certificate()">📜 Chứng chỉ</button>' : '') +
      '</div>';

    document.getElementById('lq-modal-content').innerHTML = html;
  }

  // ============ CERTIFICATE ============
  function openCertificate() {
    var name = getUserName();
    if (!name) {
      name = prompt('Nhập tên của bạn (hiện trên chứng chỉ):', '');
      if (!name) return;
      setUserName(name);
    }

    var overlay = document.getElementById('lq-cert');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = 'lq-cert';
      overlay.className = 'lq-overlay';
      overlay.innerHTML = '<div class="lq-modal" style="text-align:center">' +
        '<div id="lq-cert-render"></div>' +
        '<div style="margin-top:20px;display:flex;gap:12px;justify-content:center">' +
        '<button class="lq-btn" id="lq-cert-dl">⬇️ Tải về PNG</button>' +
        '<button class="lq-btn secondary" onclick="document.getElementById(\'lq-cert\').classList.remove(\'open\')">Đóng</button>' +
        '</div></div>';
      overlay.addEventListener('click', function(e) { if (e.target === overlay) overlay.classList.remove('open'); });
      document.body.appendChild(overlay);
      document.getElementById('lq-cert-dl').addEventListener('click', downloadCertificate);
    }

    var today = new Date().toLocaleDateString('vi-VN');
    var html = '<div class="cert" id="cert-canvas">' +
      '<div class="cert-badge">🐱</div>' +
      '<div class="cert-cat">🐱</div>' +
      '<h1>CAT++</h1>' +
      '<h2>CERTIFICATE OF COMPLETION</h2>' +
      '<div class="cert-name">' + escapeHtml(name) + '</div>' +
      '<div class="cert-body">' +
        'đã hoàn thành khóa học<br>' +
        '<b>Ngôn ngữ lập trình Cat++</b><br>' +
        'gồm <b>10 bài tập</b> và <b>10 câu hỏi kiểm tra</b>' +
      '</div>' +
      '<div class="cert-footer">' +
        '<div class="cert-sign"><div class="line">🐾 Cat++ Team</div></div>' +
        '<div class="cert-date">Ngày cấp: ' + today + '</div>' +
      '</div>' +
      '</div>';
    document.getElementById('lq-cert-render').innerHTML = html;
    overlay.classList.add('open');
  }

  function escapeHtml(s) {
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  function downloadCertificate() {
    var cert = document.getElementById('cert-canvas');
    if (!cert) return;

    // Dùng SVG foreignObject để render HTML thành ảnh
    var w = 900, h = 636;
    var data = new XMLSerializer().serializeToString(cert);
    var svg = '<svg xmlns="http://www.w3.org/2000/svg" width="' + w + '" height="' + h + '">' +
      '<foreignObject width="100%" height="100%">' +
      '<div xmlns="http://www.w3.org/1999/xhtml">' + data + '</div>' +
      '</foreignObject></svg>';

    var img = new Image();
    img.onload = function() {
      var canvas = document.createElement('canvas');
      canvas.width = w;
      canvas.height = h;
      var ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0);
      canvas.toBlob(function(blob) {
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = 'catpp-certificate.png';
        a.click();
        URL.revokeObjectURL(url);
      });
    };
    img.onerror = function() {
      alert('Không xuất được ảnh. Chụp màn hình vậy 😅');
    };
    img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svg)));
  }

  // ============ GALLERY ============
  function openGallery() {
    var overlay = document.getElementById('lq-gallery');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = 'lq-gallery';
      overlay.className = 'lq-overlay';
      overlay.innerHTML = '<div class="lq-modal" id="lq-gallery-content"></div>';
      overlay.addEventListener('click', function(e) { if (e.target === overlay) overlay.classList.remove('open'); });
      document.body.appendChild(overlay);
    }
    renderGallery();
    overlay.classList.add('open');
  }

  function renderGallery() {
    var gallery = getGallery();
    var html = '<h2>🖼️ Gallery — Code hay</h2>';
    html += '<div style="display:flex;gap:12px;margin-bottom:16px">';
    html += '<button class="lq-btn" id="lq-g-add">+ Thêm code hiện tại</button>';
    html += '<button class="lq-btn secondary" onclick="document.getElementById(\'lq-gallery\').classList.remove(\'open\')">Đóng</button>';
    html += '</div>';

    if (!gallery.length) {
      html += '<div class="lq-empty">Chưa có code nào. Mở 1 file, sửa cho hay, rồi bấm "Thêm code hiện tại" ở trên.</div>';
    } else {
      html += '<div class="lq-gallery-grid">';
      for (var i = gallery.length - 1; i >= 0; i--) {
        var g = gallery[i];
        html += '<div class="lq-gcard">' +
          '<h4>' + escapeHtml(g.name) + '</h4>' +
          '<p>' + escapeHtml((g.code || '').slice(0, 200)) + '</p>' +
          '<div class="meta">' + (g.date || '') + '</div>' +
          '<div class="actions">' +
          '<button data-open="' + i + '">Mở</button>' +
          '<button data-del="' + i + '">Xóa</button>' +
          '</div></div>';
      }
      html += '</div>';
    }
    document.getElementById('lq-gallery-content').innerHTML = html;

    var addBtn = document.getElementById('lq-g-add');
    if (addBtn) addBtn.addEventListener('click', addToGallery);

    var openBtns = document.querySelectorAll('[data-open]');
    for (var j = 0; j < openBtns.length; j++) {
      (function(btn) {
        btn.addEventListener('click', function() {
          var idx = parseInt(btn.getAttribute('data-open'), 10);
          var g = getGallery()[idx];
          if (!g) return;
          if (window.files) {
            window.files[g.name] = g.code;
            if (window.saveFiles) window.saveFiles();
            if (window.renderFileTree) window.renderFileTree();
            if (window.openFile) window.openFile(g.name);
          }
          document.getElementById('lq-gallery').classList.remove('open');
        });
      })(openBtns[j]);
    }

    var delBtns = document.querySelectorAll('[data-del]');
    for (var k = 0; k < delBtns.length; k++) {
      (function(btn) {
        btn.addEventListener('click', function() {
          var idx = parseInt(btn.getAttribute('data-del'), 10);
          if (!confirm('Xóa code này?')) return;
          var arr = getGallery();
          arr.splice(idx, 1);
          setGallery(arr);
          renderGallery();
        });
      })(delBtns[k]);
    }
  }

  function addToGallery() {
    if (!window.editor || !window.activeTab) {
      alert('Chưa có file nào đang mở');
      return;
    }
    var name = prompt('Tên gợi nhớ cho code này:', window.activeTab);
    if (!name) return;
    var gallery = getGallery();
    gallery.push({
      name: name,
      file: window.activeTab,
      code: window.editor.getValue(),
      date: new Date().toLocaleString('vi-VN')
    });
    setGallery(gallery);
    renderGallery();
  }

  // ============ HOOK VÀO LEARN MODE ============
  // Sau khi Learn Mode render xong, chèn quiz
  var origRenderTask = null;
  function hookLearnMode() {
    // Đợi learn.js load xong
    var check = setInterval(function() {
      var learnModal = document.querySelector('.ln-overlay');
      if (!learnModal) return;
      clearInterval(check);

      // Watch DOM changes trong task area
      var taskEl = document.getElementById('ln-task');
      if (!taskEl) return;

      var observer = new MutationObserver(function() {
        var currentLesson = null;
        // Tìm lesson id từ sidebar active
        var activeItem = document.querySelector('.ln-item.active');
        if (activeItem) {
          var idx = parseInt(activeItem.getAttribute('data-idx'), 10);
          var lessonIds = ['l01','l02','l03','l04','l05','l06','l07','l08','l09','l10'];
          currentLesson = lessonIds[idx];
        }
        if (!currentLesson) return;

        // Nếu chưa có quiz trong task, thêm vào
        if (!taskEl.querySelector('.lq-quiz')) {
          var div = document.createElement('div');
          div.innerHTML = renderQuiz(currentLesson);
          taskEl.appendChild(div);
          bindQuiz(taskEl, currentLesson);
        }
      });

      observer.observe(taskEl, { childList: true, subtree: false });
    }, 500);
  }

  // ============ NÚT DASHBOARD + GALLERY ============
  function addDashboardButton() {
    var ab = document.querySelector('.activitybar');
    if (ab && !document.getElementById('lq-dash-btn')) {
      var btn = document.createElement('div');
      btn.id = 'lq-dash-btn';
      btn.className = 'act-icon';
      btn.title = 'Tiến độ học tập';
      btn.innerHTML = '<i class="fas fa-chart-line"></i>';
      btn.addEventListener('click', openDashboard);
      ab.appendChild(btn);
    }
  }

  // ============ INIT ============
  document.addEventListener('DOMContentLoaded', function() {
    addDashboardButton();
    hookLearnMode();
  });

  // Expose API
  window.catLearn2 = {
    dashboard: openDashboard,
    certificate: openCertificate,
    gallery: openGallery,
    addToGallery: addToGallery
  };

  console.log('[Cat++] Learn 2 loaded — Quiz, Dashboard, Certificate, Gallery');
})();
