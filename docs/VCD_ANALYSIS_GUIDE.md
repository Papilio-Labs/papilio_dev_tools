# VCD Analysis Guide

Comprehensive guide to analyzing VCD (Value Change Dump) files for FPGA simulation debugging.

## Table of Contents
- [Overview](#overview)
- [VCD File Format](#vcd-file-format)
- [Using parse_vcd.py](#using-parsevcdpy)
- [Analysis Techniques](#analysis-techniques)
- [GTKWave (Humans Only)](#gtkwave-humans-only)
- [Common Patterns](#common-patterns)
- [Debugging Examples](#debugging-examples)

---

## Overview

VCD files are the standard output format for Verilog/SystemVerilog simulators. They record every signal change during simulation, providing complete visibility into hardware behavior.

### Why VCD Analysis Matters

- **Complete visibility**: See all signals, not just outputs
- **Exact timing**: Know precisely when events occur
- **Correlation**: Understand relationships between signals
- **Root cause**: Find exactly where bugs occur
- **Verification**: Confirm correct behavior

### Tools Overview

**For AI Agents**:
- **Primary**: `parse_vcd.py` - Text/JSON output for analysis
- **Cannot use**: GTKWave (graphical tool)
- **Can create**: Filtered VCD files for human viewing

**For Humans**:
- **Primary**: GTKWave - Visual waveform viewer
- **Helper**: parse_vcd.py for quick checks
- **Best practice**: Use AI-created filtered VCD files

---

## VCD File Format

### Basic Structure

```
$timescale 1ns $end
$scope module tb_module $end
$var wire 1 ! clk $end
$var wire 8 " data [7:0] $end
$var reg 2 # state [1:0] $end
$upscope $end
$enddefinitions $end
#0
$dumpvars
1!
b00000000 "
bx #
$end
#10
0!
#20
1!
b00000001 "
#30
0!
b10 #
```

### Format Elements

#### Header Section
```
$timescale 1ns $end          → Time unit is 1 nanosecond
$scope module tb_module $end → Entering module hierarchy
$upscope $end                → Exiting module hierarchy
$enddefinitions $end         → End of definitions
```

#### Signal Definitions
```
$var type width symbol name [range] $end

Examples:
$var wire 1 ! clk $end                    → 1-bit wire, symbol '!'
$var wire 8 " data [7:0] $end             → 8-bit wire, symbol '"'
$var reg 2 # state [1:0] $end             → 2-bit reg, symbol '#'
$var integer 32 $ counter $end            → 32-bit integer, symbol '$'
```

Signal types:
- `wire`: Combinational signal
- `reg`: Register/FF output
- `integer`: 32-bit signed integer
- `parameter`: Constant value

#### Value Changes
```
#<timestamp>                 → Timestamp in timescale units
<value><symbol>              → Signal change

Examples:
#0                           → Time = 0
1!                           → Signal '!' (clk) = 1
0!                           → Signal '!' (clk) = 0
b00001010 "                  → Signal '"' (data) = 0x0A
bx #                         → Signal '#' (state) = unknown
```

Value formats:
- `0` / `1`: Single-bit values
- `x`: Unknown/uninitialized
- `z`: High-impedance
- `b10101010`: Binary value (8 bits)
- `hAF`: Hexadecimal value (not in standard VCD, but parse_vcd.py can interpret)

#### Value States
- `0`: Logic low
- `1`: Logic high
- `x`: Unknown (uninitialized, multiple drivers)
- `z`: High-impedance (tri-state)
- `-`: Don't care (unused in VCD)

---

## Using parse_vcd.py

### Installation

```bash
# Located in papilio_dev_tools
cd libs/papilio_dev_tools/scripts/

# Or use from any library
python ../../papilio_dev_tools/scripts/parse_vcd.py file.vcd
```

### Basic Usage

```bash
# Analyze entire VCD file (text output)
python parse_vcd.py simulation.vcd

# Analyze specific signals only
python parse_vcd.py simulation.vcd --signals clk,data,state

# Output as JSON for programmatic analysis
python parse_vcd.py simulation.vcd --format json

# JSON with specific signals
python parse_vcd.py simulation.vcd --signals clk,data --format json
```

### Creating Filtered VCD Files

**For clean GTKWave viewing**:

```bash
# Create VCD with only relevant signals
python parse_vcd.py full_simulation.vcd \
    --signals clk,spi_cs_n,spi_sclk,state,fifo_data \
    --output filtered.vcd

# Human can now open clean file
gtkwave filtered.vcd
```

**Benefits**:
- Much faster GTKWave load time
- Cleaner signal list
- Focus on relevant signals
- No manual signal selection needed

### Output Formats

#### Text Output (Default)

```bash
python parse_vcd.py tb_counter.vcd

Output:
Signal: clk
  0ns: 0
  10ns: 1
  20ns: 0
  30ns: 1
  
Signal: counter [7:0]
  0ns: 00000000
  30ns: 00000001
  50ns: 00000010
  70ns: 00000011
```

#### JSON Output

```bash
python parse_vcd.py tb_counter.vcd --format json

Output:
{
  "timescale": "1ns",
  "signals": {
    "clk": [
      {"time": 0, "value": "0"},
      {"time": 10, "value": "1"},
      {"time": 20, "value": "0"}
    ],
    "counter": [
      {"time": 0, "value": "00000000"},
      {"time": 30, "value": "00000001"},
      {"time": 50, "value": "00000010"}
    ]
  }
}
```

### Command-Line Options

```bash
python parse_vcd.py [options] <vcd_file>

Options:
  --signals SIGNAL1,SIGNAL2    Filter to specific signals
  --format text|json           Output format (default: text)
  --output FILE                Create filtered VCD file
  --start TIME                 Start time (future enhancement)
  --end TIME                   End time (future enhancement)
  --help                       Show help message
```

### Programmatic Use

```python
import json
import subprocess

# Run parse_vcd.py and capture JSON
result = subprocess.run(
    ["python", "parse_vcd.py", "sim.vcd", "--format", "json"],
    capture_output=True,
    text=True
)

data = json.loads(result.stdout)

# Analyze signals
for time, value in data["signals"]["state"]:
    if value == "10":  # State == 2
        print(f"Entered STATE_READ at {time}ns")
```

---

## Analysis Techniques

### Finding Specific Events

#### When Counter Reaches Value

```bash
# Text analysis
python parse_vcd.py tb.vcd --signals byte_counter | grep "00001010"  # 10 in binary

# JSON analysis
python parse_vcd.py tb.vcd --signals byte_counter --format json > data.json
```

```python
import json
with open("data.json") as f:
    data = json.load(f)
    
for change in data["signals"]["byte_counter"]:
    if int(change["value"], 2) == 10:  # Binary to decimal
        print(f"Counter reached 10 at {change['time']}ns")
```

#### State Machine Transitions

```bash
# Find all times state = STATE_WRITE (binary 01)
python parse_vcd.py tb.vcd --signals dma_state | grep "^  [0-9]*ns: 01"

# Find transition from IDLE (00) to WRITE (01)
python parse_vcd.py tb.vcd --signals dma_state > state.txt
# Then analyze state.txt for transition pattern
```

#### Signal Edges

```bash
# Find rising edges of signal
python parse_vcd.py tb.vcd --signals valid | grep ": 1$"

# Find falling edges
python parse_vcd.py tb.vcd --signals valid | grep ": 0$"
```

### Timing Analysis

#### Measure Signal Delays

```python
import json

with open("data.json") as f:
    data = json.load(f)

# Find delay between req and ack
req_time = None
for change in data["signals"]["request"]:
    if change["value"] == "1":
        req_time = change["time"]
        break

ack_time = None
for change in data["signals"]["acknowledge"]:
    if change["time"] > req_time and change["value"] == "1":
        ack_time = change["time"]
        break

if req_time and ack_time:
    delay = ack_time - req_time
    print(f"Request to Acknowledge delay: {delay}ns")
```

#### Signal Pulse Width

```python
# Measure clock high time
clk_high_times = []
high_start = None

for change in data["signals"]["clk"]:
    if change["value"] == "1":
        high_start = change["time"]
    elif change["value"] == "0" and high_start:
        duration = change["time"] - high_start
        clk_high_times.append(duration)
        high_start = None

print(f"Average high time: {sum(clk_high_times)/len(clk_high_times)}ns")
```

### Signal Correlation

#### What is X when Y changes?

```python
# What is data value when strobe pulses?
strobe_times = [c["time"] for c in data["signals"]["strobe"] if c["value"] == "1"]

for strobe_time in strobe_times:
    # Find data value at that time
    data_value = None
    for change in data["signals"]["data"]:
        if change["time"] <= strobe_time:
            data_value = change["value"]
        else:
            break
    
    print(f"At {strobe_time}ns: data = {data_value}")
```

#### Verify Protocol Timing

```python
# Check SPI Mode 1 (CPOL=0, CPHA=1)
# Data should be valid on SCLK rising edge

sclk_edges = [c for c in data["signals"]["spi_sclk"] if c["value"] == "1"]

for edge in sclk_edges:
    edge_time = edge["time"]
    
    # Find MOSI value at this edge
    mosi_value = None
    for change in data["signals"]["spi_mosi"]:
        if change["time"] <= edge_time:
            mosi_value = change["value"]
        else:
            break
    
    print(f"SCLK rising @ {edge_time}ns: MOSI = {mosi_value}")
```

### Pattern Recognition

#### Burst Transfers

```python
# Detect burst pattern (multiple transfers with CS low)
cs_low_start = None
transfer_count = 0

for change in data["signals"]["spi_cs_n"]:
    if change["value"] == "0":
        cs_low_start = change["time"]
        transfer_count = 0
    elif change["value"] == "1" and cs_low_start:
        # Count bytes transferred while CS was low
        # (Look at bit_counter or similar)
        burst_duration = change["time"] - cs_low_start
        print(f"Burst: {transfer_count} bytes in {burst_duration}ns")
        cs_low_start = None
```

#### Glitches

```python
# Find glitches (signal changes and back within short time)
GLITCH_THRESHOLD = 5  # ns

for i in range(len(data["signals"]["signal"]) - 1):
    curr = data["signals"]["signal"][i]
    next = data["signals"]["signal"][i+1]
    
    time_diff = next["time"] - curr["time"]
    if time_diff < GLITCH_THRESHOLD and curr["value"] != next["value"]:
        print(f"Glitch at {curr['time']}ns: {curr['value']} -> {next['value']}")
```

---

## GTKWave (Humans Only)

**NOTE**: GTKWave is a graphical tool. AI agents cannot use it. This section is for human developers.

### Getting Started

```bash
# Open VCD file
gtkwave simulation.vcd

# Open filtered VCD (recommended - ask AI to create)
gtkwave filtered.vcd
```

### Best Practice: Use Filtered VCD

Instead of opening massive VCD files and manually selecting signals:

1. **AI analyzes** full VCD:
   ```bash
   python parse_vcd.py full.vcd
   ```

2. **AI identifies** relevant signals for debugging

3. **AI creates** filtered VCD:
   ```bash
   python parse_vcd.py full.vcd \
       --signals clk,state,counter,fifo_data,error_flag \
       --output debug.vcd
   ```

4. **Human opens** clean file:
   ```bash
   gtkwave debug.vcd
   ```

Much easier than sifting through hundreds of signals!

### GTKWave Basics

#### Interface Layout
```
+-----------------------------------+
| Menu Bar                           |
+------------+----------------------+
| Signal     | Waveform             |
| Hierarchy  | Display              |
| Tree       | Area                 |
|            |                      |
|            |                      |
+------------+----------------------+
| Zoom/Time Controls                |
+-----------------------------------+
```

#### Adding Signals (if not using filtered VCD)

1. Expand module hierarchy in left pane
2. Select signal names
3. Click "Insert" or press `Insert` key
4. Signals appear in waveform area

#### Basic Controls

- **Zoom In**: Click and drag in waveform area
- **Zoom Out**: Right-click and drag
- **Zoom Fit**: View → Zoom → Zoom Fit
- **Pan**: Scroll wheel or scroll bar

#### Markers and Measurements

- **Primary Marker**: Left-click in waveform area (vertical line)
- **Secondary Marker**: Middle-click or `Ctrl+Click`
- **Time Difference**: Shown in bottom status bar
- **Snap to Transition**: Markers snap to signal edges

### Advanced GTKWave Features

#### Signal Groups

Create groups for organization:
1. Select multiple signals
2. Right-click → Create Group
3. Name the group
4. Collapse/expand groups as needed

#### Signal Formatting

Right-click signal name → Data Format:
- **Binary**: 0s and 1s
- **Hexadecimal**: Compact multi-bit display
- **Decimal**: Numeric interpretation
- **ASCII**: Character interpretation

#### Search

Edit → Search:
- Find signal transitions
- Search by value or pattern
- Jump to next occurrence

#### Cursors

View → Show Grid: Display time grid
View → Show Base: Show time base

#### Save Configuration

File → Write Save File: Save signal selection and layout for reuse

---

## Common Patterns

### Pattern 1: State Machine Debug

**Goal**: Verify state transitions

**Signals to monitor**:
```
clk
rst
state
enable
trigger_condition
```

**Analysis**:
```python
python parse_vcd.py tb.vcd --signals state --format json > state.json
```

```python
import json
with open("state.json") as f:
    data = json.load(f)

# Track state history
states = data["signals"]["state"]
for i in range(len(states) - 1):
    curr_state = int(states[i]["value"], 2)
    next_state = int(states[i+1]["value"], 2)
    time = states[i+1]["time"]
    
    print(f"{time}ns: State {curr_state} -> {next_state}")
```

### Pattern 2: FIFO Debug

**Goal**: Verify FIFO operations

**Signals to monitor**:
```
clk
wr_en, wr_data, wr_full
rd_en, rd_data, rd_empty
fifo_count
```

**Create filtered VCD**:
```bash
python parse_vcd.py tb_fifo.vcd \
    --signals clk,wr_en,wr_data,wr_full,rd_en,rd_data,rd_empty,fifo_count \
    --output fifo_debug.vcd

gtkwave fifo_debug.vcd  # Human views
```

### Pattern 3: Timing Verification

**Goal**: Verify setup/hold times

**Signals to monitor**:
```
clk
data
strobe
valid
```

**Analysis**:
```python
# Check setup time (data stable before strobe)
SETUP_TIME_REQ = 10  # ns

strobe_edges = [c for c in data["signals"]["strobe"] if c["value"] == "1"]

for edge in strobe_edges:
    strobe_time = edge["time"]
    
    # Find last data change before strobe
    last_data_change = 0
    for change in data["signals"]["data"]:
        if change["time"] < strobe_time:
            last_data_change = change["time"]
        else:
            break
    
    setup_time = strobe_time - last_data_change
    
    if setup_time < SETUP_TIME_REQ:
        print(f"WARNING: Setup violation at {strobe_time}ns")
        print(f"  Setup time: {setup_time}ns (required: {SETUP_TIME_REQ}ns)")
```

### Pattern 4: Protocol Compliance

**Goal**: Verify SPI Mode 1 (CPOL=0, CPHA=1)

**Signals to monitor**:
```
spi_sclk
spi_cs_n
spi_mosi
spi_miso
```

**Verification**:
```python
# SPI Mode 1: Data captured on rising edge, shifted on falling edge

# Find all rising edges of SCLK when CS is active
sclk_rising = []
cs_active = False

for i, change in enumerate(data["signals"]["spi_sclk"]):
    # Track CS state
    for cs_change in data["signals"]["spi_cs_n"]:
        if cs_change["time"] <= change["time"]:
            cs_active = (cs_change["value"] == "0")
    
    # Record rising edges when CS active
    if change["value"] == "1" and cs_active:
        sclk_rising.append(change["time"])

print(f"Found {len(sclk_rising)} SCLK rising edges during transfer")

# Verify data stability at each edge
for edge_time in sclk_rising:
    # Check MOSI and MISO values at this edge
    # They should be stable (not changing)
    # ... verification code ...
```

---

## Debugging Examples

### Example 1: Data Corruption

**Symptom**: Reading wrong data from FIFO

**Debug steps**:

1. **Analyze writes**:
```bash
python parse_vcd.py tb.vcd --signals wr_en,wr_data
```

Output shows:
```
Signal: wr_data [7:0]
  1000ns: 00000000
  2000ns: 00000001
  3000ns: 00000010
  4000ns: 00000011
```

2. **Analyze reads**:
```bash
python parse_vcd.py tb.vcd --signals rd_en,rd_data
```

Output shows:
```
Signal: rd_data [7:0]
  10000ns: 00000000  ← Correct
  11000ns: 00000011  ← WRONG! Expected 00000001
```

3. **Check FIFO internals**:
```bash
python parse_vcd.py tb.vcd \
    --signals wr_ptr,rd_ptr,fifo_count \
    --output fifo_internal.vcd

gtkwave fifo_internal.vcd  # Human investigates
```

4. **Root cause**: Write pointer incremented twice!

### Example 2: State Machine Stuck

**Symptom**: State machine not advancing

**Debug steps**:

1. **Monitor state**:
```bash
python parse_vcd.py tb.vcd --signals state,enable,trigger
```

Output shows:
```
Signal: state [1:0]
  0ns: 00     (IDLE)
  100ns: 01   (WAITING)
  150ns: 01   ← Still WAITING
  200ns: 01   ← Still WAITING
  ... (never advances)
```

2. **Check transition condition**:
```bash
python parse_vcd.py tb.vcd --signals state,trigger,enable,counter
```

Output shows:
```
Signal: trigger
  0ns: 0
  ... (never goes to 1!)
```

3. **Root cause**: Trigger never asserts → condition never met

### Example 3: Timing Violation

**Symptom**: Intermittent failures

**Debug steps**:

1. **Check clock domains**:
```bash
python parse_vcd.py tb.vcd --signals clk_a,clk_b,signal_a,signal_b_sync
```

2. **Measure clock relationship**:
```python
# Find phase relationship between clocks
clk_a_edges = [c["time"] for c in data["signals"]["clk_a"] if c["value"] == "1"]
clk_b_edges = [c["time"] for c in data["signals"]["clk_b"] if c["value"] == "1"]

# Find closest edges
for edge_a in clk_a_edges[:10]:
    closest_b = min(clk_b_edges, key=lambda x: abs(x - edge_a))
    offset = closest_b - edge_a
    print(f"Clock offset at {edge_a}ns: {offset}ns")
```

3. **Verify synchronizer**:
```bash
python parse_vcd.py tb.vcd \
    --signals signal_a,sync1,sync2,signal_b_sync \
    --output sync_debug.vcd
```

4. **Root cause**: Missing synchronizer stage or metastability

---

## Summary for AI Agents

### Critical Rules

1. ✅ **ALWAYS use parse_vcd.py** for analysis (primary tool)
2. ✅ **CAN create filtered VCD** for human viewing (--output)
3. ❌ **CANNOT use GTKWave** directly (GUI tool)
4. ✅ **USE JSON output** for programmatic analysis (--format json)

### Workflow

1. **Analyze full VCD**:
   ```bash
   python parse_vcd.py simulation.vcd --format json > analysis.json
   ```

2. **Identify relevant signals** from analysis

3. **Create filtered VCD** for human:
   ```bash
   python parse_vcd.py simulation.vcd \
       --signals signal1,signal2,signal3 \
       --output debug.vcd
   ```

4. **Report findings** to user with filtered VCD path

### Quick Reference

```bash
# Basic text analysis
python parse_vcd.py file.vcd

# Specific signals
python parse_vcd.py file.vcd --signals clk,data,state

# JSON for programmatic use
python parse_vcd.py file.vcd --format json

# Filtered VCD for human
python parse_vcd.py file.vcd --signals sig1,sig2 --output clean.vcd
```

VCD analysis is your window into hardware behavior!
