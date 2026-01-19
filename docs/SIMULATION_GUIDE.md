# Simulation Guide

A comprehensive guide to FPGA simulation for Papilio libraries using Icarus Verilog.

## Table of Contents
- [Overview](#overview)
- [When to Simulate](#when-to-simulate)
- [Tool Setup](#tool-setup)
- [Testbench Development](#testbench-development)
- [Running Simulations](#running-simulations)
- [Analysis and Debugging](#analysis-and-debugging)
- [Best Practices](#best-practices)
- [Examples](#examples)

---

## Overview

Simulation is a critical part of FPGA development that allows you to:
- Verify logic before hardware
- Debug complex timing issues
- Test corner cases safely
- Iterate 35x faster than hardware
- Gain complete visibility into internal signals

### Why Simulation Matters

Real example from Papilio project:
- **Hardware debug**: 50 iterations × 35 seconds = 29 minutes minimum
- **Simulation debug**: 50 runs × 1 second = 50 seconds
- **Actual benefit**: Even greater - simulation revealed root cause quickly

---

## When to Simulate

### Always Simulate For
- Logic bugs and state machine verification
- Protocol compliance (SPI, I2C, Wishbone, etc.)
- Algorithm validation
- Timing relationships (functional correctness)
- Corner cases and edge conditions

### Hardware Still Needed For
- Exact timing margins (post-P&R verification)
- Signal integrity issues
- Real-world interface compliance
- Performance under load
- Temperature/voltage variations

### Decision Rule
**Simulate first, then validate in hardware.** Don't skip simulation even if you have hardware access.

---

## Tool Setup

### Required Tools

1. **Icarus Verilog** (iverilog, vvp)
   - Open-source Verilog simulator
   - Fast compilation and execution
   - Excellent for functional verification

2. **OSS CAD Suite** (recommended)
   - Includes iverilog, vvp, gtkwave
   - Pre-configured environment
   - Windows: `C:\\oss-cad-suite\\`
   - Download: https://github.com/YosysHQ/oss-cad-suite-build

3. **Python 3.7+**
   - For automation scripts
   - Cross-platform test runners

### Environment Setup (Automatic)

**CRITICAL**: Never invoke simulation tools directly!

The provided Python scripts handle all environment setup:
```bash
# Scripts automatically:
# 1. Call environment.bat on Windows (sets PATH, lib paths)
# 2. Locate iverilog/vvp tools
# 3. Handle cross-platform differences
# 4. Report clear errors

python tests/sim/run_all_sims.py  # Handles everything!
```

### Manual Setup (Not Recommended)

If you must run manually (not recommended):

**Windows**:
```cmd
call C:\\oss-cad-suite\\environment.bat
iverilog -g2012 -o sim.vvp testbench.v module.v
vvp sim.vvp
```

**Linux/macOS**:
```bash
export PATH="/path/to/oss-cad-suite/bin:$PATH"
iverilog -g2012 -o sim.vvp testbench.v module.v
vvp sim.vvp
```

**Problems with manual approach**:
- Forgetting environment.bat causes cryptic errors
- Path issues across platforms
- Inconsistent results
- Hard to debug

**Solution**: Use the Python scripts provided in `papilio_dev_tools`.

---

## Testbench Development

### Before Writing Code

**IMPORTANT**: Before writing any testbench, autonomously search for specifications:

1. **Use `fetch_webpage` to retrieve**:
   - Datasheets for ICs/components
   - Protocol specifications (SPI, I2C, Wishbone)
   - Timing diagrams
   - Example waveforms
   - State machine descriptions

2. **What to look for**:
   - Signal timing requirements (setup/hold times)
   - Protocol sequences (read/write operations)
   - Edge cases and error conditions
   - Reset behavior
   - Clock domain considerations

3. **Only ask user if**:
   - Component is custom/internal
   - Specification is ambiguous
   - Web search unsuccessful

**Benefits**:
- First testbench is accurate
- Covers edge cases from specification
- Correct timing relationships
- Fewer iterations needed

### Testbench Structure

```verilog
`timescale 1ns / 1ps

module tb_my_module;
    // 1. Signal declarations
    reg clk = 0;
    reg rst = 1;
    reg [7:0] data_in;
    wire [7:0] data_out;
    wire valid;
    
    // 2. Clock generation
    initial begin
        clk = 0;
        forever #18.5 clk = ~clk;  // 27MHz clock
    end
    
    // 3. Device Under Test (DUT) instantiation
    my_module dut (
        .clk(clk),
        .rst(rst),
        .data_in(data_in),
        .data_out(data_out),
        .valid(valid)
    );
    
    // 4. Reusable tasks
    task write_byte;
        input [7:0] data;
        begin
            data_in = data;
            @(posedge clk);
        end
    endtask
    
    task check_output;
        input [7:0] expected;
        begin
            if (data_out !== expected) begin
                $display("ERROR: Expected 0x%02h, got 0x%02h", 
                         expected, data_out);
                $finish;
            end else begin
                $display("PASS: Output = 0x%02h", data_out);
            end
        end
    endtask
    
    // 5. Test sequence
    initial begin
        // VCD dump for waveform analysis
        $dumpfile("tb_my_module.vcd");
        $dumpvars(0, tb_my_module);
        
        // Test begins
        $display("=== Test Start ===");
        
        // Reset sequence
        rst = 1;
        #200;  // Hold reset
        rst = 0;
        #100;  // Wait after reset
        
        // Test case 1
        $display("Test 1: Write single byte");
        write_byte(8'h42);
        #100;
        check_output(8'h42);
        
        // Test case 2
        $display("Test 2: Write multiple bytes");
        write_byte(8'h12);
        write_byte(8'h34);
        write_byte(8'h56);
        #100;
        
        // More tests...
        
        $display("=== All Tests Passed ===");
        $finish;
    end
    
    // 6. Timeout protection
    initial begin
        #1000000;  // 1ms timeout
        $display("ERROR: Test timeout!");
        $finish;
    end
    
endmodule
```

### Critical Elements

#### 1. Timescale
```verilog
`timescale 1ns / 1ps
```
- First number: Time unit (1ns)
- Second number: Time precision (1ps)

#### 2. Clock Generation
```verilog
reg clk = 0;
initial begin
    clk = 0;
    forever #(PERIOD/2) clk = ~clk;
end
```

Common frequencies:
```verilog
// 100MHz: period = 10ns
forever #5 clk = ~clk;

// 50MHz: period = 20ns  
forever #10 clk = ~clk;

// 27MHz: period = 37.037ns
forever #18.5 clk = ~clk;

// 1MHz: period = 1000ns
forever #500 clk = ~clk;
```

#### 3. Reset Handling
```verilog
reg rst = 1;  // Start in reset
initial begin
    rst = 1;
    #200;      // Hold for several clock cycles
    rst = 0;   // Release reset
    #100;      // Wait before starting tests
end
```

#### 4. Reusable Tasks
Tasks encapsulate common operations:

```verilog
// SPI transfer task
task spi_transfer;
    input [7:0] tx_data;
    output [7:0] rx_data;
    integer i;
    begin
        spi_cs_n = 0;  // Assert chip select
        #100;          // Setup time
        
        rx_data = 8'h00;
        for (i = 7; i >= 0; i = i - 1) begin
            spi_mosi = tx_data[i];  // Output bit
            #500 spi_sclk = 1;      // Clock high
            rx_data[i] = spi_miso;  // Sample input
            #500 spi_sclk = 0;      // Clock low
        end
        
        #100;          // Hold time
        spi_cs_n = 1;  // Deassert chip select
    end
endtask

// Usage:
reg [7:0] rx;
spi_transfer(8'hAA, rx);
$display("Received: 0x%02h", rx);
```

#### 5. VCD Dump
```verilog
initial begin
    $dumpfile("tb_module.vcd");    // Output file
    $dumpvars(0, tb_module);       // Dump all signals in module
    
    // Or dump specific signals:
    // $dumpvars(1, tb_module);     // Only top-level signals
    // $dumpvars(2, tb_module.dut); // Two levels deep
end
```

#### 6. Display Messages
```verilog
// Informational
$display("Starting test phase 2");
$display("Count = %d", counter);
$display("Data = 0x%02h", data);

// Formatted display
$display("Time=%0t: state=%b, count=%d", $time, state, count);

// Errors
$error("Unexpected value: %d", value);

// Finish simulation
$finish;  // End successfully
$stop;    // Pause (interactive mode)
```

#### 7. Timing Control

```verilog
// Absolute delay
#100;  // Wait 100 time units

// Wait for event
@(posedge clk);       // Wait for rising edge
@(negedge clk);       // Wait for falling edge
@(signal);            // Wait for any change

// Wait for condition
wait (ready == 1);    // Block until ready
wait (count > 10);

// Conditional events
@(posedge clk or negedge rst);  // Either event
```

#### 8. Result Checking

```verilog
// Simple check
if (actual == expected)
    $display("PASS: Value correct");
else begin
    $display("FAIL: Expected %d, got %d", expected, actual);
    $finish;
end

// With tolerance
if ((actual >= expected - 1) && (actual <= expected + 1))
    $display("PASS: Within tolerance");

// Assertion (SystemVerilog)
assert (condition) else $error("Assertion failed");
```

### Timing Considerations

#### Inter-Transaction Delays
Allow time for state machines and logic to settle:

```verilog
// Before starting transaction
#100;  // Setup time

// Between transactions
#500;  // Processing time

// After transaction
#100;  // Hold time
```

#### DMA/State Machine Delays
Complex operations need significant time:

```verilog
// Write data
for (i = 0; i < 256; i++) begin
    write_byte(i);
end

// Wait for DMA to complete
#50000;  // 50μs @ 1ns timescale

// Read data back
for (i = 0; i < 256; i++) begin
    read_byte(rx);
end
```

#### Clock Domain Crossing
When crossing clock domains, allow synchronization time:

```verilog
// Change signal in domain A
signal_a = 1;

// Wait for synchronization to domain B (2-3 clock cycles of slower domain)
repeat (3) @(posedge clk_b);

// Now safe to check in domain B
if (signal_b_sync == 1) $display("Synchronized");
```

---

## Running Simulations

### Using Python Scripts (Recommended)

```bash
# Run all simulations in tests/sim/
python tests/sim/run_all_sims.py

# Output shows:
# - Which testbenches are found
# - Compilation status
# - Simulation results
# - VCD file locations
```

The script:
- Discovers all `tb_*.v` files automatically
- Sets up environment (calls environment.bat on Windows)
- Compiles with correct include paths
- Runs simulation
- Reports results clearly
- Generates VCD files

### Script Internals (FYI)

The `run_all_sims.py` script does:

1. **Environment setup**:
   ```python
   if platform.system() == "Windows":
       subprocess.run(["cmd", "/c", "call", "C:\\\\oss-cad-suite\\\\environment.bat"])
   ```

2. **Auto-discovery**:
   ```python
   testbenches = glob.glob("tb_*.v")
   ```

3. **Compilation**:
   ```python
   iverilog_cmd = [
       "iverilog",
       "-g2012",               # SystemVerilog 2012
       "-o", "sim.vvp",        # Output file
       "-I", "../gateware",    # Include path
       testbench,
       "module.v"
   ]
   subprocess.run(iverilog_cmd)
   ```

4. **Execution**:
   ```python
   vvp_cmd = ["vvp", "sim.vvp"]
   subprocess.run(vvp_cmd)
   ```

### Manual Compilation (Not Recommended)

If you must compile manually:

```bash
# Set up environment (Windows)
call C:\\oss-cad-suite\\environment.bat

# Compile
iverilog -g2012 ^
    -o sim.vvp ^
    -I ../../libs/papilio_hdl_blocks ^
    testbench.v ^
    module1.v ^
    module2.v

# Run
vvp sim.vvp

# View waveforms (optional)
gtkwave output.vcd
```

Common `iverilog` flags:
- `-g2012`: Use SystemVerilog 2012 standard
- `-g2005`: Use Verilog 2005 standard  
- `-o filename`: Output file
- `-I path`: Include directory
- `-D DEFINE`: Define preprocessor macro
- `-v`: Verbose output
- `-Wall`: All warnings

---

## Analysis and Debugging

### Using parse_vcd.py (AI Agents)

**Primary tool for AI agents**:

```bash
# Analyze entire VCD
python scripts/parse_vcd.py tb_module.vcd

# Specific signals only
python scripts/parse_vcd.py tb_module.vcd --signals clk,state,counter

# JSON output for programmatic analysis
python scripts/parse_vcd.py tb_module.vcd --format json

# Create filtered VCD for human viewing
python scripts/parse_vcd.py tb_module.vcd \
    --signals clk,state,data,valid \
    --output filtered.vcd
```

See [VCD_ANALYSIS_GUIDE.md](VCD_ANALYSIS_GUIDE.md) for complete details.

### Debugging Workflow

1. **Run simulation**, note failure:
   ```
   Read[3]: 0x20 FAIL (expected 0x03)
   ```

2. **Analyze VCD** to find relevant signals:
   ```bash
   python scripts/parse_vcd.py tb.vcd --signals state,counter,data
   ```

3. **Create filtered VCD** for human if needed:
   ```bash
   python scripts/parse_vcd.py tb.vcd \
       --signals clk,spi_cs_n,state,shift_reg,bit_count \
       --output debug.vcd
   ```

4. **Identify problem** in waveform analysis

5. **Modify testbench** or design

6. **Re-run simulation** (fast iteration!)

7. **Verify fix**

### Common Debug Techniques

#### Check Reset Behavior
```verilog
initial begin
    $display("=== Reset Test ===");
    rst = 1;
    #200;
    rst = 0;
    #10;
    
    // Check reset values
    if (state != IDLE) $error("State not reset!");
    if (counter != 0) $error("Counter not reset!");
end
```

#### Monitor State Transitions
```verilog
always @(posedge clk) begin
    if (state != prev_state) begin
        $display("Time=%0t: State %d -> %d", $time, prev_state, state);
        prev_state <= state;
    end
end
```

#### Track Signal History
```verilog
always @(posedge clk) begin
    $display("Time=%0t: count=%d, valid=%b, data=0x%02h",
             $time, count, valid, data);
end
```

#### Conditional Breakpoints
```verilog
always @(posedge clk) begin
    if (error_condition) begin
        $display("ERROR CONDITION at time %0t", $time);
        $display("  State: %d", state);
        $display("  Data: 0x%02h", data);
        $finish;  // Stop simulation
    end
end
```

---

## Best Practices

### Testbench Development

1. **Start Simple**
   - Test one feature at a time
   - Use small data sets (10 bytes before 256)
   - Add complexity gradually

2. **Use Meaningful Names**
   - `byte_counter` not `cnt`
   - `tx_fifo_ready` not `sig42`
   - `STATE_IDLE` not `2'b00`

3. **Document Intentions**
   ```verilog
   // Test multi-byte burst with inter-byte gap
   // This verifies the FIFO doesn't underrun
   // Expected: 10 bytes transferred successfully
   ```

4. **Test Edge Cases**
   - Empty conditions
   - Full conditions
   - Back-to-back transactions
   - Maximum values
   - Minimum values

5. **Use Assertions**
   ```verilog
   if (fifo_count > FIFO_DEPTH) begin
       $error("FIFO overflow!");
       $finish;
   end
   ```

### Timing Best Practices

1. **Synchronous Design**
   ```verilog
   // Good: Synchronous
   always @(posedge clk) begin
       if (rst)
           counter <= 0;
       else if (enable)
           counter <= counter + 1;
   end
   ```

2. **Avoid Race Conditions**
   ```verilog
   // Bad: Race condition
   initial begin
       clk = 0;
       data = 8'hAA;  // Same time as clock edge!
   end
   
   // Good: Setup time
   initial begin
       clk = 0;
       #10;  // Setup before first clock
       data = 8'hAA;
   end
   ```

3. **Clock Domain Crossing**
   ```verilog
   // Use synchronizer for CDC
   reg sync1, sync2;
   always @(posedge clk_dest) begin
       sync1 <= signal_src;
       sync2 <= sync1;  // Use sync2, not signal_src
   end
   ```

### Performance Tips

1. **Limit VCD Scope**
   ```verilog
   // Dump only DUT, not testbench
   $dumpvars(1, tb_module.dut);
   ```

2. **Use `+define` for Debug**
   ```verilog
   `ifdef DEBUG
       $display("Debug: value=%d", value);
   `endif
   ```
   
   Compile with: `iverilog -DDEBUG ...`

3. **Timescale Appropriately**
   ```verilog
   // For high-speed designs
   `timescale 1ns / 1ps  // Good precision
   
   // For slower designs
   `timescale 1us / 1ns  // Faster simulation
   ```

---

## Examples

### Example 1: Simple Counter

```verilog
`timescale 1ns / 1ps

module tb_counter;
    reg clk = 0;
    reg rst = 1;
    reg enable = 0;
    wire [7:0] count;
    
    // 50MHz clock
    initial forever #10 clk = ~clk;
    
    // DUT
    counter dut (
        .clk(clk),
        .rst(rst),
        .enable(enable),
        .count(count)
    );
    
    // Test
    initial begin
        $dumpfile("tb_counter.vcd");
        $dumpvars(0, tb_counter);
        
        // Reset
        rst = 1;
        #100;
        rst = 0;
        #50;
        
        // Test counting
        $display("=== Test: Counting ===");
        enable = 1;
        repeat (10) begin
            @(posedge clk);
            $display("Count = %d", count);
        end
        
        // Test pause
        $display("=== Test: Pause ===");
        enable = 0;
        repeat (5) @(posedge clk);
        
        // Test resume
        $display("=== Test: Resume ===");
        enable = 1;
        repeat (5) @(posedge clk);
        
        $display("=== Test Complete ===");
        $finish;
    end
    
    initial begin
        #10000;  // Timeout
        $error("Test timeout!");
        $finish;
    end
endmodule
```

### Example 2: SPI Master/Slave

```verilog
`timescale 1ns / 1ps

module tb_spi;
    reg clk = 0;
    reg rst = 1;
    
    // SPI signals
    reg spi_sclk = 0;
    reg spi_cs_n = 1;
    reg spi_mosi = 0;
    wire spi_miso;
    
    // System clock: 27MHz
    initial forever #18.5 clk = ~clk;
    
    // DUT
    spi_slave dut (
        .clk(clk),
        .rst(rst),
        .spi_sclk(spi_sclk),
        .spi_cs_n(spi_cs_n),
        .spi_mosi(spi_mosi),
        .spi_miso(spi_miso)
    );
    
    // SPI transfer task
    task spi_transfer;
        input [7:0] tx_data;
        output [7:0] rx_data;
        integer i;
        begin
            spi_cs_n = 0;  // Assert CS
            #100;          // Setup time
            
            rx_data = 8'h00;
            for (i = 7; i >= 0; i = i - 1) begin
                spi_mosi = tx_data[i];
                #500 spi_sclk = 1;  // 1MHz SPI clock
                #500 spi_sclk = 0;
                rx_data[i] = spi_miso;
            end
            
            #100;  // Hold time
            spi_cs_n = 1;  // Deassert CS
            #500;  // Inter-transaction delay
        end
    endtask
    
    // Test sequence
    initial begin
        $dumpfile("tb_spi.vcd");
        $dumpvars(0, tb_spi);
        
        // Reset
        rst = 1;
        #200;
        rst = 0;
        #100;
        
        // Test transfers
        reg [7:0] rx;
        
        $display("=== Test: Single Transfer ===");
        spi_transfer(8'hA5, rx);
        $display("TX: 0xA5, RX: 0x%02h", rx);
        
        $display("=== Test: Multiple Transfers ===");
        spi_transfer(8'h00, rx);
        spi_transfer(8'h01, rx);
        spi_transfer(8'h02, rx);
        
        $display("=== Test Complete ===");
        $finish;
    end
    
    initial begin
        #100000;  // 100μs timeout
        $error("Test timeout!");
        $finish;
    end
endmodule
```

### Example 3: FIFO Verification

```verilog
`timescale 1ns / 1ps

module tb_fifo;
    reg clk = 0;
    reg rst = 1;
    
    // Write interface
    reg wr_en = 0;
    reg [7:0] wr_data = 0;
    wire wr_full;
    
    // Read interface
    reg rd_en = 0;
    wire [7:0] rd_data;
    wire rd_empty;
    
    // Clock: 100MHz
    initial forever #5 clk = ~clk;
    
    // DUT
    fifo #(
        .DEPTH(8),
        .WIDTH(8)
    ) dut (
        .clk(clk),
        .rst(rst),
        .wr_en(wr_en),
        .wr_data(wr_data),
        .wr_full(wr_full),
        .rd_en(rd_en),
        .rd_data(rd_data),
        .rd_empty(rd_empty)
    );
    
    // Write task
    task write_fifo;
        input [7:0] data;
        begin
            @(posedge clk);
            wr_data = data;
            wr_en = 1;
            @(posedge clk);
            wr_en = 0;
            $display("Write: 0x%02h", data);
        end
    endtask
    
    // Read task
    task read_fifo;
        output [7:0] data;
        begin
            @(posedge clk);
            rd_en = 1;
            @(posedge clk);
            rd_en = 0;
            data = rd_data;
            $display("Read: 0x%02h", data);
        end
    endtask
    
    // Test sequence
    initial begin
        $dumpfile("tb_fifo.vcd");
        $dumpvars(0, tb_fifo);
        
        // Reset
        rst = 1;
        repeat (3) @(posedge clk);
        rst = 0;
        repeat (2) @(posedge clk);
        
        // Test 1: Write and read
        $display("=== Test: Write then Read ===");
        write_fifo(8'hAA);
        write_fifo(8'hBB);
        write_fifo(8'hCC);
        
        reg [7:0] rx;
        read_fifo(rx);
        if (rx != 8'hAA) $error("Expected 0xAA");
        read_fifo(rx);
        if (rx != 8'hBB) $error("Expected 0xBB");
        read_fifo(rx);
        if (rx != 8'hCC) $error("Expected 0xCC");
        
        // Test 2: Fill FIFO
        $display("=== Test: Fill FIFO ===");
        repeat (8) begin
            if (wr_full) begin
                $display("FIFO full (expected)");
                break;
            end
            write_fifo(8'h55);
        end
        
        // Test 3: Empty FIFO
        $display("=== Test: Empty FIFO ===");
        repeat (8) begin
            if (rd_empty) begin
                $display("FIFO empty (expected)");
                break;
            end
            read_fifo(rx);
        end
        
        $display("=== Test Complete ===");
        $finish;
    end
    
    initial begin
        #100000;
        $error("Test timeout!");
        $finish;
    end
endmodule
```

---

## Summary

Key points for successful simulation:

1. ✅ **Use provided Python scripts** - Never invoke iverilog/vvp directly
2. ✅ **Fetch specifications first** - Before writing testbenches
3. ✅ **Start simple** - Test basic functionality before complex cases
4. ✅ **Use tasks** - Encapsulate common operations
5. ✅ **Clear phases** - Use $display to narrate test progress
6. ✅ **Proper timing** - Allow setup/hold times and processing delays
7. ✅ **Timeout protection** - Catch infinite loops early
8. ✅ **VCD analysis** - Use parse_vcd.py for debugging

Simulation is your fastest path to working hardware!
