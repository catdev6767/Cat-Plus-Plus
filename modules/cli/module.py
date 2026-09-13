"""Module CLI — chạy catpp CLI."""
import sys, os, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.module import BaseModule


class CLIModule(BaseModule):
    name = 'cli'
    version = '2.0.0'
    dependencies = ['interpreter']

    def setup(self):
        self.registry.set('cli', self)

    def run(self, args):
        cli_path = os.path.join(ROOT, 'catpp')
        if not os.path.exists(cli_path):
            print(f'Lỗi: không tìm thấy {cli_path}')
            return 1
        result = subprocess.run(
            [sys.executable, cli_path] + list(args),
            cwd=ROOT
        )
        return result.returncode
