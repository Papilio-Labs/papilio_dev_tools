#!/usr/bin/env python3
"""
Test report generator for Papilio libraries

Aggregates test results from simulation and hardware tests and generates reports.

Usage:
    python generate_test_report.py --sim results/sim.json --hw results/hw.json
    python generate_test_report.py --format markdown --output report.md
    python generate_test_report.py --help

Author: Papilio Project
License: MIT
"""

import sys
import os
import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


class TestReport:
    """Test report generator"""
    
    def __init__(self):
        self.sim_results = {}
        self.hw_results = {}
        self.timestamp = datetime.now()
    
    def load_sim_results(self, filepath: str):
        """Load simulation test results from JSON file"""
        try:
            with open(filepath, 'r') as f:
                self.sim_results = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load sim results: {e}", file=sys.stderr)
    
    def load_hw_results(self, filepath: str):
        """Load hardware test results from JSON file"""
        try:
            with open(filepath, 'r') as f:
                self.hw_results = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load hw results: {e}", file=sys.stderr)
    
    def generate_markdown(self) -> str:
        """Generate Markdown format report"""
        lines = []
        
        # Header
        lines.append("# Test Report")
        lines.append(f"\n**Generated**: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Summary
        lines.append("## Summary")
        lines.append("")
        
        sim_total = len(self.sim_results.get('tests', []))
        sim_passed = sum(1 for t in self.sim_results.get('tests', []) if t.get('passed'))
        
        hw_total = len(self.hw_results.get('tests', []))
        hw_passed = sum(1 for t in self.hw_results.get('tests', []) if t.get('passed'))
        
        total_tests = sim_total + hw_total
        total_passed = sim_passed + hw_passed
        
        lines.append(f"- **Total Tests**: {total_tests}")
        lines.append(f"- **Passed**: {total_passed}")
        lines.append(f"- **Failed**: {total_tests - total_passed}")
        lines.append(f"- **Success Rate**: {100.0 * total_passed / total_tests if total_tests > 0 else 0:.1f}%")
        lines.append("")
        
        # Simulation Results
        if self.sim_results:
            lines.append("## Simulation Tests")
            lines.append("")
            lines.append(f"**Total**: {sim_total} | **Passed**: {sim_passed} | **Failed**: {sim_total - sim_passed}")
            lines.append("")
            
            if self.sim_results.get('tests'):
                lines.append("| Test | Status | Duration |")
                lines.append("|------|--------|----------|")
                
                for test in self.sim_results['tests']:
                    name = test.get('name', 'Unknown')
                    passed = test.get('passed', False)
                    duration = test.get('duration', 0)
                    
                    status = "✅ PASS" if passed else "❌ FAIL"
                    
                    lines.append(f"| {name} | {status} | {duration:.3f}s |")
                
                lines.append("")
        
        # Hardware Results
        if self.hw_results:
            lines.append("## Hardware Tests")
            lines.append("")
            lines.append(f"**Total**: {hw_total} | **Passed**: {hw_passed} | **Failed**: {hw_total - hw_passed}")
            lines.append("")
            
            if self.hw_results.get('tests'):
                lines.append("| Test | Status | Duration |")
                lines.append("|------|--------|----------|")
                
                for test in self.hw_results['tests']:
                    name = test.get('name', 'Unknown')
                    passed = test.get('passed', False)
                    duration = test.get('duration', 0)
                    
                    status = "✅ PASS" if passed else "❌ FAIL"
                    
                    lines.append(f"| {name} | {status} | {duration:.3f}s |")
                
                lines.append("")
        
        # Failures
        failures = []
        for test in self.sim_results.get('tests', []):
            if not test.get('passed'):
                failures.append(('Simulation', test))
        
        for test in self.hw_results.get('tests', []):
            if not test.get('passed'):
                failures.append(('Hardware', test))
        
        if failures:
            lines.append("## Failed Tests")
            lines.append("")
            
            for test_type, test in failures:
                name = test.get('name', 'Unknown')
                error = test.get('error', 'No error message')
                
                lines.append(f"### {test_type}: {name}")
                lines.append(f"```")
                lines.append(error)
                lines.append(f"```")
                lines.append("")
        
        return "\n".join(lines)
    
    def generate_json(self) -> str:
        """Generate JSON format report"""
        report = {
            "timestamp": self.timestamp.isoformat(),
            "simulation": self.sim_results,
            "hardware": self.hw_results,
            "summary": {
                "sim_total": len(self.sim_results.get('tests', [])),
                "sim_passed": sum(1 for t in self.sim_results.get('tests', []) if t.get('passed')),
                "hw_total": len(self.hw_results.get('tests', [])),
                "hw_passed": sum(1 for t in self.hw_results.get('tests', []) if t.get('passed')),
            }
        }
        
        report["summary"]["total_tests"] = report["summary"]["sim_total"] + report["summary"]["hw_total"]
        report["summary"]["total_passed"] = report["summary"]["sim_passed"] + report["summary"]["hw_passed"]
        report["summary"]["total_failed"] = report["summary"]["total_tests"] - report["summary"]["total_passed"]
        
        if report["summary"]["total_tests"] > 0:
            report["summary"]["success_rate"] = 100.0 * report["summary"]["total_passed"] / report["summary"]["total_tests"]
        else:
            report["summary"]["success_rate"] = 0.0
        
        return json.dumps(report, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Generate test reports from simulation and hardware test results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate markdown report
  python generate_test_report.py --sim results/sim.json --hw results/hw.json
  
  # Generate JSON report
  python generate_test_report.py --sim results/sim.json --format json
  
  # Save to file
  python generate_test_report.py --sim results/sim.json --output report.md
"""
    )
    
    parser.add_argument('--sim', help='Simulation results JSON file')
    parser.add_argument('--hw', help='Hardware results JSON file')
    parser.add_argument('--format', choices=['markdown', 'json'], default='markdown',
                       help='Report format (default: markdown)')
    parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    
    args = parser.parse_args()
    
    # Create report
    report = TestReport()
    
    if args.sim:
        report.load_sim_results(args.sim)
    
    if args.hw:
        report.load_hw_results(args.hw)
    
    # Generate report
    if args.format == 'json':
        content = report.generate_json()
    else:
        content = report.generate_markdown()
    
    # Output
    if args.output:
        with open(args.output, 'w') as f:
            f.write(content)
        print(f"Report written to: {args.output}", file=sys.stderr)
    else:
        print(content)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
