"""Module server — chạy HTTP server trong thread."""
import sys, os, threading
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.module import BaseModule


class ServerModule(BaseModule):
    name = 'server'
    version = '2.0.0'
    dependencies = ['interpreter']

    def __init__(self, registry, bus):
        super().__init__(registry, bus)
        self.httpd = None
        self.thread = None
        self.port = 5000

    def setup(self):
        self.registry.set('server', self)

    def start(self):
        from server import create_server
        self.httpd = create_server(self.port)
        self.thread = threading.Thread(
            target=self.httpd.serve_forever,
            daemon=True,
            name='catpp-server'
        )
        self.thread.start()
        print(f'[server] Đang chạy http://localhost:{self.port}')

    def stop(self):
        if self.httpd:
            try:
                self.httpd.shutdown()
                self.httpd.server_close()
            except Exception:
                pass
            print('[server] Đã dừng')
