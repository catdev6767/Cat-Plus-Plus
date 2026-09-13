"""Loader — tự động tìm và load modules."""

import os
import json
import importlib
from .module import BaseModule
from .registry import Registry
from .bus import EventBus


class Loader:
    def __init__(self, modules_dir='modules', config_file='config.json'):
        self.modules_dir = modules_dir
        self.config = self._load_config(config_file)
        self.registry = Registry()
        self.bus = EventBus()
        self.modules = {}

    def _load_config(self, path):
        if not os.path.exists(path):
            return {'modules': {}}
        try:
            with open(path, encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f'[loader] Lỗi đọc config: {e}')
            return {'modules': {}}

    def _is_enabled(self, name):
        cfg = self.config.get('modules', {}).get(name, {})
        return cfg.get('enabled', True)

    def load_all(self):
        if not os.path.isdir(self.modules_dir):
            print(f'[loader] Không tìm thấy thư mục {self.modules_dir}/')
            return

        for name in sorted(os.listdir(self.modules_dir)):
            if name.startswith('_') or name.startswith('.'):
                continue
            path = os.path.join(self.modules_dir, name)
            if not os.path.isdir(path):
                continue
            mod_file = os.path.join(path, 'module.py')
            if not os.path.exists(mod_file):
                continue

            if not self._is_enabled(name):
                print(f'[loader] Bỏ qua {name} (disabled)')
                continue

            try:
                mod = importlib.import_module(f'{self.modules_dir}.{name}.module')
                cls = None
                for attr_name in dir(mod):
                    attr = getattr(mod, attr_name)
                    if (isinstance(attr, type)
                        and issubclass(attr, BaseModule)
                        and attr is not BaseModule
                        and attr.__module__ == mod.__name__):
                        cls = attr
                        break

                if cls is None:
                    print(f'[loader] {name}: không tìm thấy class BaseModule')
                    continue

                instance = cls(self.registry, self.bus)
                self.modules[name] = instance
                print(f'[loader] Loaded {name} v{instance.version}')
            except Exception as e:
                print(f'[loader] Lỗi load {name}: {e}')
                import traceback
                traceback.print_exc()

    def setup_all(self):
        ordered = self._topo_sort()
        for name in ordered:
            mod = self.modules[name]
            try:
                mod.setup()
                print(f'[loader] Setup {name} OK')
            except Exception as e:
                print(f'[loader] Setup {name} lỗi: {e}')
                import traceback
                traceback.print_exc()

    def start_all(self):
        for name, mod in self.modules.items():
            try:
                mod.start()
            except Exception as e:
                print(f'[loader] Start {name} lỗi: {e}')

    def stop_all(self):
        for name, mod in reversed(list(self.modules.items())):
            try:
                mod.stop()
            except Exception:
                pass

    def _topo_sort(self):
        visited = set()
        result = []

        def visit(name):
            if name in visited: return
            visited.add(name)
            mod = self.modules.get(name)
            if mod:
                for dep in getattr(mod, 'dependencies', []):
                    if dep in self.modules:
                        visit(dep)
            result.append(name)

        for name in sorted(self.modules.keys()):
            visit(name)
        return result
