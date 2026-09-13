"""Event Bus — module phát và lắng nghe sự kiện."""

class EventBus:
    def __init__(self):
        self._listeners = {}

    def on(self, event, handler):
        self._listeners.setdefault(event, []).append(handler)

    def off(self, event, handler):
        if event in self._listeners:
            try:
                self._listeners[event].remove(handler)
            except ValueError:
                pass

    def emit(self, event, data=None):
        for h in self._listeners.get(event, []):
            try:
                h(data)
            except Exception as e:
                print(f'[bus] Lỗi trong handler của "{event}": {e}')

    def clear(self):
        self._listeners.clear()
