# Simulation Tests

Example simulation test structure for Papilio libraries.

## Contents

- `example_tb.v` - Minimal working testbench example
- `run_all_sims.py` - Automated test runner
- `.gitignore` - Ignore compiled files

## Running Tests

```bash
# Run all simulation tests
python run_all_sims.py

# Or use the library-level runner
python ../../run_all_tests.py --sim-only
```

## Writing New Tests

1. **Create testbench file**: `tb_<module_name>.v`
2. **Follow naming convention**: Test files must start with `tb_`
3. **Include VCD dump**: For waveform analysis
4. **Add clear messages**: Use $display to narrate test progress
5. **Run automatically**: `run_all_sims.py` discovers all `tb_*.v` files

## Testbench Template

```verilog
`timescale 1ns / 1ps

module tb_module_name;
    reg clk = 0;
    reg rst = 1;
    // ... signals
    
    // Clock
    initial forever #10 clk = ~clk;
    
    // DUT
    module_name dut (
        .clk(clk),
        .rst(rst)
    );
    
    // Test
    initial begin
        $dumpfile("tb_module_name.vcd");
        $dumpvars(0, tb_module_name);
        
        rst = 1;
        #100;
        rst = 0;
        
        // Test cases here
        
        $display("=== All Tests Passed ===");
        $finish;
    end
endmodule
```

## See Also

- [../../AI_SKILL.md](../../AI_SKILL.md) - Simulation workflows
- [../../docs/SIMULATION_GUIDE.md](../../docs/SIMULATION_GUIDE.md) - Detailed guide
- [../../docs/VCD_ANALYSIS_GUIDE.md](../../docs/VCD_ANALYSIS_GUIDE.md) - VCD analysis
