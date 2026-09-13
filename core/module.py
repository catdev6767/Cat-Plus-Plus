"""Base class cho mọi module."""

class BaseModule:
    name = 'unnamed'
    version = '0.0.0'
    dependencies = []

    def __init__(self, registry, bus):
        self.registry = registry
        self.bus = bus

    def setup(self):
        """Đăng ký API, lắng nghe event. Gọi 1 lần khi load."""
        pass

    def start(self):
        """Bắt đầu hoạt động (mở port, thread). Gọi sau setup."""
        pass

    def stop(self):
        """Dọn dẹp khi tắt."""
        pass
