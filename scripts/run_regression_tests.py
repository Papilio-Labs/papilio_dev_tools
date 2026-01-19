#!/usr/bin/env python3
"""
Regression test runner template for Papilio libraries

This script runs both simulation and hardware tests.
Copy to your library root and customize as needed.

Usage:
    python run_regression_tests.py
    python run_regression_tests.py --sim-only
    python run_regression_tests.py --hw-only
    python run_regression_tests.py --help

Author: Papilio Project
License: MIT
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path


def run_sim_tests(verbose=False):
    """Run simulation tests"""
    print("\n" + "="*60)
    print("Running Simulation Tests")
    print("="*60)
    
    sim_dir = Path("tests/sim")
    
    if not sim_dir.exists():
        print("[WARN] No simulation tests found (tests/sim/ does not exist)")
        return True
    
    run_script = sim_dir / "run_all_sims.py"
    
    if not run_script.exists():
        print("[WARN] No simulation runner found (tests/sim/run_all_sims.py)")
        return True
    
    try:
        # Run from the sim directory, pass only the script name
        cmd = [sys.executable, "run_all_sims.py"]
        result = subprocess.run(
            cmd,
            cwd=str(sim_dir),
            check=True,
            capture_output=not verbose
        )
        
        if result.stdout and verbose:
            print(result.stdout.decode())
        
        print("[PASS] Simulation tests PASSED")
        return True
        
    except subprocess.CalledProcessError as e:
        print("[FAIL] Simulation tests FAILED")
        if e.stdout:
            print(e.stdout.decode())
        if e.stderr:
            print(e.stderr.decode())
        return False
    except Exception as e:
        print(f"[ERROR] Error running simulation tests: {e}")
        return False


def run_hw_tests(verbose=False):
    """Run hardware tests"""
    print("\n" + "="*60)
    print("Running Hardware Tests")
    print("="*60)
    
    hw_dir = Path("tests/hw")
    
    if not hw_dir.exists():
        print("[WARN] No hardware tests found (tests/hw/ does not exist)")
        return True
    
    run_script = hw_dir / "run_hw_tests.py"
    
    if not run_script.exists():
        print("[WARN] No hardware test runner found (tests/hw/run_hw_tests.py)")
        return True
    
    try:
        # Run from the hw directory, pass only the script name
        cmd = [sys.executable, "run_hw_tests.py"]
        result = subprocess.run(
            cmd,
            cwd=str(hw_dir),
            check=True,
            capture_output=not verbose
        )
        
        if result.stdout and verbose:
            print(result.stdout.decode())
        
        print("[PASS] Hardware tests PASSED")
        return True
        
    except subprocess.CalledProcessError as e:
        print("[FAIL] Hardware tests FAILED")
        if e.stdout:
            print(e.stdout.decode())
        if e.stderr:
            print(e.stderr.decode())
        return False
    except Exception as e:
        print(f"[ERROR] Error running hardware tests: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Run regression tests (simulation + hardware)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests
  python run_regression_tests.py
  
  # Run simulation tests only
  python run_regression_tests.py --sim-only
  
  # Run hardware tests only
  python run_regression_tests.py --hw-only
  
  # Verbose output
  python run_regression_tests.py -v
"""
    )
    
    parser.add_argument('--sim-only', action='store_true',
                       help='Run simulation tests only')
    parser.add_argument('--hw-only', action='store_true',
                       help='Run hardware tests only')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    # Track results
    results = []
    
    # Run tests based on arguments
    if not args.hw_only:
        results.append(("Simulation", run_sim_tests(args.verbose)))
    
    if not args.sim_only:
        results.append(("Hardware", run_hw_tests(args.verbose)))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    all_passed = True
    for test_type, passed in results:
        status = "PASS" if passed else "FAIL"
        symbol = "[PASS]" if passed else "[FAIL]"
        print(f"{symbol} {test_type}: {status}")
        all_passed = all_passed and passed
    
    print("="*60)
    
    if all_passed:
        print("\n*** All tests passed! ***")
        return 0
    else:
        print("\n*** Some tests failed! ***")
        return 1


if __name__ == "__main__":
    sys.exit(main())
