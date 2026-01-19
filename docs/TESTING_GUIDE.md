# Testing Guide

Best practices for simulation and hardware testing of Papilio FPGA libraries.

## Table of Contents
- [Overview](#overview)
- [Testing Philosophy](#testing-philosophy)
- [Simulation Testing](#simulation-testing)
- [Hardware Testing](#hardware-testing)
- [Test Organization](#test-organization)
- [Regression Testing](#regression-testing)
- [Coverage Considerations](#coverage-considerations)
- [Best Practices](#best-practices)

---

## Overview

Comprehensive testing combines simulation (fast iteration, complete visibility) with hardware validation (real-world verification).

### Testing Pyramid

```
           /\
          /  \     Hardware Tests
         /    \    (Real-world validation)
        /------\
       /        \  Integration Tests
      /          \ (Multi-module verification)
     /------------\
    /              \ Unit Tests
   /                \ (Individual modules)
  /------------------\
  Simulation Tests     Hardware Tests
  (Fast iteration)     (Final validation)
```

---

## Testing Philosophy

### Test Early, Test Often

1. **Write testbench** while developing module
2. **Simulate continuously** during development
3. **Validate in hardware** after simulation passes
4. **Regression test** before releases

### Specification-First Approach

**Before writing any test**:

1. **Autonomously fetch specifications**:
   - Use `fetch_webpage` to retrieve datasheets, protocol specs
   - Search for timing diagrams, waveforms, state machines
   - Review signal requirements, setup/hold times
   - Check example transactions and sequences

2. **Analyze the specification**:
   - Identify normal operation scenarios
   - Find edge cases and error conditions
   - Note timing requirements
   - Understand state transitions

3. **Only ask user if**:
   - Component is custom/internal (not documented online)
   - Specification is ambiguous or contradictory
   - Need clarification on specific requirements
   - Web search unsuccessful

**Benefits**:
- Tests based on actual requirements
- Better edge case coverage
- Correct timing from the start
- Fewer false positives/negatives

### Progressive Testing

```
Step 1: Unit Test (single module)
  ↓
Step 2: Integration Test (multiple modules)
  ↓
Step 3: System Test (complete design)
  ↓
Step 4: Hardware Validation
```

---

## Simulation Testing

### Test Structure

```
tests/sim/
├── README.md              # How to run tests
├── run_all_sims.py        # Automated test runner
├── tb_module1.v           # Unit test for module1
├── tb_module2.v           # Unit test for module2
├── tb_integration.v       # Integration test
└── .gitignore            # Ignore *.vvp, *.vcd
```

### Unit Test Template

```verilog
`timescale 1ns / 1ps

module tb_module_name;
    // 1. Signals
    reg clk = 0;
    reg rst = 1;
    // ... module-specific signals
    
    // 2. Clock generation
    initial forever #(PERIOD/2) clk = ~clk;
    
    // 3. DUT instantiation
    module_name dut (
        .clk(clk),
        .rst(rst),
        // ... connections
    );
    
    // 4. Test sequence
    initial begin
        // VCD dump
        $dumpfile("tb_module_name.vcd");
        $dumpvars(0, tb_module_name);
        
        // Reset
        rst = 1;
        #200;
        rst = 0;
        #100;
        
        // Test cases
        test_case_1();
        test_case_2();
        test_case_3();
        
        $display("=== All Tests Passed ===");
        $finish;
    end
    
    // 5. Test case tasks
    task test_case_1;
        begin
            $display("=== Test: Basic Operation ===");
            // ... test code ...
        end
    endtask
    
    // 6. Timeout
    initial begin
        #TIMEOUT;
        $error("Test timeout!");
        $finish;
    end
endmodule
```

### What to Test

#### Functional Correctness
- **Normal operation**: Does it work as specified?
- **Edge cases**: Empty, full, overflow, underflow
- **Error conditions**: Invalid inputs, out-of-range values
- **State transitions**: All legal paths through FSM

#### Timing Correctness
- **Setup times**: Data stable before clock?
- **Hold times**: Data stable after clock?
- **Propagation delays**: Output changes appropriately?
- **Clock domain crossing**: Proper synchronization?

#### Protocol Compliance
- **Signal sequences**: Correct order of operations?
- **Timing relationships**: Meet protocol timing?
- **Handshaking**: Ready/valid/ack sequences correct?

### Test Patterns

#### Pattern 1: Sequential Operations

```verilog
task test_sequential;
    integer i;
    begin
        $display("=== Test: Sequential Writes ===");
        for (i = 0; i < 16; i = i + 1) begin
            write_byte(i[7:0]);
            #100;  // Inter-write delay
        end
        
        $display("=== Test: Sequential Reads ===");
        for (i = 0; i < 16; i = i + 1) begin
            read_byte(rx_data);
            if (rx_data != i[7:0]) begin
                $error("Mismatch at %d: got 0x%02h", i, rx_data);
                $finish;
            end
        end
    end
endtask
```

#### Pattern 2: Burst Operations

```verilog
task test_burst;
    integer i;
    begin
        $display("=== Test: Burst Transfer ===");
        
        start_burst();
        for (i = 0; i < 256; i = i + 1) begin
            transfer_byte(i[7:0]);
            // No delay between bytes in burst
        end
        end_burst();
        
        #10000;  // Wait for processing
        verify_burst_results();
    end
endtask
```

#### Pattern 3: Back-to-Back Operations

```verilog
task test_back_to_back;
    begin
        $display("=== Test: Back-to-Back Transfers ===");
        
        // No delay between operations
        write_operation(8'hAA);
        write_operation(8'hBB);
        write_operation(8'hCC);
        
        // Verify FIFO/buffer handles this correctly
    end
endtask
```

#### Pattern 4: Stress Testing

```verilog
task test_stress;
    integer i;
    begin
        $display("=== Test: Stress (Max Speed) ===");
        
        // Fill at maximum rate
        for (i = 0; i < FIFO_DEPTH*2; i = i + 1) begin
            @(posedge clk);
            if (!full) begin
                write_enable = 1;
                write_data = i[7:0];
            end else begin
                write_enable = 0;
            end
        end
        
        // Empty at maximum rate
        for (i = 0; i < FIFO_DEPTH*2; i = i + 1) begin
            @(posedge clk);
            if (!empty) begin
                read_enable = 1;
            end else begin
                read_enable = 0;
            end
        end
    end
endtask
```

### Running Simulation Tests

```bash
# Run all simulations (recommended)
python tests/sim/run_all_sims.py

# Run specific testbench (manual - not recommended)
# Don't do this - scripts handle environment setup!
# iverilog tb_module.v module.v
# vvp a.out
```

---

## Hardware Testing

### Test Structure

#### Option A: Standalone Test Project
```
tests/hw/
├── README.md              # How to run tests
├── platformio.ini         # Standalone project config
├── run_hw_tests.py        # Test automation
└── src/
    ├── test_spi.cpp       # SPI tests
    ├── test_wishbone.cpp  # Wishbone tests
    └── main.cpp           # Test coordinator
```

#### Option B: Workspace Integration
```
workspace/
├── platformio.ini         # Main project config
├── test/
│   └── test_papilio_module/
│       └── test_module.cpp
└── libs/
    └── papilio_module/
```

See [INTEGRATION_PATTERNS.md](INTEGRATION_PATTERNS.md) for details.

### Hardware Test Template

```cpp
#include <Arduino.h>
#include <unity.h>

// Test fixtures
void setUp(void) {
    // Called before each test
    Serial.begin(115200);
}

void tearDown(void) {
    // Called after each test
}

// Test case
void test_basic_read_write(void) {
    const uint8_t test_data = 0x42;
    
    // Write
    write_register(REG_ADDR, test_data);
    delay(10);  // Allow time for write
    
    // Read
    uint8_t read_data = read_register(REG_ADDR);
    
    // Verify
    TEST_ASSERT_EQUAL_HEX8(test_data, read_data);
}

void test_burst_transfer(void) {
    uint8_t write_data[256];
    uint8_t read_data[256];
    
    // Prepare test data
    for (int i = 0; i < 256; i++) {
        write_data[i] = i & 0xFF;
    }
    
    // Write burst
    write_burst(BASE_ADDR, write_data, 256);
    delay(100);  // Processing time
    
    // Read burst
    read_burst(BASE_ADDR, read_data, 256);
    
    // Verify
    TEST_ASSERT_EQUAL_HEX8_ARRAY(write_data, read_data, 256);
}

void test_edge_cases(void) {
    // Test minimum value
    write_register(REG_ADDR, 0x00);
    TEST_ASSERT_EQUAL_HEX8(0x00, read_register(REG_ADDR));
    
    // Test maximum value
    write_register(REG_ADDR, 0xFF);
    TEST_ASSERT_EQUAL_HEX8(0xFF, read_register(REG_ADDR));
    
    // Test wraparound
    write_register(REG_COUNTER, 0xFF);
    increment_counter();
    TEST_ASSERT_EQUAL_HEX8(0x00, read_register(REG_COUNTER));
}

void test_timing(void) {
    unsigned long start = micros();
    
    write_burst(BASE_ADDR, test_data, 256);
    
    unsigned long duration = micros() - start;
    
    // Verify performance
    TEST_ASSERT_LESS_THAN(10000, duration);  // < 10ms
    
    Serial.printf("Burst write took %lu µs\n", duration);
}

void setup() {
    delay(2000);  // Wait for Serial
    
    UNITY_BEGIN();
    
    RUN_TEST(test_basic_read_write);
    RUN_TEST(test_burst_transfer);
    RUN_TEST(test_edge_cases);
    RUN_TEST(test_timing);
    
    UNITY_END();
}

void loop() {
    // Tests run once
}
```

### What to Test in Hardware

#### Functional Verification
- **Basic operations**: Read/write single registers
- **Burst operations**: Multi-byte transfers
- **Timing**: Meets performance requirements
- **Edge cases**: Boundary conditions work in real hardware

#### Real-World Conditions
- **Signal integrity**: No glitches or noise issues
- **Clock stability**: Design works at specified frequencies
- **Temperature**: Works across temperature range (if critical)
- **Power**: Works with real power supply variations

#### Integration
- **Multiple modules**: Work together correctly
- **Interrupt handling**: ISRs respond appropriately
- **DMA operations**: Background transfers work
- **Concurrent operations**: Multi-tasking scenarios

### Running Hardware Tests

```bash
# Upload and run tests
python tests/hw/run_hw_tests.py

# Or use PlatformIO directly
pio test -e esp32

# Monitor output
pio device monitor
```

---

## Test Organization

### Directory Structure

```
library_name/
├── src/               # Library source code
├── gateware/          # FPGA modules
├── tests/
│   ├── sim/          # Simulation tests
│   │   ├── README.md
│   │   ├── run_all_sims.py
│   │   ├── tb_module1.v
│   │   └── tb_module2.v
│   └── hw/           # Hardware tests
│       ├── README.md
│       ├── platformio.ini (Option A)
│       ├── run_hw_tests.py
│       └── src/
│           └── test_module.cpp
└── run_all_tests.py  # Top-level test runner
```

### Test Naming

**Simulation**:
- `tb_<module_name>.v` - Unit test
- `tb_<feature>_integration.v` - Integration test
- `tb_<system>_full.v` - System test

**Hardware**:
- `test_<module>_basic.cpp` - Basic functionality
- `test_<module>_timing.cpp` - Timing/performance
- `test_<module>_stress.cpp` - Stress/edge cases

### Documentation

Each test directory should have `README.md`:

```markdown
# Module Tests

## Simulation Tests

### tb_module_basic.v
- Tests basic read/write operations
- Verifies reset behavior
- Checks state machine transitions

### tb_module_burst.v
- Tests burst transfers
- Verifies FIFO operation
- Checks back-to-back transactions

## Hardware Tests

### test_module_basic.cpp
- Basic register read/write
- Verify communication
- Check data integrity

### test_module_performance.cpp
- Measure throughput
- Verify timing requirements
- Test at different clock speeds

## Running Tests

```bash
# All tests
python ../../run_all_tests.py

# Simulation only
python sim/run_all_sims.py

# Hardware only
python hw/run_hw_tests.py
```
```

---

## Regression Testing

### Test Automation

Top-level test runner (`run_all_tests.py`):

```python
#!/usr/bin/env python3
"""
Regression test runner for library_name
Runs both simulation and hardware tests
"""

import sys
import subprocess
import argparse

def run_sim_tests(verbose=False):
    """Run simulation tests"""
    print("\n" + "="*60)
    print("Running Simulation Tests")
    print("="*60)
    
    try:
        result = subprocess.run(
            ["python", "tests/sim/run_all_sims.py"],
            check=True,
            capture_output=not verbose
        )
        print("✅ Simulation tests PASSED")
        return True
    except subprocess.CalledProcessError:
        print("❌ Simulation tests FAILED")
        return False
    except FileNotFoundError:
        print("⚠️  Simulation tests not found (skipping)")
        return True

def run_hw_tests(verbose=False):
    """Run hardware tests"""
    print("\n" + "="*60)
    print("Running Hardware Tests")
    print("="*60)
    
    try:
        result = subprocess.run(
            ["python", "tests/hw/run_hw_tests.py"],
            check=True,
            capture_output=not verbose
        )
        print("✅ Hardware tests PASSED")
        return True
    except subprocess.CalledProcessError:
        print("❌ Hardware tests FAILED")
        return False
    except FileNotFoundError:
        print("⚠️  Hardware tests not found (skipping)")
        return True

def main():
    parser = argparse.ArgumentParser(description="Run library tests")
    parser.add_argument("--sim-only", action="store_true",
                       help="Run simulation tests only")
    parser.add_argument("--hw-only", action="store_true",
                       help="Run hardware tests only")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Verbose output")
    
    args = parser.parse_args()
    
    # Run tests
    results = []
    
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
        symbol = "✅" if passed else "❌"
        print(f"{symbol} {test_type}: {status}")
        all_passed = all_passed and passed
    
    print("="*60)
    
    if all_passed:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n💥 Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

### Running Regression Tests

```bash
# All tests (simulation + hardware)
python run_all_tests.py

# Simulation only (fast)
python run_all_tests.py --sim-only

# Hardware only
python run_all_tests.py --hw-only

# Verbose output
python run_all_tests.py -v
```

### Continuous Integration (Future)

Placeholder for CI/CD integration:

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  simulation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install Icarus Verilog
        run: sudo apt-get install iverilog
      - name: Run Simulation Tests
        run: python run_all_tests.py --sim-only
  
  hardware:
    runs-on: ubuntu-latest
    # Requires hardware-in-the-loop setup
    # TBD based on infrastructure
```

---

## Coverage Considerations

### Simulation Coverage

**Code Coverage** (what was executed):
- Line coverage: All lines executed?
- Branch coverage: All if/else paths taken?
- State coverage: All FSM states visited?

**Functional Coverage** (what was tested):
- All features tested?
- All edge cases covered?
- All protocols verified?

### Manual Coverage Checklist

For each module, verify tests cover:

- [ ] Normal operation (happy path)
- [ ] Edge cases (boundaries)
- [ ] Error conditions (invalid inputs)
- [ ] Reset behavior (initial state)
- [ ] All FSM states and transitions
- [ ] Full/empty conditions (FIFOs, buffers)
- [ ] Overflow/underflow handling
- [ ] Timing requirements (setup/hold)
- [ ] Clock domain crossings
- [ ] All protocol operations

### Coverage Tools (Future)

Consider tools like:
- **Verilator**: Fast simulation with coverage
- **GTKWave + VCD analysis**: Manual coverage analysis
- **Custom scripts**: parse_vcd.py based coverage checks

---

## Best Practices

### General

1. **Test first, code second** (TDD when possible)
2. **Automate everything** (no manual test running)
3. **Fast feedback** (simulation before hardware)
4. **Clear pass/fail** (no ambiguous results)
5. **Document tests** (what and why)

### Simulation

1. **Use specification first**: Fetch datasheets/specs autonomously
2. **Use provided scripts**: Never invoke iverilog/vvp directly
3. **Start simple**: Basic tests before complex scenarios
4. **Use tasks**: Reusable test operations
5. **Clear phases**: Display messages for test progress
6. **Timeout protection**: Catch infinite loops
7. **VCD analysis**: Use parse_vcd.py for debugging

### Hardware

1. **Simulation first**: Catch bugs before hardware
2. **Small iterations**: Test incrementally
3. **Timing measurements**: Verify performance
4. **Error handling**: Test failure modes
5. **Real conditions**: Test with actual signals/timing

### Maintenance

1. **Keep tests updated**: Tests evolve with code
2. **Don't skip tests**: Regression catches issues
3. **Fix broken tests immediately**: Don't accumulate technical debt
4. **Add tests for bugs**: Prevent regression
5. **Review test coverage**: Ensure adequate testing

---

## Summary Checklist

Before releasing a module:

- [ ] Unit tests written and passing (simulation)
- [ ] Integration tests written and passing (simulation)
- [ ] Hardware tests written and passing
- [ ] Edge cases covered
- [ ] Performance verified (timing)
- [ ] Documentation complete (README, test docs)
- [ ] Regression tests automated (run_all_tests.py)
- [ ] All tests pass on clean checkout

Testing is not optional - it's how we ensure quality!
