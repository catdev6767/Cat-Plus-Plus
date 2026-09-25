#!/usr/bin/env python3
"""Dev server — serve IDE + landing + docs."""
import http.server, socketserver, os, sys

PORT = int(os.environ.get('PORT', 5000))
ROOT = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def do_GET(self):
        # Route / -> landing
        if self.path == '/':
            self.path = '/index.html'
        # /ide -> ide/index.html
        elif self.path in ('/ide', '/ide/'):
            self.path = '/ide/index.html'
        # /docs -> static/docs
        elif self.path.startswith('/docs'):
            self.path = '/static/docs' + self.path[5:]
            if self.path == '/static/docs' or self.path == '/static/docs/':
                self.path = '/static/docs/index.html'
        return super().do_GET()

    def log_message(self, *a):
        pass

with socketserver.TCPServer(('0.0.0.0', PORT), Handler) as httpd:
    print(f'🐱 Cat++ dev server: http://localhost:{PORT}')
    print(f'   Landing: http://localhost:{PORT}/')
    print(f'   IDE:     http://localhost:{PORT}/ide/')
    httpd.serve_forever()
