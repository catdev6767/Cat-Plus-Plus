#!/usr/bin/env python3
"""Cat++ v2.0 — Entry point."""
import sys, os, signal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.loader import Loader


CLI_COMMANDS = ('run', 'repl', 'fmt', 'lint', 'test', '--help', '-h', '--version')


def main():
    argv = sys.argv[1:]

    if argv and argv[0] in CLI_COMMANDS:
        loader = Loader('modules', 'config.json')
        loader.load_all()
        loader.setup_all()
        cli = loader.registry.get('cli')
        if cli is None:
            print('Lỗi: module cli chưa load')
            return 1
        return cli.run(argv)

    print('🐱 Cat++ v2.0 đang khởi động...')
    print()

    loader = Loader('modules', 'config.json')
    loader.load_all()
    print()
    loader.setup_all()
    print()
    loader.start_all()
    print()

    print('─' * 50)
    print('  🐱 Cat++ IDE + Docs đã sẵn sàng')
    print('─' * 50)
    print('  IDE:   http://localhost:5000/')
    print('  Docs:  http://localhost:5000/docs/')
    print()
    print('  Ctrl+C để tắt')
    print('─' * 50)
    print()

    try:
        signal.pause()
    except KeyboardInterrupt:
        pass
    finally:
        print()
        print('Đang tắt...')
        loader.stop_all()
        print('👋 Tạm biệt!')

    return 0


if __name__ == '__main__':
    sys.exit(main())
