#!/bin/bash
# Use the Python 3.12 environment where all packages are installed
PYTHON="/Library/Frameworks/Python.framework/Versions/3.12/bin/python3"
cd "$(dirname "$0")"
"$PYTHON" app.py
