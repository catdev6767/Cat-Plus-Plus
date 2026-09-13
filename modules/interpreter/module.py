"""Module interpreter — wrap interpreter.py."""
import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.module import BaseModule


class InterpreterModule(BaseModule):
    name = 'interpreter'
    version = '2.0.0'
    dependencies = []

    def setup(self):
        self.registry.set('interpreter', self)
        self.bus.on('code.run', self._on_code_run)

    def _on_code_run(self, data):
        if not isinstance(data, dict):
            return
        code = data.get('code', '')
        timeout = data.get('timeout', 5.0)
        try:
            data['result'] = {'ok': True, 'output': self.run(code, timeout)}
        except Exception as e:
            data['result'] = {
                'ok': False,
                'output': str(e),
                'line': getattr(e, 'line', 0)
            }

    def run(self, code, timeout=5.0, read_input=None):
        from interpreter import run_catpp
        return run_catpp(code, timeout=timeout, read_input=read_input)

    def keywords(self):
        try:
            from interpreter import KEYWORDS
            return sorted(KEYWORDS)
        except Exception:
            return []
