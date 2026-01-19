# Papilio Dev Tools - AI Skills

This document provides essential development skills and workflows for AI coding assistants working on Papilio FPGA libraries. These skills are general-purpose and applicable across all Papilio projects.

## Table of Contents
- [FPGA Simulation](#fpga-simulation)
- [VCD Analysis](#vcd-analysis)
- [Hardware Debugging](#hardware-debugging)
- [Test Integration](#test-integration)
- [Best Practices](#best-practices)

---

## FPGA Simulation

### When to Simulate

**ALWAYS** simulate gateware before hardware testing:
- Simulation is ~35x faster than hardware build-test cycles
- Complete visibility into internal signals, states, and registers
- Deterministic behavior (same inputs → same outputs)
- Safe experimentation without hardware damage risk
- Perfect for logic bugs, state machines, protocol compliance, timing relationships

### Before Writing Testbenches

**CRITICAL**: Before writing any testbench code, autonomously search for and retrieve specifications:

1. **Search for specifications online**:
   - Use `fetch_webpage` to retrieve datasheets, protocol specifications, or reference documentation
   - Look for: timing diagrams, protocol specifications, waveforms, state machines
   - Check: signal requirements, setup/hold times, example transactions
   - Verify: pin assignments, signal polarities, voltage levels

2. **Analyze the specification**:
   - Review timing diagrams carefully
   - Note signal sequences and dependencies
   - Identify edge cases and corner conditions
   - Understand state transitions

3. **Only ask user if**:
   - Component is custom/internal (not publicly documented)
   - Specification is ambiguous or contradictory
   - Need clarification on specific requirements
   - Web search unsuccessful or incomplete

**Benefits of specification-first approach**:
- More accurate testbenches from the start
- Better coverage of edge cases
- Correct timing relationships
- Proper protocol implementation
- Fewer iterations needed

### Tool Environment

**CRITICAL**: Never invoke simulation tools directly (iverilog, vvp, gtkwave).

Always use the provided Python scripts which handle:
- Environment variable setup (OSS CAD Suite)
- Cross-platform paths (Windows/Linux/macOS)
- Tool discovery and configuration
- Error handling and reporting
- Proper PATH setup

**Why scripts are required**:
- On Windows, iverilog needs `environment.bat` called first
- Tool paths vary by installation and OS
- Library paths must be set correctly
- Direct invocation will fail with cryptic errors

### Simulation Workflow

```bash
# Complete workflow (all handled by scripts)

# 0. Before writing testbench: Fetch specifications from the web
#    Use fetch_webpage to get datasheets, protocol specs, timing diagrams

# 1. Write testbench in tests/sim/
#    Example: tests/sim/tb_my_module.v

# 2. Run simulation (handles environment automatically)
python tests/sim/run_all_sims.py

# 3. Analyze VCD output (PRIMARY tool for AI agents)
python scripts/parse_vcd.py tb_my_module.vcd

# 4. Optional: Create filtered VCD for human viewing
python scripts/parse_vcd.py tb_my_module.vcd --signals clk,state,data --output filtered.vcd

# 5. Optional: Human views in GTKWave (GUI tool - AI cannot use)
gtkwave filtered.vcd
```

**Important**:
- AI agents MUST use `parse_vcd.py` for VCD analysis (cannot see GTKWave GUI)
- AI agents CAN create filtered VCD files for cleaner human visualization
- Scripts handle all environment setup automatically
- GTKWave is optional and for human visual debugging only

### Critical Testbench Elements

**Before implementation**: Fetch and review datasheet/specification from the web for timing and protocol details. Only ask user if component is custom or specifications unavailable online.

#### 1. Timescale Declaration
```verilog
`timescale 1ns / 1ps
```

#### 2. Clock Generation
```verilog
reg clk = 0;
initial begin
    clk = 0;
    forever #18.5 clk = ~clk;  // 27MHz = 37ns period
end
```

#### 3. Reset Handling
```verilog
reg rst = 1;
initial begin
    rst = 1;
    #200;  // Hold reset for several clock cycles
    rst = 0;
end
```

#### 4. Reusable Tasks
```verilog
task spi_transfer;
    input [7:0] data_out;
    output [7:0] data_in;
    integer i;
    begin
        data_in = 8'h00;
        for (i = 7; i >= 0; i = i - 1) begin
            spi_mosi = data_out[i];
            #500 spi_sclk = 1;  // 1MHz SPI clock
            #500 spi_sclk = 0;
            data_in[i] = spi_miso;
        end
    end
endtask
```

#### 5. VCD Dump
```verilog
initial begin
    $dumpfile("tb_my_module.vcd");
    $dumpvars(0, tb_my_module);
    
    // Test sequence here
    
    $finish;
end
```

#### 6. Timing Considerations
- **Inter-transaction delays**: Allow time for state machines to complete
  ```verilog
  #100;  // Setup time before CS assertion
  spi_cs_n = 0;
  // ... transfers ...
  #100;  // Hold time after transaction
  spi_cs_n = 1;
  ```

- **Processing time**: Wait for DMA/state machines between operations
  ```verilog
  #50000;  // 50μs wait for DMA to complete
  ```

#### 7. Result Checking
```verilog
if (actual == expected)
    $display("Test PASS: got 0x%02h", actual);
else
    $display("Test FAIL: got 0x%02h, expected 0x%02h", actual, expected);
```

#### 8. Timeout Protection
```verilog
initial begin
    #1000000;  // 1ms timeout
    $display("ERROR: Test timeout!");
    $finish;
end
```

### Testbench Best Practices

1. **Start small**: Test 10 bytes before testing 256
2. **Clear test phases**: Use `$display` to narrate test progress
   ```verilog
   $display("\n=== Phase 1: Write Data ===");
   // ... writes ...
   $display("\n=== Phase 2: Read Data ===");
   // ... reads ...
   ```

3. **Use meaningful names**: `tx_fifo_ready` not `sig_42`
4. **Test incrementally**: Add complexity gradually
5. **Document assumptions**: Comment expected behavior
6. **Use assertions**: Check assumptions during simulation
   ```verilog
   if (byte_count != expected_count) begin
       $error("Unexpected byte count: %d", byte_count);
       $finish;
   end
   ```

### Simulation Advantages
- **35x faster** than hardware build-test cycles
- Complete visibility into all signals
- Deterministic behavior
- Non-destructive testing
- Precise timing measurements
- Easy "what-if" analysis

### Simulation Limitations
Does NOT catch:
- Clock domain crossing metastability (unless modeled)
- Real-world timing variations
- Signal integrity issues
- Power supply problems
- Temperature effects

**Therefore**: Always follow simulation with hardware validation.

---

## VCD Analysis

### Primary Tool: parse_vcd.py

**FOR AI AGENTS**: Always use `parse_vcd.py` to analyze VCD files. You cannot see GTKWave's graphical output.

#### Basic Usage
```bash
# Analyze entire VCD file (text output)
python scripts/parse_vcd.py tb_module.vcd

# Extract specific signals only (cleaner output)
python scripts/parse_vcd.py tb_module.vcd --signals clk,reset,state

# Output as JSON for programmatic analysis
python scripts/parse_vcd.py tb_module.vcd --format json

# Create filtered VCD with only relevant signals (for GTKWave)
python scripts/parse_vcd.py tb_module.vcd --signals clk,reset,state --output filtered.vcd
```

#### Filtered VCD Workflow

**Best practice for human collaboration**:
1. AI analyzes full VCD using parse_vcd.py
2. AI identifies relevant signals for debugging
3. AI creates filtered VCD with only those signals: `--output filtered.vcd`
4. Human opens `filtered.vcd` in GTKWave for clean visualization
5. Much easier than manually selecting from hundreds of signals!

Example:
```bash
# AI analyzes and finds relevant signals
python scripts/parse_vcd.py full_simulation.vcd

# AI creates filtered VCD for human
python scripts/parse_vcd.py full_simulation.vcd \
    --signals clk,spi_cs_n,spi_sclk,state,byte_count,fifo_data \
    --output debug_view.vcd

# Human can now easily view in GTKWave
gtkwave debug_view.vcd  # Much cleaner!
```

### Understanding VCD Files

VCD (Value Change Dump) files record every signal change during simulation.

#### VCD Structure
```
$timescale 1ps $end
$scope module tb_spi_fifo_dma $end
$var wire 1 ! spi_miso $end
$var wire 8 ) tx_fifo_data [7:0] $end
$var reg 2 9 dma_state [1:0] $end
$var reg 9 7 bytes_written [8:0] $end
$upscope $end
$enddefinitions $end

#0
$dumpvars
bx 9
b0 7
$end

#18500
1"
#37000
0"
b101 9
```

#### VCD Format Elements
- `$timescale 1ps $end`: Time unit (picoseconds)
- `$var wire 1 ! signal_name`: Signal definition (1-bit wire, symbol `!`)
- `$var reg 8 ) data [7:0]`: 8-bit register, symbol `)`
- `#18500`: Timestamp (18.5ns in this example)
- `1"`: Signal `"` goes high
- `0"`: Signal `"` goes low
- `b101 9`: Signal `9` changes to binary `101` (decimal 5)
- `bx 7`: Signal `7` is unknown/uninitialized

### Key Signals to Monitor

When debugging, focus on:
- **State machines**: FSM state registers
- **Counters**: Loop counters, byte counters, bit counters
- **Control signals**: Ready, valid, enable, chip select
- **Data paths**: FIFO data, shift registers, output data
- **Timing signals**: Clocks, strobes, acknowledge signals

Example (SPI debugging):
```
State machine:    dma_state
Counters:         bytes_written, dma_count, tx_bit_count
BRAM signals:     storage_addr, storage_we, storage_wdata, storage_rdata
FIFO signals:     tx_fifo_data, tx_fifo_valid, tx_fifo_ready
SPI signals:      spi_sclk, spi_cs_n, spi_miso, spi_mosi
TX path:          tx_shift, tx_data_loaded
```

### VCD Analysis Techniques

#### Finding Specific Events
```bash
# Find when a counter reaches specific value
python scripts/parse_vcd.py tb.vcd --signals byte_counter --format json | jq '.signals.byte_counter[] | select(.value == 10)'

# Find state transitions
python scripts/parse_vcd.py tb.vcd --signals state_reg
```

#### Timing Analysis
```bash
# Get signal change history with timestamps
python scripts/parse_vcd.py tb.vcd --signals clk,data_valid --format json
```

#### Signal Correlation
Look for relationships between signals:
- When does `valid` assert after `ready`?
- What is `data` value when `strobe` pulses?
- How long after `cs_n` goes low does `sclk` start?

### GTKWave (Optional - Humans Only)

**NOTE**: GTKWave is a graphical tool for human debugging. AI agents cannot use it and should use `parse_vcd.py` instead.

**Tip for humans**: VCD files often contain too many signals. Ask AI to create a filtered VCD:
```bash
python scripts/parse_vcd.py full.vcd --signals clk,data,state --output filtered.vcd
gtkwave filtered.vcd  # Much easier to read!
```

GTKWave features:
- Visual waveform viewing
- Signal grouping and hierarchy
- Zoom and pan controls
- Measurement cursors
- Signal search and filtering
- Save signal configurations

---

## Hardware Debugging

### Serial Debugging Patterns

#### Basic Debug Output
```cpp
Serial.begin(115200);
Serial.println("Starting test...");
Serial.printf("Register value: 0x%02X\n", reg_val);
```

#### Timing Measurements
```cpp
unsigned long start = micros();
// ... operation ...
unsigned long duration = micros() - start;
Serial.printf("Operation took %lu µs\n", duration);
```

#### State Logging
```cpp
enum State { IDLE, BUSY, DONE };
State state = IDLE;

void log_state_change(State new_state) {
    Serial.printf("State: %s -> %s\n", 
        state_name(state), state_name(new_state));
    state = new_state;
}
```

### Common Hardware Issues

#### Clock Domain Crossing
- **Symptom**: Intermittent failures, metastability
- **Debug**: Add synchronizer FFs, verify setup/hold times
- **Test**: Run repeatedly with varying conditions

#### Timing Violations
- **Symptom**: Wrong data at high speeds, works at low speeds
- **Debug**: Review timing constraints, add pipeline stages
- **Test**: Sweep clock frequencies

#### Signal Integrity
- **Symptom**: Glitches, noise, unreliable communication
- **Debug**: Check pull-ups/pull-downs, ground connections
- **Test**: Use logic analyzer to view actual signals

### Hardware Test Organization

```
tests/hw/
├── README.md              # How to run hardware tests
├── platformio.ini         # Test project configuration
├── src/
│   ├── test_spi.cpp       # SPI communication tests
│   ├── test_wishbone.cpp  # Wishbone bus tests
│   └── test_dma.cpp       # DMA tests
└── run_hw_tests.py        # Automated test runner
```

---

## Test Integration

### Two Patterns for Library Tests

#### Option A: Standalone Test Project
Best for: Libraries that need isolated testing, complex test setups

```
libs/papilio_xxx/
├── library.json
├── src/
├── tests/
│   ├── sim/
│   │   ├── run_all_sims.py
│   │   └── tb_xxx.v
│   └── hw/
│       ├── platformio.ini    # Standalone test project
│       ├── src/
│       │   └── test_xxx.cpp
│       └── run_hw_tests.py
└── run_all_tests.py
```

**Pros**:
- Complete isolation
- Own dependencies
- Easy CI integration
- Clear test-only code

**Cons**:
- Duplicate configuration
- Separate build
- More directory overhead

#### Option B: Workspace Integration
Best for: Libraries integrated into a main project

```
workspace/
├── platformio.ini          # Main project with test environments
├── src/
│   └── main.cpp           # Main application
├── test/
│   ├── test_papilio_xxx/  # Library tests
│   │   └── test_xxx.cpp
│   └── test_desktop/
│       └── test_native.cpp
└── libs/
    └── papilio_xxx/
        ├── library.json
        ├── src/
        └── tests/sim/     # Simulation tests
```

**Pros**:
- Single build system
- Shared configuration
- Less overhead
- Easy library-app testing

**Cons**:
- Test-app coupling
- Harder to isolate
- More complex platformio.ini

### Choosing a Pattern

Use **Option A** (Standalone) when:
- Library is reusable across projects
- Need clean separation of concerns
- Plan to publish library separately
- Want simple CI integration

Use **Option B** (Workspace) when:
- Library is project-specific
- Tests need application context
- Want unified build/test commands
- Development agility is priority

### Regression Testing

Complete test coverage requires both simulation and hardware tests:

```python
# run_all_tests.py - Template from papilio_dev_tools

import sys
import subprocess

def run_sim_tests():
    print("\n=== Running Simulation Tests ===")
    result = subprocess.run(["python", "tests/sim/run_all_sims.py"])
    return result.returncode == 0

def run_hw_tests():
    print("\n=== Running Hardware Tests ===")
    result = subprocess.run(["python", "tests/hw/run_hw_tests.py"])
    return result.returncode == 0

if __name__ == "__main__":
    sim_ok = run_sim_tests()
    hw_ok = run_hw_tests()
    
    if sim_ok and hw_ok:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
```

---

## Best Practices

### Development Workflow

1. **Specification First**
   - Use `fetch_webpage` to autonomously retrieve datasheets/specs
   - Review timing diagrams, protocols, and requirements
   - Only ask user for custom/internal components

2. **Simulation First**
   - Write testbench based on specification
   - Simulate extensively before hardware
   - Debug issues in simulation (35x faster)

3. **Incremental Development**
   - Start with simple functionality
   - Add complexity gradually
   - Test at each step

4. **Hardware Validation**
   - Verify simulation results in hardware
   - Test real-world timing and conditions
   - Document any simulation-hardware differences

### Debugging Workflow

When hardware fails:
1. **Reproduce in simulation**
   - Create testbench that shows the bug
   - Confirm same failure mode

2. **Debug in simulation**
   - Use parse_vcd.py to analyze signals
   - Create filtered VCD for human visualization
   - Identify root cause

3. **Fix and verify in simulation**
   - Implement fix
   - Run regression tests
   - Confirm fix works

4. **Validate in hardware**
   - Test fixed design in hardware
   - Verify issue is resolved

### Documentation Practices

1. **Document assumptions**: What are you assuming works?
2. **Document limitations**: What doesn't work yet?
3. **Document test coverage**: What's tested, what isn't?
4. **Document known issues**: What problems exist?

### Code Quality

1. **Meaningful names**: `byte_counter` not `cnt_b`
2. **Comments for why, not what**: Explain design decisions
3. **Parameterize constants**: Use `localparam` not magic numbers
4. **Design for observability**: Expose state for debugging

---

## Summary for AI Agents

### Critical Rules
1. ✅ **ALWAYS** use scripts (run_all_sims.py, run_sim.py) - never invoke iverilog/vvp directly
2. ✅ **ALWAYS** use parse_vcd.py for VCD analysis - cannot use GTKWave GUI
3. ✅ **ALWAYS** fetch specifications autonomously before writing testbenches
4. ✅ **CAN** create filtered VCD files for human visualization
5. ✅ **ALWAYS** simulate before hardware testing (35x faster iteration)

### Workflow Summary
1. Fetch specification from web (fetch_webpage)
2. Write testbench based on specification
3. Run simulation using Python scripts
4. Analyze VCD using parse_vcd.py
5. Create filtered VCD for human if needed
6. Fix issues in simulation
7. Validate in hardware

### Getting Help
- Simulation guide: `docs/SIMULATION_GUIDE.md`
- VCD analysis guide: `docs/VCD_ANALYSIS_GUIDE.md`
- Testing guide: `docs/TESTING_GUIDE.md`
- Integration patterns: `docs/INTEGRATION_PATTERNS.md`
