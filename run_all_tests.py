#!/usr/bin/env python3
"""
Top-level test runner for papilio_dev_tools

This is an example of how to use the regression test infrastructure.
Copy this pattern to your library root directory.

Usage:
    python run_all_tests.py
    python run_all_tests.py --sim-only
    python run_all_tests.py --hw-only

Author: Papilio Project
License: MIT
"""

import sys
import subprocess
from pathlib import Path

# Use the regression test runner from scripts
script_path = Path(__file__).parent / "scripts" / "run_regression_tests.py"

if __name__ == "__main__":
    # Pass all arguments to the regression test runner
    # Run from the library root directory
    lib_root = Path(__file__).parent
    result = subprocess.run(
        [sys.executable, str(script_path)] + sys.argv[1:],
        cwd=str(lib_root)
    )
    sys.exit(result.returncode)
