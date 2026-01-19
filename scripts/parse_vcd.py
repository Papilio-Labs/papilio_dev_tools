#!/usr/bin/env python3
"""
VCD (Value Change Dump) Parser and Analyzer

This script parses VCD files and provides multiple output formats:
1. Human-readable text output (default)
2. JSON output for programmatic analysis
3. Filtered VCD output for GTKWave

Usage:
    python parse_vcd.py simulation.vcd
    python parse_vcd.py simulation.vcd --signals clk,data,state
    python parse_vcd.py simulation.vcd --format json
    python parse_vcd.py simulation.vcd --signals clk,data --output filtered.vcd

Author: Papilio Project
License: MIT
"""

import sys
import argparse
import json
import re
from typing import Dict, List, Tuple, Optional
from collections import defaultdict


class VCDParser:
    """Parse VCD files and extract signal information"""
    
    def __init__(self, vcd_file: str):
        self.vcd_file = vcd_file
        self.timescale = "1ns"
        self.signals = {}  # symbol -> (name, width)
        self.values = defaultdict(list)  # name -> [(time, value), ...]
        self.current_time = 0
        
    def parse(self) -> None:
        """Parse the VCD file"""
        with open(self.vcd_file, 'r') as f:
            in_definitions = True
            
            for line in f:
                line = line.strip()
                
                if not line:
                    continue
                
                # Parse header section
                if in_definitions:
                    if line.startswith('$timescale'):
                        self.timescale = line.split()[1]
                    
                    elif line.startswith('$var'):
                        # Format: $var type width symbol name [range] $end
                        parts = line.split()
                        if len(parts) >= 5:
                            var_type = parts[1]
                            width = int(parts[2])
                            symbol = parts[3]
                            name = parts[4]
                            
                            # Remove bracketed range if present
                            if '[' in name:
                                name = name.split('[')[0]
                            
                            self.signals[symbol] = (name, width)
                    
                    elif line == '$enddefinitions $end':
                        in_definitions = False
                
                # Parse value changes
                else:
                    if line.startswith('#'):
                        # Timestamp
                        self.current_time = int(line[1:])
                    
                    elif line and line[0] in '01xzXZ':
                        # Single-bit value change: <value><symbol>
                        value = line[0]
                        symbol = line[1:]
                        if symbol in self.signals:
                            name = self.signals[symbol][0]
                            self.values[name].append((self.current_time, value))
                    
                    elif line.startswith('b'):
                        # Multi-bit value change: b<value> <symbol>
                        parts = line.split()
                        if len(parts) >= 2:
                            value = parts[0][1:]  # Remove 'b' prefix
                            symbol = parts[1]
                            if symbol in self.signals:
                                name = self.signals[symbol][0]
                                self.values[name].append((self.current_time, value))
    
    def get_signal_names(self) -> List[str]:
        """Get list of all signal names"""
        return [name for name, width in self.signals.values()]
    
    def get_signal_values(self, signal_name: str) -> List[Tuple[int, str]]:
        """Get value changes for a specific signal"""
        return self.values.get(signal_name, [])
    
    def filter_signals(self, signal_list: List[str]) -> None:
        """Keep only specified signals"""
        # Build reverse mapping: name -> symbol
        name_to_symbol = {name: symbol for symbol, (name, width) in self.signals.items()}
        
        # Filter signals
        filtered_signals = {}
        for name in signal_list:
            if name in name_to_symbol:
                symbol = name_to_symbol[name]
                filtered_signals[symbol] = self.signals[symbol]
        
        self.signals = filtered_signals
        
        # Filter values
        filtered_values = {}
        for name in signal_list:
            if name in self.values:
                filtered_values[name] = self.values[name]
        
        self.values = defaultdict(list, filtered_values)


def format_text(parser: VCDParser) -> str:
    """Format output as human-readable text"""
    output = []
    output.append(f"Timescale: {parser.timescale}")
    output.append("")
    
    for signal_name in sorted(parser.get_signal_names()):
        values = parser.get_signal_values(signal_name)
        
        if not values:
            continue
        
        output.append(f"Signal: {signal_name}")
        
        for time, value in values:
            # Convert time to readable format
            if parser.timescale == "1ps":
                time_str = f"{time}ps"
            elif parser.timescale == "1ns":
                time_str = f"{time}ns"
            elif parser.timescale == "1us":
                time_str = f"{time}us"
            else:
                time_str = f"{time}"
            
            # Format value
            if len(value) > 1:
                # Multi-bit value
                output.append(f"  {time_str}: {value}")
            else:
                # Single-bit value
                output.append(f"  {time_str}: {value}")
        
        output.append("")
    
    return "\n".join(output)


def format_json(parser: VCDParser) -> str:
    """Format output as JSON"""
    data = {
        "timescale": parser.timescale,
        "signals": {}
    }
    
    for signal_name in sorted(parser.get_signal_names()):
        values = parser.get_signal_values(signal_name)
        
        data["signals"][signal_name] = [
            {"time": time, "value": value}
            for time, value in values
        ]
    
    return json.dumps(data, indent=2)


def write_filtered_vcd(parser: VCDParser, output_file: str) -> None:
    """Write filtered VCD file with only selected signals"""
    
    # Read original VCD to preserve header structure
    with open(parser.vcd_file, 'r') as f:
        original_lines = f.readlines()
    
    with open(output_file, 'w') as f:
        # Write header section
        in_definitions = True
        symbols_to_keep = set(parser.signals.keys())
        
        for line in original_lines:
            stripped = line.strip()
            
            if in_definitions:
                # Keep all header lines except $var lines we're filtering out
                if stripped.startswith('$var'):
                    parts = stripped.split()
                    if len(parts) >= 4:
                        symbol = parts[3]
                        if symbol in symbols_to_keep:
                            f.write(line)
                else:
                    f.write(line)
                
                if stripped == '$enddefinitions $end':
                    in_definitions = False
            else:
                # Write value changes for filtered signals only
                if stripped.startswith('#'):
                    # Always write timestamps
                    f.write(line)
                elif stripped:
                    # Check if this value change is for a kept signal
                    if stripped[0] in '01xzXZ':
                        # Single-bit: <value><symbol>
                        if len(stripped) > 1:
                            symbol = stripped[1:]
                            if symbol in symbols_to_keep:
                                f.write(line)
                    elif stripped.startswith('b'):
                        # Multi-bit: b<value> <symbol>
                        parts = stripped.split()
                        if len(parts) >= 2:
                            symbol = parts[1]
                            if symbol in symbols_to_keep:
                                f.write(line)
                    else:
                        # Other value change formats
                        f.write(line)


def main():
    parser_args = argparse.ArgumentParser(
        description="Parse and analyze VCD files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze entire VCD file
  python parse_vcd.py simulation.vcd
  
  # Analyze specific signals only
  python parse_vcd.py simulation.vcd --signals clk,data,state
  
  # Output as JSON for programmatic analysis
  python parse_vcd.py simulation.vcd --format json
  
  # Create filtered VCD for GTKWave
  python parse_vcd.py simulation.vcd --signals clk,data --output filtered.vcd
"""
    )
    
    parser_args.add_argument('vcd_file', help='VCD file to parse')
    parser_args.add_argument('--signals', help='Comma-separated list of signals to extract')
    parser_args.add_argument('--format', choices=['text', 'json'], default='text',
                           help='Output format (default: text)')
    parser_args.add_argument('--output', help='Output filtered VCD file')
    
    args = parser_args.parse_args()
    
    try:
        # Parse VCD file
        vcd_parser = VCDParser(args.vcd_file)
        vcd_parser.parse()
        
        # Filter signals if requested
        if args.signals:
            signal_list = [s.strip() for s in args.signals.split(',')]
            vcd_parser.filter_signals(signal_list)
        
        # Output filtered VCD if requested
        if args.output:
            write_filtered_vcd(vcd_parser, args.output)
            print(f"Filtered VCD written to: {args.output}", file=sys.stderr)
            print(f"Open with: gtkwave {args.output}", file=sys.stderr)
            return 0
        
        # Output analysis
        if args.format == 'json':
            print(format_json(vcd_parser))
        else:
            print(format_text(vcd_parser))
        
        return 0
        
    except FileNotFoundError:
        print(f"Error: File not found: {args.vcd_file}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
