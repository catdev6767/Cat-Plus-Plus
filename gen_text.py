#!/usr/bin/env python3
import sys, os, re, io
import html as htmllib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import docs_data_en

def strip_tags(s):
    s = re.sub(r'<pre><code>(.*?)</code></pre>',
               lambda m: '\n```\n' + htmllib.unescape(m.group(1)) + '\n```\n',
               s, flags=re.DOTALL)
    s = re.sub(r'<code>(.*?)</code>', lambda m: '`' + htmllib.unescape(m.group(1)) + '`', s)
    s = re.sub(r'<h1>(.*?)</h1>', r'\n# \1\n', s)
    s = re.sub(r'<h2>(.*?)</h2>', r'\n## \1\n', s)
    s = re.sub(r'<h3>(.*?)</h3>', r'\n### \1\n', s)
    s = re.sub(r'<b>(.*?)</b>', r'**\1**', s)
    s = re.sub(r'<i>(.*?)</i>', r'*\1*', s)
    s = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'[\2](\1)', s)
    s = re.sub(r'<li>(.*?)</li>', r'- \1\n', s)
    s = re.sub(r'</?ul>|</?ol>', '', s)
    s = re.sub(r'<p>(.*?)</p>', r'\1\n\n', s)
    s = re.sub(r'<table>.*?</table>', '', s, flags=re.DOTALL)
    s = re.sub(r'<[^>]+>', '', s)
    s = htmllib.unescape(s)
    return re.sub(r'\n{3,}', '\n\n', s).strip()

def build_md(lang):
    m = docs_data_en
    K, B, TUT, SP = m.KEYWORDS, m.BUILTINS, m.TUTORIAL, m.SPEC
    if lang == 'vi':
        T = {'title':'Cat++ Documentation — Tiếng Việt','toc':'Mục lục',
             'tut':'Tutorial','kw':'Từ khóa','bi':'Hàm có sẵn','spec':'Đặc tả',
             'cat':'Danh mục','sig':'Cú pháp','desc':'Mô tả','ex':'Ví dụ',
             'kq':'Kết quả','sig2':'Chữ ký'}
    else:
        T = {'title':'Cat++ Documentation — English','toc':'Table of Contents',
             'tut':'Tutorial','kw':'Keywords','bi':'Builtins','spec':'Specification',
             'cat':'Category','sig':'Syntax','desc':'Description','ex':'Examples',
             'kq':'Result','sig2':'Signature'}
    out = io.StringIO()
    out.write('# ' + T['title'] + '\n\n---\n\n## ' + T['toc'] + '\n\n')
    for i, (s, t, _) in enumerate(TUT, 1): out.write(str(i) + '. ' + t + '\n')
    out.write('\n### ' + T['kw'] + '\n')
    for k in sorted(K): out.write('- ' + k + '\n')
    out.write('\n### ' + T['bi'] + '\n')
    for k in sorted(B): out.write('- ' + k + '()\n')
    out.write('\n### ' + T['spec'] + '\n')
    for s, t, _ in SP: out.write('- ' + t + '\n')
    out.write('\n---\n\n# ' + T['tut'] + '\n\n---\n\n')
    for s, t, b in TUT: out.write('# ' + t + '\n\n' + strip_tags(b) + '\n\n---\n\n')
    out.write('# ' + T['kw'] + '\n\n---\n\n')
    for k in sorted(K):
        d = K[k]
        out.write('# ' + k + '\n\n**' + T['cat'] + ':** ' + d['cat'] + '  \n')
        out.write('**' + T['sig'] + ':** `' + d['sig'] + '`\n\n## ' + T['desc'] + '\n\n')
        out.write(d['desc'] + '\n\n')
        if d.get('detail'): out.write(strip_tags(d['detail']) + '\n\n')
        if d.get('ex'):
            out.write('## ' + T['ex'] + '\n\n')
            for e in d['ex']:
                out.write('### ' + e[0] + '\n\n```cat\n' + e[1] + '\n```\n\n')
                if len(e) > 2 and e[2]: out.write('**' + T['kq'] + ':** `' + e[2] + '`\n\n')
        out.write('---\n\n')
    out.write('# ' + T['bi'] + '\n\n---\n\n')
    for k in sorted(B):
        d = B[k]
        out.write('# ' + k + '()\n\n**' + T['cat'] + ':** ' + d['cat'] + '  \n')
        out.write('**' + T['sig2'] + ':** `' + d['sig'] + '`\n\n## ' + T['desc'] + '\n\n')
        out.write(d['desc'] + '\n\n')
        if d.get('ex'):
            out.write('## ' + T['ex'] + '\n\n')
            for e in d['ex']:
                out.write('### ' + e[0] + '\n\n```cat\n' + e[1] + '\n```\n\n')
                if len(e) > 2 and e[2]: out.write('**' + T['kq'] + ':** `' + e[2] + '`\n\n')
        out.write('---\n\n')
    out.write('# ' + T['spec'] + '\n\n---\n\n')
    for s, t, b in SP: out.write('# ' + t + '\n\n' + strip_tags(b) + '\n\n---\n\n')
    return out.getvalue()

def build_txt(lang):
    md = build_md(lang)
    md = re.sub(r'^#{1,6}\s+', '', md, flags=re.MULTILINE)
    md = re.sub(r'\*\*(.*?)\*\*', r'\1', md)
    md = re.sub(r'\*(.*?)\*', r'\1', md)
    md = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', md)
    md = re.sub(r'```\w*\n', '--- CODE ---\n', md)
    md = re.sub(r'\n```', '\n--- END ---', md)
    md = re.sub(r'`([^`]+)`', r'\1', md)
    md = re.sub(r'^---+$', '=' * 60, md, flags=re.MULTILINE)
    return md

if __name__ == '__main__':
    os.makedirs('static/docs', exist_ok=True)
    for lang in ['en']:
        md = build_md(lang)
        with open('static/docs/catpp-docs-' + lang + '.md', 'w', encoding='utf-8') as f:
            f.write(md)
        txt = build_txt(lang)
        with open('static/docs/catpp-docs-' + lang + '.txt', 'w', encoding='utf-8') as f:
            f.write(txt)
        print('  [' + lang + '] md=' + str(len(md)) + 'B, txt=' + str(len(txt)) + 'B')
    print('OK')
