# Cat++ v1.0 — Docker image
# Build:  docker build -t catpp:1.0 .
# Run:    docker run -p 5000:5000 catpp:1.0
# Mở:     http://localhost:5000

FROM python:3.12-slim

LABEL maintainer="Cat++ Team"
LABEL description="Cat++ language, IDE, and transpiler"
LABEL version="1.0.0"

WORKDIR /app

# Copy source
COPY . .

# Không cần pip install — dùng Python stdlib
# Chỉ expose port
EXPOSE 5000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/')" || exit 1

# Start server
CMD ["python3", "catpp.py"]
