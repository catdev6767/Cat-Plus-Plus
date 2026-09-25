#!/bin/bash
cd "$(dirname "$0")"
pkill -f "python3 catpp.py" 2>/dev/null
sleep 1
echo "Cat++ IDE: http://localhost:5000"
python3 catpp.py
