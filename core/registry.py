"""Registry — module đăng ký API, module khác tra cứu."""

class Registry:
    def __init__(self):
        self._items = {}

    def set(self, name, value):
        self._items[name] = value

    def get(self, name, default=None):
        return self._items.get(name, default)

    def has(self, name):
        return name in self._items

    def list(self):
        return sorted(self._items.keys())
