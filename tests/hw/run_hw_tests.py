#!/usr/bin/env python3
"""
Run hardware tests for papilio_dev_tools

Uses PlatformIO to build and run tests on target hardware.

Usage:
    python run_hw_tests.py
    python run_hw_tests.py --env esp32
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_tests(env='esp32'):
    """Run hardware tests"""
    print("="*60)
    print(f"Hardware Tests: papilio_dev_tools ({env})")
    print("="*60)
    
    # Build and run tests
    try:
        print("\nBuilding and uploading tests...")
        cmd = ["pio", "test", "-e", env]
        result = subprocess.run(cmd, check=True)
        
        print("\n[PASS] Hardware tests PASSED")
        return 0
        
    except subprocess.CalledProcessError as e:
        print(f"\n[FAIL] Hardware tests FAILED (exit code {e.returncode})")
        return 1
    except FileNotFoundError:
        print("[ERROR] PlatformIO CLI (pio) not found!")
        print("   Install PlatformIO: https://platformio.org/install")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="Run hardware tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run tests on ESP32 (default)
  python run_hw_tests.py
  
  # Run tests on specific environment
  python run_hw_tests.py --env esp32
  
  # Run tests on native (host PC)
  python run_hw_tests.py --env native
"""
    )
    
    parser.add_argument('--env', '-e', default='esp32',
                       help='Test environment (default: esp32)')
    
    args = parser.parse_args()
    
    return run_tests(args.env)


if __name__ == "__main__":
    sys.exit(main())
