#!/usr/bin/env python3
"""
Run all simulation tests in this directory

Discovers all tb_*.v files and runs them with proper environment setup.

Usage:
    python run_all_sims.py
"""

import sys
import os
import glob
import subprocess
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

# Import run_sim module
try:
    import run_sim
except ImportError:
    print("Error: Could not import run_sim module", file=sys.stderr)
    print(f"Looking in: {scripts_dir}", file=sys.stderr)
    sys.exit(1)


def find_testbenches():
    """Find all testbench files (tb_*.v)"""
    testbenches = glob.glob("tb_*.v")
    return sorted(testbenches)


def run_testbench(testbench, oss_cad_path):
    """Run a single testbench"""
    print(f"\n{'='*60}")
    print(f"Running: {testbench}")
    print('='*60)
    
    # Compile
    output = testbench.replace('.v', '.vvp')
    success = run_sim.compile_verilog(
        sources=[testbench],
        output=output,
        include_dirs=None,
        standard="2012",
        oss_cad_path=oss_cad_path
    )
    
    if not success:
        return False
    
    # Run
    success = run_sim.run_simulation(output, oss_cad_path=oss_cad_path)
    
    return success


def main():
    print("="*60)
    print("Papilio Dev Tools - Simulation Test Runner")
    print("="*60)
    
    # Set up environment
    oss_cad_path = run_sim.setup_environment()
    
    # Find testbenches
    testbenches = find_testbenches()
    
    if not testbenches:
        print("No testbenches found (no tb_*.v files)")
        return 0
    
    print(f"\nFound {len(testbenches)} testbench(es):")
    for tb in testbenches:
        print(f"  - {tb}")
    
    # Run each testbench
    results = []
    for tb in testbenches:
        success = run_testbench(tb, oss_cad_path)
        results.append((tb, success))
    
    # Summary
    print(f"\n{'='*60}")
    print("Test Summary")
    print('='*60)
    
    passed = sum(1 for _, success in results if success)
    failed = len(results) - passed
    
    for tb, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status}: {tb}")
    
    print(f"\nTotal: {len(results)} | Passed: {passed} | Failed: {failed}")
    
    if failed == 0:
        print("\n*** All simulation tests passed! ***")
        return 0
    else:
        print(f"\n*** {failed} test(s) failed! ***")
        return 1


if __name__ == "__main__":
    sys.exit(main())
