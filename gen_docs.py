#!/usr/bin/env python3
import os, html, shutil, importlib

SITE = 'static/docs'

CSS = """* { margin:0; padding:0; box-sizing:border-box; }
:root{--bg:#0d1117;--bg-side:#161b22;--bg-hover:#21262d;--bg-code:#1c2128;
--fg:#c9d1d9;--fg-dim:#8b949e;--fg-bright:#f0f6fc;--accent:#f97316;
--accent2:#fb923c;--border:#30363d;--border-soft:#21262d;--green:#7ee787;
--purple:#d2a8ff;--orange:#ffa657;--blue:#79c0ff;--yellow:#f2cc60;--red:#ff7b72;}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
background:var(--bg);color:var(--fg);line-height:1.65;font-size:16px;}
a{color:var(--accent);text-decoration:none;} a:hover{text-decoration:underline;}
code{background:var(--bg-code);color:var(--orange);padding:2px 6px;border-radius:4px;
font-family:ui-monospace,Consolas,monospace;font-size:.9em;border:1px solid var(--border-soft);}
pre{background:var(--bg-code);border:1px solid var(--border);border-radius:6px;
padding:16px 20px;overflow-x:auto;margin:14px 0;position:relative;line-height:1.55;}
pre code{background:transparent;color:var(--fg);padding:0;border:none;font-size:14px;}
h1,h2,h3{color:var(--fg-bright);font-weight:600;}
h1{font-size:2rem;margin:0 0 1rem;padding-bottom:.5rem;border-bottom:1px solid var(--border);}
h2{font-size:1.5rem;margin:2rem 0 .75rem;padding-bottom:.25rem;border-bottom:1px solid var(--border-soft);}
h3{font-size:1.2rem;margin:1.5rem 0 .5rem;}
p,ul,ol{margin:.75rem 0;} ul,ol{margin-left:1.5rem;} li{margin:.25rem 0;}
table{width:100%;border-collapse:collapse;margin:1rem 0;font-size:.95em;}
th,td{border:1px solid var(--border);padding:8px 14px;text-align:left;}
th{background:var(--bg-side);color:var(--fg-bright);}
.layout{display:grid;grid-template-columns:260px 1fr;min-height:100vh;}
.header{position:sticky;top:0;z-index:10;background:var(--bg-side);
border-bottom:1px solid var(--border);padding:12px 24px;display:flex;align-items:center;gap:8px;grid-column:1/-1;}
.header-logo{font-weight:700;font-size:18px;color:var(--fg-bright);margin-right:16px;}
.header-logo span{color:var(--accent);}
.header-spacer{flex:1;}
.header-link{color:var(--fg-dim);padding:6px 12px;border-radius:6px;font-size:14px;}
.header-link:hover{background:var(--bg-hover);color:var(--fg-bright);text-decoration:none;}
.header-link.dl{background:linear-gradient(135deg,#f97316,#ea580c);color:#fff;font-weight:600;}
.header-link.dl:hover{background:linear-gradient(135deg,#fb923c,#f97316);}
.lang-switch{display:flex;gap:2px;background:var(--bg);border:1px solid var(--border);
border-radius:6px;padding:2px;margin-right:8px;}
.lang-switch a{padding:4px 10px;border-radius:4px;font-size:13px;color:var(--fg-dim);}
.lang-switch a:hover{background:var(--bg-hover);color:var(--fg-bright);text-decoration:none;}
.lang-switch a.active{background:var(--accent);color:#fff;}
.sidebar{background:var(--bg-side);border-right:1px solid var(--border);
padding:20px 0;overflow-y:auto;position:sticky;top:57px;height:calc(100vh - 57px);}
.sidebar-section{padding:8px 20px 4px;font-size:11px;text-transform:uppercase;
letter-spacing:.1em;color:var(--fg-dim);font-weight:600;}
.sidebar-link{display:block;padding:6px 20px;color:var(--fg);font-size:14px;
border-left:2px solid transparent;}
.sidebar-link:hover{background:var(--bg-hover);color:var(--fg-bright);text-decoration:none;}
.sidebar-link.active{background:var(--bg-hover);color:var(--fg-bright);border-left-color:var(--accent);}
.sidebar-search{padding:0 16px 12px;}
.sidebar-search input{width:100%;background:var(--bg);color:var(--fg);
border:1px solid var(--border);border-radius:6px;padding:8px 12px;font-size:14px;outline:none;}
.sidebar-search input:focus{border-color:var(--accent);}
.content{padding:32px 48px 80px;max-width:900px;}
.breadcrumb{font-size:13px;color:var(--fg-dim);margin-bottom:8px;display:flex;gap:8px;flex-wrap:wrap;}
.breadcrumb a{color:var(--fg-dim);}
.pager{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:48px;
padding-top:24px;border-top:1px solid var(--border);}
.pager-item{padding:14px 18px;border:1px solid var(--border);border-radius:8px;
display:flex;flex-direction:column;gap:4px;}
.pager-item:hover{border-color:var(--accent);background:var(--bg-side);text-decoration:none;}
.pager-item span{font-size:12px;color:var(--fg-dim);}
.pager-item b{color:var(--fg-bright);font-size:14px;}
.pager-item.next{text-align:right;}
.hero{padding:60px 0 40px;text-align:center;}
.hero h1{border:none;font-size:3rem;margin-bottom:12px;}
.hero p{font-size:1.2rem;color:var(--fg-dim);max-width:600px;margin:0 auto 32px;}
.hero-btns{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;}
.btn{display:inline-block;padding:10px 20px;border-radius:6px;font-weight:500;font-size:15px;}
.btn-primary{background:var(--accent);color:#fff;}
.btn-primary:hover{background:var(--accent2);text-decoration:none;}
.btn-secondary{background:var(--bg-hover);color:var(--fg);}
.btn-secondary:hover{background:var(--border);text-decoration:none;color:var(--fg-bright);}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px;margin:32px 0;}
.card{background:var(--bg-side);border:1px solid var(--border);border-radius:8px;
padding:20px;text-decoration:none;color:inherit;display:block;}
.card:hover{border-color:var(--accent);text-decoration:none;}
.card h3{margin-top:0;font-size:1.05rem;}
.card p{color:var(--fg-dim);font-size:.92em;margin:.5rem 0 0;}
.kw{color:var(--purple);font-weight:600;}
.str{color:var(--orange);}
.num{color:var(--blue);}
.cmt{color:var(--fg-dim);font-style:italic;}
.bi{color:var(--green);}
.fn{color:var(--yellow);}
.op{color:var(--red);}

.kw-ref {
  display: inline-block;
  background: linear-gradient(135deg, #f97316, #ea580c);
  color: #fff;
  padding: 1px 7px;
  border-radius: 4px;
  font-weight: 600;
  font-size: 0.85em;
  font-family: ui-monospace, Consolas, monospace;
  box-shadow: 0 1px 3px rgba(249, 115, 22, 0.3);
}
@media(max-width:900px){.layout{grid-template-columns:1fr;}.sidebar{display:none;}
.content{padding:20px;}.hero h1{font-size:2rem;}.pager{grid-template-columns:1fr;}
.pager-item.next{text-align:left;}}
"""

JS = """const KW=['paw','meow','purr','give','hiss','tap','sit','leap','listen','sniff',
'swat','knead','groom','of','nod','shake','hungry','with','either','never',
'cat','me','kin','kit','litter'];
const BI=['tail','puff','melt','nip','bolt','kitten','lion','scratch','flop',
'perch','say','tally','drip','collar','kits','seek','shred','weave','swap',
'lick','hunt','stash','snatch','line','flip','head','rear','pile','walk',
'chase','sift','curl','sway','wave','slant','grow','bound','wander','dice'];

function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}

function hl(code){
  var out='';
  var i=0;
  var n=code.length;
  while(i<n){
    var c=code[i];
    if(c==='#'){
      var j=i;
      while(j<n&&code[j]!=='\\n')j++;
      out+='<span class="cmt">'+esc(code.slice(i,j))+'</span>';
      i=j;
      continue;
    }
    if(c==='\\"'){
      var j=i+1;
      var s='\\"';
      while(j<n&&code[j]!=='\\"'){
        if(code[j]==='\\\\'&&j+1<n){
          s+=code[j]+code[j+1];
          j+=2;
        } else {
          s+=code[j];
          j++;
        }
      }
      if(j<n){s+='\\"';j++;}
      out+='<span class="str">'+esc(s)+'</span>';
      i=j;
      continue;
    }
    if(c>='0'&&c<='9'){
      var j=i;
      while(j<n&&(code[j]>='0'&&code[j]<='9'||code[j]==='.'))j++;
      out+='<span class="num">'+code.slice(i,j)+'</span>';
      i=j;
      continue;
    }
    if(/[a-zA-Z_]/.test(c)){
      var j=i;
      while(j<n&&/[a-zA-Z0-9_]/.test(code[j]))j++;
      var w=code.slice(i,j);
      if(KW.indexOf(w)>=0)out+='<span class="kw">'+w+'</span>';
      else if(BI.indexOf(w)>=0)out+='<span class="bi">'+w+'</span>';
      else if(code[j]==='(')out+='<span class="fn">'+w+'</span>';
      else out+=esc(w);
      i=j;
      continue;
    }
    if('+-*/%=<>!'.indexOf(c)>=0){
      var j=i;
      while(j<n&&'+-*/%=<>!'.indexOf(code[j])>=0)j++;
      out+='<span class="op">'+esc(code.slice(i,j))+'</span>';
      i=j;
      continue;
    }
    out+=esc(c);
    i++;
  }
  return out;
}

document.addEventListener('DOMContentLoaded',function(){
  var codes=document.querySelectorAll('pre > code');
  for(var k=0;k<codes.length;k++){
    var el=codes[k];
    var raw=el.textContent;
    el.innerHTML=hl(raw);
    var pre=el.parentElement;
    var btn=document.createElement('button');
    btn.textContent='Copy';
    btn.style.cssText='position:absolute;top:8px;right:8px;background:#21262d;color:#c9d1d9;border:1px solid #30363d;padding:4px 10px;border-radius:4px;cursor:pointer;font-size:12px;opacity:0;transition:opacity .15s;';
    btn.onclick=function(e){
      e.stopPropagation();
      navigator.clipboard.writeText(raw).then(function(){
        btn.textContent='Copied!';
        setTimeout(function(){btn.textContent='Copy';},1200);
      });
    };
    pre.appendChild(btn);
    pre.addEventListener('mouseenter',function(){btn.style.opacity='1';});
    pre.addEventListener('mouseleave',function(){btn.style.opacity='0';});
  }

  var si=document.getElementById('search-input');
  if(si){
    si.addEventListener('input',function(e){
      var q=e.target.value.toLowerCase().trim();
      var links=document.querySelectorAll('.sidebar-link');
      for(var i=0;i<links.length;i++){
        var txt=links[i].textContent.toLowerCase();
        links[i].style.display=(!q||txt.indexOf(q)>=0)?'':'none';
      }
    });
  }

  var sb=document.querySelector('.sidebar');
  if(!sb)return;

  var cur=location.pathname;
  if(cur.length>1&&cur.slice(-1)==='/')cur=cur.slice(0,-1);

  var links=sb.querySelectorAll('.sidebar-link');
  var activeLink=null;
  for(var i=0;i<links.length;i++){
    var href=links[i].getAttribute('href');
    if(!href)continue;
    var abs=href;
    try{abs=new URL(href,location.href).pathname;}catch(e){continue;}
    if(abs.length>1&&abs.slice(-1)==='/')abs=abs.slice(0,-1);
    if(abs===cur){
      links[i].classList.add('active');
      activeLink=links[i];
    }
  }

  if(activeLink){
    setTimeout(function(){
      try{activeLink.scrollIntoView({block:'center'});}catch(e){}
    },150);
  }

  for(var i=0;i<links.length;i++){
    links[i].addEventListener('click',function(){
      try{sessionStorage.setItem('catpp-sbs',sb.scrollTop);}catch(e){}
    });
  }

  if(!activeLink){
    try{
      var sv=sessionStorage.getItem('catpp-sbs');
      if(sv)sb.scrollTop=parseInt(sv,10);
    }catch(e){}
  }
});
"""

def esc_code(c):
    return '<pre><code>' + html.escape(c) + '</code></pre>'

def build_lang(lang_code, data_module):
    KEYWORDS = data_module.KEYWORDS
    BUILTINS = data_module.BUILTINS
    TUTORIAL = data_module.TUTORIAL
    SPEC = data_module.SPEC

    site = os.path.join(SITE, lang_code)
    if os.path.exists(site):
        shutil.rmtree(site)
    for d in ['', '/tutorial', '/ref/keyword', '/ref/builtin', '/spec']:
        os.makedirs(site + d, exist_ok=True)

    with open(site + '/style.css', 'w', encoding='utf-8') as f: f.write(CSS)
    with open(site + '/app.js', 'w', encoding='utf-8') as f: f.write(JS)

    if lang_code == 'vi':
        TXT = {
            'overview':'Tổng quan','home':'Trang chủ','tutorial':'Tutorial',
            'keyword':'Từ khóa','builtin':'Hàm có sẵn','spec':'Đặc tả',
            'search':'Tìm kiếm...','back_ide':'← IDE','ref':'Reference',
            'prev':'← Trước','next':'Tiếp →','mota':'Mô tả','vidu':'Ví dụ',
            'kq':'Kết quả','danhmuc':'Danh mục','cuphap':'Cú pháp','chuky':'Chữ ký',
            'hero_p':'Ngôn ngữ lập trình với cú pháp tiếng mèo. Dễ đọc, dễ học, vui vẻ.',
            'hero_start':'Bắt đầu học →','hero_ref':'Tra cứu','hero_ide':'Mở IDE',
            'khampha':'Khám phá','thongke':'Thống kê',
            'hangmuc':'Hạng mục','soluong':'Số lượng',
            'tukhoa':'Từ khóa','hamcosan':'Hàm có sẵn','baitut':'Bài tutorial',
            'tongtrang':'Tổng số trang','tailieu':'📦 Tải tài liệu',
            'tut_desc':'10 bài từ Hello đến Class.','ref_desc':'Tra cứu keyword và hàm có sẵn.',
            'spec_desc':'Grammar EBNF, ngữ nghĩa.','ide_desc':'Chạy Cat++ trực tiếp.',
        }
    else:
        TXT = {
            'overview':'Overview','home':'Home','tutorial':'Tutorial',
            'keyword':'Keywords','builtin':'Builtins','spec':'Specification',
            'search':'Search...','back_ide':'← IDE','ref':'Reference',
            'prev':'← Prev','next':'Next →','mota':'Description','vidu':'Examples',
            'kq':'Result','danhmuc':'Category','cuphap':'Syntax','chuky':'Signature',
            'hero_p':'A programming language with cat syntax. Easy to read, easy to learn, fun.',
            'hero_start':'Start learning →','hero_ref':'Reference','hero_ide':'Open IDE',
            'khampha':'Explore','thongke':'Statistics',
            'hangmuc':'Item','soluong':'Count',
            'tukhoa':'Keywords','hamcosan':'Builtins','baitut':'Tutorials',
            'tongtrang':'Total pages','tailieu':'📦 Download docs',
            'tut_desc':'10 lessons from Hello to Class.','ref_desc':'Look up keywords and builtins.',
            'spec_desc':'EBNF grammar, semantics.','ide_desc':'Run Cat++ directly.',
        }

    def sidebar(root=''):
        s = '<div class="sidebar-search"><input id="search-input" placeholder="' + TXT['search'] + '"></div>'
        s += '<div class="sidebar-section">' + TXT['overview'] + '</div>'
        s += '<a href="' + root + 'index.html" class="sidebar-link">' + TXT['home'] + '</a>'
        s += '<div class="sidebar-section">' + TXT['tutorial'] + '</div>'
        for slug, title, _ in TUTORIAL:
            s += '<a href="' + root + 'tutorial/' + slug + '.html" class="sidebar-link">' + title + '</a>'
        s += '<div class="sidebar-section">' + TXT['keyword'] + '</div>'
        for k in sorted(KEYWORDS):
            s += '<a href="' + root + 'ref/keyword/' + k + '.html" class="sidebar-link">' + k + '</a>'
        s += '<div class="sidebar-section">' + TXT['builtin'] + '</div>'
        for k in sorted(BUILTINS):
            s += '<a href="' + root + 'ref/builtin/' + k + '.html" class="sidebar-link">' + k + '</a>'
        s += '<div class="sidebar-section">' + TXT['spec'] + '</div>'
        for slug, title, _ in SPEC:
            s += '<a href="' + root + 'spec/' + slug + '.html" class="sidebar-link">' + title + '</a>'
        return s

    def page(title, body, root='', prev=None, nxt=None, bc=None):
        bch = ''
        if bc:
            bch = '<div class="breadcrumb">'
            for i, (t, u) in enumerate(bc):
                bch += '<a href="' + u + '">' + t + '</a>' if u else '<span>' + t + '</span>'
                if i < len(bc) - 1: bch += '<span>&rsaquo;</span>'
            bch += '</div>'
        ph = ''
        if prev or nxt:
            ph = '<div class="pager">'
            if prev: ph += '<a class="pager-item prev" href="' + prev[1] + '"><span>' + TXT['prev'] + '</span><b>' + prev[0] + '</b></a>'
            else: ph += '<div></div>'
            if nxt: ph += '<a class="pager-item next" href="' + nxt[1] + '"><span>' + TXT['next'] + '</span><b>' + nxt[0] + '</b></a>'
            ph += '</div>'

        lang_switch = ('<div class="lang-switch">'
            '<a href="/docs/vi/" class="' + ('active' if lang_code=='vi' else '') + '">VI</a>'
            '<a href="/docs/en/" class="' + ('active' if lang_code=='en' else '') + '">EN</a>'
            '</div>')

        header = (
            '<div class="header">'
            '<a href="' + root + 'index.html" class="header-logo">Cat++<span>Docs</span></a>'
            '<a href="/" class="header-link">' + TXT['back_ide'] + '</a>'
            '<div class="header-spacer"></div>'
            + lang_switch +
            '<a href="' + root + 'tutorial/01-hello.html" class="header-link">' + TXT['tutorial'] + '</a>'
            '<a href="' + root + 'ref/keyword/meow.html" class="header-link">' + TXT['ref'] + '</a>'
            '<a href="' + root + 'spec/grammar.html" class="header-link">' + TXT['spec'] + '</a>'
            '<a href="/api/docs/download-txt?lang=' + lang_code + '" class="header-link dl" '
            'style="background:linear-gradient(135deg,#10b981,#059669)">📄 TXT</a>'
            '</div>'
        )

        return ('<!DOCTYPE html><html lang="' + lang_code + '"><head><meta charset="UTF-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>' + title + ' — Cat++ Docs</title>'
            '<link rel="stylesheet" href="' + root + 'style.css"></head><body>'
            '<div class="layout">' + header +
            '<aside class="sidebar">' + sidebar(root) + '</aside>'
            '<main class="content">' + bch + body + ph + '</main></div>'
            '<script src="' + root + 'app.js"></script></body></html>')

    home = ('<div class="hero"><h1>Cat++</h1><p>' + TXT['hero_p'] + '</p>'
        '<div class="hero-btns">'
        '<a href="tutorial/01-hello.html" class="btn btn-primary">' + TXT['hero_start'] + '</a>'
        '<a href="ref/keyword/meow.html" class="btn btn-secondary">' + TXT['hero_ref'] + '</a>'
        '<a href="/" class="btn btn-secondary">' + TXT['hero_ide'] + '</a></div></div>'
        '<h2>' + TXT['vidu'] + '</h2><pre><code>meow "Meow! Hello, Cat++!"\n\n'
        'paw cats = ["Tom", "Jerry"]\npurr greet(name)\n'
        '    meow "Xin chao, " + name + "!"\n\ngroom c of cats\n    greet(c)</code></pre>'
        '<h2>' + TXT['khampha'] + '</h2><div class="cards">'
        '<a class="card" href="tutorial/01-hello.html"><h3>' + TXT['tutorial'] + '</h3>'
        '<p>' + TXT['tut_desc'] + '</p></a>'
        '<a class="card" href="ref/keyword/meow.html"><h3>' + TXT['ref'] + '</h3>'
        '<p>' + TXT['ref_desc'] + '</p></a>'
        '<a class="card" href="spec/grammar.html"><h3>' + TXT['spec'] + '</h3>'
        '<p>' + TXT['spec_desc'] + '</p></a>'
        '<a class="card" href="/"><h3>Web IDE</h3>'
        '<p>' + TXT['ide_desc'] + '</p></a></div>'
        '<h2>' + TXT['thongke'] + '</h2><table>'
        '<tr><th>' + TXT['hangmuc'] + '</th><th>' + TXT['soluong'] + '</th></tr>'
        '<tr><td>' + TXT['tukhoa'] + '</td><td>' + str(len(KEYWORDS)) + '</td></tr>'
        '<tr><td>' + TXT['hamcosan'] + '</td><td>' + str(len(BUILTINS)) + '</td></tr>'
        '<tr><td>' + TXT['baitut'] + '</td><td>' + str(len(TUTORIAL)) + '</td></tr>'
        '<tr><td>' + TXT['tongtrang'] + '</td><td>' + str(1 + len(TUTORIAL) + len(KEYWORDS) + len(BUILTINS) + len(SPEC)) + '</td></tr>'
        '</table>')
    with open(site + '/index.html', 'w', encoding='utf-8') as f:
        f.write(page(TXT['home'], home, root='',
            nxt=(TUTORIAL[0][1], 'tutorial/' + TUTORIAL[0][0] + '.html'),
            bc=[(TXT['home'], None)]))

    for i, (slug, title, body) in enumerate(TUTORIAL):
        prev = (TXT['home'], '../index.html') if i == 0 else (TUTORIAL[i-1][1], TUTORIAL[i-1][0] + '.html')
        nxt = (TUTORIAL[i+1][1], TUTORIAL[i+1][0] + '.html') if i < len(TUTORIAL) - 1 else None
        with open(site + '/tutorial/' + slug + '.html', 'w', encoding='utf-8') as f:
            f.write(page(title, '<h1>' + title + '</h1>' + body, root='../',
                prev=prev, nxt=nxt,
                bc=[(TXT['home'], '../index.html'), (TXT['tutorial'], None), (title, None)]))

    kl = sorted(KEYWORDS)
    for i, k in enumerate(kl):
        d = KEYWORDS[k]
        body = '<h1>' + k + '</h1>'
        body += '<p><b>' + TXT['danhmuc'] + ':</b> ' + d['cat'] + ' &middot; <b>' + TXT['cuphap'] + ':</b> <code>' + html.escape(d['sig']) + '</code></p>'
        body += '<h2>' + TXT['mota'] + '</h2><p>' + d['desc'] + '</p>'
        if d.get('detail'): body += '<p>' + d['detail'] + '</p>'
        if d.get('ex'):
            body += '<h2>' + TXT['vidu'] + '</h2>'
            for e in d['ex']:
                body += '<h3>' + e[0] + '</h3>' + esc_code(e[1])
                if len(e) > 2 and e[2]: body += '<p><b>' + TXT['kq'] + ':</b> <code>' + html.escape(e[2]) + '</code></p>'
        prev = (kl[i-1], kl[i-1] + '.html') if i > 0 else (TXT['home'], '../../index.html')
        nxt = (kl[i+1], kl[i+1] + '.html') if i < len(kl) - 1 else None
        with open(site + '/ref/keyword/' + k + '.html', 'w', encoding='utf-8') as f:
            f.write(page(k, body, root='../../', prev=prev, nxt=nxt,
                bc=[(TXT['home'], '../../index.html'), (TXT['ref'], None), (TXT['keyword'], None), (k, None)]))

    bl = sorted(BUILTINS)
    for i, k in enumerate(bl):
        d = BUILTINS[k]
        body = '<h1><code>' + k + '()</code></h1>'
        body += '<p><b>' + TXT['danhmuc'] + ':</b> ' + d['cat'] + ' &middot; <b>' + TXT['chuky'] + ':</b> <code>' + html.escape(d['sig']) + '</code></p>'
        body += '<h2>' + TXT['mota'] + '</h2><p>' + d['desc'] + '</p>'
        if d.get('ex'):
            body += '<h2>' + TXT['vidu'] + '</h2>'
            for e in d['ex']:
                body += '<h3>' + e[0] + '</h3>' + esc_code(e[1])
                if len(e) > 2 and e[2]: body += '<p><b>' + TXT['kq'] + ':</b> <code>' + html.escape(e[2]) + '</code></p>'
        prev = (bl[i-1], bl[i-1] + '.html') if i > 0 else None
        nxt = (bl[i+1], bl[i+1] + '.html') if i < len(bl) - 1 else None
        with open(site + '/ref/builtin/' + k + '.html', 'w', encoding='utf-8') as f:
            f.write(page(k + '()', body, root='../../', prev=prev, nxt=nxt,
                bc=[(TXT['home'], '../../index.html'), (TXT['ref'], None), (TXT['builtin'], None), (k, None)]))

    for i, (slug, title, body) in enumerate(SPEC):
        prev = (TXT['home'], '../index.html') if i == 0 else (SPEC[i-1][1], SPEC[i-1][0] + '.html')
        nxt = (SPEC[i+1][1], SPEC[i+1][0] + '.html') if i < len(SPEC) - 1 else None
        with open(site + '/spec/' + slug + '.html', 'w', encoding='utf-8') as f:
            f.write(page(title, '<h1>' + title + '</h1>' + body, root='../',
                prev=prev, nxt=nxt,
                bc=[(TXT['home'], '../index.html'), (TXT['spec'], None), (title, None)]))

    total = 1 + len(TUTORIAL) + len(KEYWORDS) + len(BUILTINS) + len(SPEC)
    print('  [' + lang_code + '] ' + str(total) + ' trang')

def build():
    backup = SITE + '.bak'
    if os.path.exists(backup): shutil.rmtree(backup)
    if os.path.exists(SITE): shutil.move(SITE, backup)
    try:
        os.makedirs(SITE, exist_ok=True)
        import docs_data_vi, docs_data_en
        importlib.reload(docs_data_vi)
        importlib.reload(docs_data_en)
        # Merge extra
        try:
            import docs_extra_vi, docs_extra_en
            importlib.reload(docs_extra_vi)
            importlib.reload(docs_extra_en)
            docs_data_vi.KEYWORDS = {**docs_data_vi.KEYWORDS, **docs_extra_vi.KEYWORDS_EXTRA}
            docs_data_vi.BUILTINS = {**docs_data_vi.BUILTINS, **docs_extra_vi.BUILTINS_EXTRA}
            docs_data_en.KEYWORDS = {**docs_data_en.KEYWORDS, **docs_extra_en.KEYWORDS_EXTRA}
            docs_data_en.BUILTINS = {**docs_data_en.BUILTINS, **docs_extra_en.BUILTINS_EXTRA}
            print(f'  + Merged extras')
        except Exception as e:
            print(f'  ⚠ Không merge extra: {e}')
        print('Build docs:')
        build_lang('vi', docs_data_vi)
        build_lang('en', docs_data_en)
        redirect = '''<!DOCTYPE html><html><head><meta charset="UTF-8">
<title>Cat++ Docs</title>
<script>
  var lang = localStorage.getItem('catpp:lang') || 'vi';
  location.replace('/docs/' + lang + '/');
</script>
</head><body>
<p>Redirecting... <a href="/docs/vi/">VI</a> | <a href="/docs/en/">EN</a></p>
</body></html>'''
        with open(SITE + '/index.html', 'w', encoding='utf-8') as f:
            f.write(redirect)
        if os.path.exists(backup): shutil.rmtree(backup)
        print('OK')
    except Exception as e:
        if os.path.exists(backup):
            if os.path.exists(SITE): shutil.rmtree(SITE)
            shutil.move(backup, SITE)
        raise e

if __name__ == '__main__':
    build()
