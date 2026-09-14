.PHONY: help run test test-verbose test-cli clean install docs build lint format check

PY = python3

help:
	@echo "🐱 Cat++ v2.0 — Makefile"
	@echo ""
	@echo "  make run           Chạy IDE server"
	@echo "  make test          Chạy toàn bộ test"
	@echo "  make test-cli      Test CLI"
	@echo "  make clean         Xóa cache, file tạm"
	@echo "  make install       Cài catpp vào ~/.local/bin"
	@echo "  make docs          Sinh lại tài liệu"
	@echo "  make build         Build từ source"
	@echo "  make lint          Chạy linter"
	@echo "  make format        Format code"
	@echo "  make check         Kiểm tra trạng thái"
	@echo ""

run:
	$(PY) catpp.py

test:
	@$(PY) tests/test_all.py

test-cli:
	@echo "Test CLI..."
	@$(PY) catpp.py --version
	@$(PY) catpp.py run examples/hello.cat
	@echo "✓ CLI OK"

test-verbose:
	@$(PY) tests/test_all.py 2>&1 | grep -E "✗|FAIL|ERROR" || echo "✓ Tất cả pass"

clean:
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf .pytest_cache/ 2>/dev/null || true
	@echo "✓ Đã dọn cache"

install:
	@bash install.sh 2>/dev/null || echo "Không có install.sh"

docs:
	@$(PY) gen_docs.py
	@$(PY) gen_text.py 2>/dev/null || true
	@echo "✓ Đã sinh lại docs"

build:
	@echo "Build không cần thiết — chạy trực tiếp bằng Python"
	@echo "  python3 catpp.py"

lint:
	@$(PY) catpp.py lint examples/hello.cat 2>/dev/null || true

format:
	@$(PY) catpp.py fmt examples/hello.cat -w 2>/dev/null || true

check:
	@echo "═══ Kiểm tra hệ thống ═══"
	@echo "Python: $$($(PY) --version)"
	@echo ""
	@echo "Files:"
	@for f in catpp.py config.json core/loader.py interpreter.py server.py; do \
		if [ -f "$$f" ]; then echo "  ✓ $$f"; else echo "  ✗ $$f"; fi \
	done
	@echo ""
	@echo "Modules:"
	@for m in interpreter server cli; do \
		if [ -f "modules/$$m/module.py" ]; then echo "  ✓ $$m"; else echo "  ✗ $$m"; fi \
	done
	@echo ""
	@echo "Chạy 'make test' để kiểm tra chức năng"

# ═══ Felis OS ═══
build-catos:
	@bash build_felis.sh

run-felis: build-catos
	@if [ -f felis.iso ]; then \
		qemu-system-x86_64 -cdrom felis.iso; \
	else \
		echo "Chưa có felis.iso"; \
	fi

felis-clean:
	@rm -f kernel/*.o kernel/*.elf kernel/demo.c felis.iso
	@rm -rf iso/
	@echo "✓ Đã xóa build Felis OS"
