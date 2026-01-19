#!/usr/bin/env python3
"""
Cross-platform Verilog simulation runner

Handles environment setup for Icarus Verilog on Windows/Linux/macOS.
IMPORTANT: Always use this script - never invoke iverilog/vvp directly!

Usage:
    python run_sim.py testbench.v module.v
    python run_sim.py -o output.vvp -I../gateware testbench.v module.v
    python run_sim.py --help

Author: Papilio Project
License: MIT
"""

import sys
import os
import platform
import subprocess
import argparse
from pathlib import Path


def setup_environment():
    """
    Set up environment for Icarus Verilog
    
    On Windows, returns the OSS CAD Suite path for environment.bat
    On Linux/macOS, assumes tools are in PATH
    
    Returns:
        Path to OSS CAD Suite on Windows, None otherwise
    """
    system = platform.system()
    
    if system == "Windows":
        # Try to find OSS CAD Suite installation
        possible_paths = [
            r"C:\oss-cad-suite",
            r"C:\Program Files\oss-cad-suite",
            os.path.expanduser(r"~\oss-cad-suite"),
        ]
        
        oss_cad_path = None
        for path in possible_paths:
            if os.path.exists(path):
                oss_cad_path = path
                break
        
        if oss_cad_path:
            print(f"Using OSS CAD Suite from: {oss_cad_path}", file=sys.stderr)
            return oss_cad_path
        else:
            print("WARNING: OSS CAD Suite not found in standard locations.", file=sys.stderr)
            print("         Assuming iverilog is in PATH.", file=sys.stderr)
            print("         If simulation fails, install OSS CAD Suite:", file=sys.stderr)
            print("         https://github.com/YosysHQ/oss-cad-suite-build", file=sys.stderr)
            return None
    
    elif system in ["Linux", "Darwin"]:  # Darwin = macOS
        # Assume tools are in PATH
        # Check if iverilog is available
        try:
            result = subprocess.run(["which", "iverilog"], 
                                  capture_output=True, 
                                  text=True)
            if result.returncode == 0:
                iverilog_path = result.stdout.strip()
                print(f"Using iverilog from: {iverilog_path}", file=sys.stderr)
            else:
                print("WARNING: iverilog not found in PATH.", file=sys.stderr)
                print("         Install Icarus Verilog or OSS CAD Suite.", file=sys.stderr)
        except Exception:
            pass
        return None
    
    else:
        print(f"WARNING: Unsupported platform: {system}", file=sys.stderr)
        return None


def compile_verilog(sources, output, include_dirs=None, standard="2012", oss_cad_path=None):
    """
    Compile Verilog sources with iverilog
    
    Args:
        sources: List of Verilog source files
        output: Output compiled file (.vvp)
        include_dirs: List of include directories
        standard: Verilog standard (2012, 2005, 2001)
        oss_cad_path: Path to OSS CAD Suite on Windows (for environment.bat)
    
    Returns:
        True if compilation succeeded, False otherwise
    """
    # Build iverilog command
    iverilog_cmd = ["iverilog"]
    
    # Add standard
    iverilog_cmd.extend([f"-g{standard}"])
    
    # Add output file
    iverilog_cmd.extend(["-o", output])
    
    # Add include directories
    if include_dirs:
        for inc_dir in include_dirs:
            iverilog_cmd.extend(["-I", inc_dir])
    
    # Add source files
    iverilog_cmd.extend(sources)
    
    # On Windows, wrap with cmd /c "call environment.bat && ..."
    if platform.system() == "Windows" and oss_cad_path:
        env_bat = os.path.join(oss_cad_path, "environment.bat")
        if os.path.exists(env_bat):
            # Build the full command string for cmd - use quotes properly
            iverilog_cmd_str = " ".join(iverilog_cmd)
            cmd = ["cmd", "/c", f'call {env_bat} && {iverilog_cmd_str}']
        else:
            cmd = iverilog_cmd
    else:
        cmd = iverilog_cmd
    
    print(f"Compiling: {' '.join(iverilog_cmd)}", file=sys.stderr)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        if result.stdout:
            print(result.stdout, file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        print(f"[PASS] Compilation successful: {output}", file=sys.stderr)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] Compilation failed!", file=sys.stderr)
        if e.stdout:
            print(e.stdout, file=sys.stderr)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        return False
    except FileNotFoundError:
        print(f"[ERROR] iverilog not found!", file=sys.stderr)
        print(f"        Make sure Icarus Verilog or OSS CAD Suite is installed.", file=sys.stderr)
        return False


def run_simulation(vvp_file, oss_cad_path=None):
    """
    Run compiled simulation with vvp
    
    Args:
        vvp_file: Compiled .vvp file
        oss_cad_path: Path to OSS CAD Suite on Windows (for environment.bat)
    
    Returns:
        True if simulation succeeded, False otherwise
    """
    vvp_cmd = ["vvp", vvp_file]
    
    # On Windows, wrap with cmd /c "call environment.bat && ..."
    if platform.system() == "Windows" and oss_cad_path:
        env_bat = os.path.join(oss_cad_path, "environment.bat")
        if os.path.exists(env_bat):
            # Build the full command string for cmd - use quotes properly
            vvp_cmd_str = " ".join(vvp_cmd)
            cmd = ["cmd", "/c", f'call {env_bat} && {vvp_cmd_str}']
        else:
            cmd = vvp_cmd
    else:
        cmd = vvp_cmd
    
    print(f"Running simulation: {' '.join(vvp_cmd)}", file=sys.stderr)
    print("="*60, file=sys.stderr)
    
    try:
        result = subprocess.run(cmd, check=True)
        
        print("="*60, file=sys.stderr)
        print(f"[PASS] Simulation complete", file=sys.stderr)
        return True
        
    except subprocess.CalledProcessError as e:
        print("="*60, file=sys.stderr)
        print(f"[FAIL] Simulation failed with exit code {e.returncode}", file=sys.stderr)
        return False
    except FileNotFoundError:
        print(f"[ERROR] vvp not found!", file=sys.stderr)
        print(f"   Make sure Icarus Verilog or OSS CAD Suite is installed.", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Cross-platform Verilog simulation runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compile and run testbench
  python run_sim.py testbench.v module.v
  
  # With include directories
  python run_sim.py -I../gateware -I../libs testbench.v
  
  # Specify output file
  python run_sim.py -o my_sim.vvp testbench.v module.v
  
  # Use Verilog 2005 standard
  python run_sim.py --std 2005 testbench.v module.v

Note: This script automatically handles environment setup.
      Never invoke iverilog/vvp directly!
"""
    )
    
    parser.add_argument('sources', nargs='+', 
                       help='Verilog source files')
    parser.add_argument('-o', '--output', default='sim.vvp',
                       help='Output file (default: sim.vvp)')
    parser.add_argument('-I', '--include', action='append', dest='include_dirs',
                       help='Include directory (can specify multiple times)')
    parser.add_argument('--std', '--standard', default='2012',
                       choices=['2001', '2005', '2009', '2012'],
                       help='Verilog standard (default: 2012)')
    parser.add_argument('--compile-only', action='store_true',
                       help='Compile only, do not run simulation')
    
    args = parser.parse_args()
    
    # Set up environment
    oss_cad_path = setup_environment()
    
    # Compile
    success = compile_verilog(
        sources=args.sources,
        output=args.output,
        include_dirs=args.include_dirs,
        standard=args.std,
        oss_cad_path=oss_cad_path
    )
    
    if not success:
        return 1
    
    # Run simulation (unless compile-only)
    if not args.compile_only:
        success = run_simulation(args.output, oss_cad_path=oss_cad_path)
        if not success:
            return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
