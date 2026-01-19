# Papilio Dev Tools

Development infrastructure, testing frameworks, simulation skills, and debugging tools for Papilio library development.

## Purpose

This library provides:
- **AI Skills**: Development knowledge for AI coding assistants in `AI_SKILL.md`
- **Testing Framework**: Templates and patterns for simulation and hardware tests
- **Reusable Scripts**: Tools for VCD analysis, simulation, and test automation
- **Documentation**: Comprehensive guides for FPGA simulation, testing, and debugging

## For AI Assistants

**Start here:** Read [`AI_SKILL.md`](AI_SKILL.md) for:
- FPGA simulation workflows
- VCD analysis techniques
- Hardware debugging strategies
- Test integration patterns

## For Developers

### Quick Start

1. **Simulation Testing**
   ```bash
   # Run simulations (automatically handles environment setup)
   python tests/sim/run_all_sims.py
   
   # Analyze VCD output
   python scripts/parse_vcd.py output.vcd
   
   # Create filtered VCD for GTKWave
   python scripts/parse_vcd.py output.vcd --signals clk,state,data --output filtered.vcd
   ```

2. **Hardware Testing**
   ```bash
   # Run hardware tests
   python tests/hw/run_hw_tests.py
   ```

3. **Full Regression**
   ```bash
   # Run all tests (sim + hardware)
   python run_all_tests.py
   ```

### Documentation

- [`docs/SIMULATION_GUIDE.md`](docs/SIMULATION_GUIDE.md) - Comprehensive simulation guide
- [`docs/VCD_ANALYSIS_GUIDE.md`](docs/VCD_ANALYSIS_GUIDE.md) - VCD file analysis guide
- [`docs/TESTING_GUIDE.md`](docs/TESTING_GUIDE.md) - Testing best practices
- [`docs/INTEGRATION_PATTERNS.md`](docs/INTEGRATION_PATTERNS.md) - Test integration patterns

### Tools

- **parse_vcd.py** - VCD file parser and analyzer
  - Text/JSON output for AI agent analysis
  - Filtered VCD generation for clean GTKWave viewing
  - Signal extraction and timing analysis
  
- **run_sim.py** - Cross-platform simulation runner
  - Automatic environment setup (OSS CAD Suite)
  - Handles iverilog paths and configuration
  - Error reporting

- **run_regression_tests.py** - Test automation template
  - Run simulation and hardware tests
  - Test result aggregation
  - Report generation

- **generate_test_report.py** - Test report generator
  - Markdown and JSON output
  - Pass/fail summaries
  - Timing statistics

## Directory Structure

```
papilio_dev_tools/
├── library.json                    # PlatformIO library metadata
├── README.md                       # This file
├── AI_SKILL.md                     # AI assistant skills and workflows
├── docs/                           # Detailed guides
│   ├── SIMULATION_GUIDE.md
│   ├── VCD_ANALYSIS_GUIDE.md
│   ├── TESTING_GUIDE.md
│   └── INTEGRATION_PATTERNS.md
├── scripts/                        # Reusable tools
│   ├── parse_vcd.py
│   ├── run_sim.py
│   ├── run_regression_tests.py
│   └── generate_test_report.py
├── run_all_tests.py                # Top-level test runner
└── tests/                          # Test templates
    ├── sim/                        # Simulation test examples
    └── hw/                         # Hardware test examples
```

## Using in Your Library

### Option A: Reference the Skills

Add to your library's AI_SKILL.md:
```markdown
## Development Skills
See [papilio_dev_tools/AI_SKILL.md](../papilio_dev_tools/AI_SKILL.md) for:
- FPGA simulation workflows
- VCD analysis techniques
- Hardware debugging strategies
```

### Option B: Integrate Test Structure

1. Copy `tests/` structure to your library
2. Adapt testbenches and hardware tests
3. Use `scripts/parse_vcd.py` for VCD analysis
4. Reference integration patterns in docs

## Requirements

- **Python 3.7+** for scripts
- **Icarus Verilog** for simulation (via OSS CAD Suite)
- **GTKWave** (optional) for waveform viewing
- **PlatformIO** for hardware tests

## License

MIT License - See project root for details
