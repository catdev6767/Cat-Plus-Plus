#!/usr/bin/env python3
from http.server import HTTPServer, SimpleHTTPRequestHandler
from interpreter import run_catpp, CatError

# Engine nhanh (tuỳ chọn)
try:
    from catpp_pycompiler import run_catpp_py, Unsupported as PyUnsupported
    HAVE_PYCOMPILER = True
except Exception:
    HAVE_PYCOMPILER = False

def run_catpp_fast(code, timeout=5.0):
    """Thử PyCompiler trước, fallback interpreter."""
    if HAVE_PYCOMPILER:
        try:
            return run_catpp_py(code, timeout=timeout)
        except PyUnsupported:
            pass
        except Exception:
            pass  # Lỗi runtime → fallback
    return run_catpp(code, timeout=timeout)
import json, time, threading, os

PORT = 5000
RATE = {}
LOCK = threading.Lock()

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory='static', **kw)

    def guess_type(self, path):
        mt = super().guess_type(path)
        if mt and ('text/' in mt or 'javascript' in mt or 'json' in mt) and 'charset' not in mt:
            mt += '; charset=utf-8'
        return mt

    def do_GET(self):
        # /api/public-url — trả public URL nếu có tunnel
        if self.path == '/api/public-url':
            url = ''
            # Ưu tiên theo thứ tự
            candidates = [
                '/tmp/catpp-url.txt',
                '/tmp/ngrok-url.txt',
                '/tmp/tailscale-url.txt',
            ]
            for path in candidates:
                if os.path.exists(path):
                    try:
                        with open(path) as fh:
                            u = fh.read().strip()
                            if u and u.startswith('http'):
                                url = u
                                break
                    except Exception:
                        pass
            # Kiểm tra env biến (nếu chạy qua tailscale funnel)
            if not url:
                url = os.environ.get('CATPP_PUBLIC_URL', '')
            data = json.dumps({'url': url, 'has_tunnel': bool(url)}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        # / → landing
        if self.path in ('/', '/index.html'):
            self.path = '/landing.html'
            return super().do_GET()
        # /ide/ → IDE
        if self.path in ('/ide', '/ide/'):
            self.path = '/index.html'
            return super().do_GET()
        # Endpoint trả public URL
        # Landing ở /
        if self.path in ('/', '/index.html'):
            self.path = '/landing.html'
            return super().do_GET()
        # /ide → IDE
        if self.path in ('/ide', '/ide/'):
            self.path = '/index.html'
            return super().do_GET()
        # MD download
        if self.path.startswith('/api/docs/download-md'):
            return self._serve_text('md')
        # TXT download
        if self.path.startswith('/api/docs/download-txt'):
            return self._serve_text('txt')
        # ZIP download
        if self.path == '/api/docs/download':
            return self._serve_zip()
        # Redirect /docs -> /docs/
        if self.path == '/docs':
            self.send_response(301)
            self.send_header('Location', '/docs/')
            self.end_headers()
            return
        return super().do_GET()

    def _serve_text(self, fmt):
        # Parse ?lang=vi|en
        lang = 'vi'
        if '?' in self.path:
            qs = self.path.split('?', 1)[1]
            for pair in qs.split('&'):
                if pair.startswith('lang='):
                    v = pair[5:]
                    if v in ('vi', 'en'):
                        lang = v
        fname = 'catpp-docs-' + lang + '.' + fmt
        path = os.path.join('static/docs', fname)
        if not os.path.exists(path):
            self.send_error(404, 'Not found: ' + fname)
            return
        with open(path, 'rb') as f:
            data = f.read()
        mime = 'text/markdown' if fmt == 'md' else 'text/plain'
        self.send_response(200)
        self.send_header('Content-Type', mime + '; charset=utf-8')
        self.send_header('Content-Disposition', 'attachment; filename="' + fname + '"')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _serve_zip(self):
        import zipfile, io
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, fs in os.walk('static/docs'):
                for fname in fs:
                    full = os.path.join(root, fname)
                    rel = os.path.relpath(full, 'static/docs')
                    zf.write(full, rel)
        data = buf.getvalue()
        self.send_response(200)
        self.send_header('Content-Type', 'application/zip')
        self.send_header('Content-Disposition', 'attachment; filename="catpp-docs.zip"')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path == '/api/run':
            ip = self.client_address[0]
            now = time.time()
            with LOCK:
                RATE.setdefault(ip, [])
                RATE[ip] = [t for t in RATE[ip] if now - t < 60]
                if len(RATE[ip]) >= 60:
                    return self._json({'ok': False, 'output': 'Qua nhanh', 'line': 0}, 429)
                RATE[ip].append(now)
            n = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(n) or b'{}')
            try:
                out = run_catpp_fast(body.get('code', ''), timeout=5.0)
                self._json({'ok': True, 'output': out, 'line': 0})
            except CatError as e:
                self._json({'ok': False, 'output': str(e), 'line': getattr(e, 'line', 0)})
            except Exception as e:
                self._json({'ok': False, 'output': f'{type(e).__name__}: {e}', 'line': 0})
        else:
            self.send_error(404)

    def _json(self, obj, code=200):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass

def create_server(port=PORT):
    return HTTPServer(('0.0.0.0', port), Handler)


if __name__ == '__main__':
    print(f'Cat++ IDE: http://localhost:{PORT}')
    create_server().serve_forever()
