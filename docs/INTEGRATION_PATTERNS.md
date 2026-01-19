# Integration Patterns

Guide to integrating tests into Papilio library projects - two approaches with decision criteria.

## Table of Contents
- [Overview](#overview)
- [Decision Guide](#decision-guide)
- [Option A: Standalone Test Project](#option-a-standalone-test-project)
- [Option B: Workspace Integration](#option-b-workspace-integration)
- [Comparison](#comparison)
- [Migration Between Patterns](#migration-between-patterns)
- [Examples](#examples)

---

## Overview

There are two main patterns for organizing library tests:

1. **Standalone Test Project**: Tests are a separate PlatformIO project within the library
2. **Workspace Integration**: Tests are part of the main workspace project

Both patterns work well - choose based on your needs.

---

## Decision Guide

### Choose Option A (Standalone) When:

✅ **Library is reusable** across multiple projects  
✅ **Clean separation** desired between library and tests  
✅ **CI/CD integration** planned (easier with standalone)  
✅ **Library will be published** separately  
✅ **Multiple developers** working on library independently  
✅ **Simple project structure** preferred (each library self-contained)

### Choose Option B (Workspace) When:

✅ **Library is project-specific** (not reused elsewhere)  
✅ **Unified build system** desired (one platformio.ini)  
✅ **Testing with main application** needed (library + app interaction)  
✅ **Development agility** is priority (less configuration overhead)  
✅ **Single workspace** approach preferred  
✅ **Shared test fixtures** across libraries needed

### Still Unsure?

**Default recommendation**: Start with **Option A (Standalone)** - easier to migrate to Option B later if needed.

---

## Option A: Standalone Test Project

### Structure

```
libs/papilio_my_library/
├── library.json              # Library metadata
├── README.md
├── AI_SKILL.md
├── src/                      # Library source code
│   ├── my_library.cpp
│   └── my_library.h
├── gateware/                 # FPGA modules
│   └── my_module.v
├── tests/
│   ├── sim/                  # Simulation tests
│   │   ├── README.md
│   │   ├── run_all_sims.py
│   │   └── tb_my_module.v
│   └── hw/                   # Hardware tests (standalone project)
│       ├── README.md
│       ├── platformio.ini    # ← Standalone test project
│       ├── run_hw_tests.py
│       └── src/
│           └── test_my_library.cpp
└── run_all_tests.py          # Top-level test runner
```

### Hardware Test platformio.ini

```ini
; Hardware tests for papilio_my_library
; This is a standalone test project

[platformio]
default_envs = esp32

[env:esp32]
platform = espressif32
board = esp32dev
framework = arduino

; Test configuration
test_framework = unity
test_build_src = yes

; Library under test (use lib_extra_dirs to reference parent library)
lib_extra_dirs = 
    ../..  ; Points to libs/ directory

; Explicitly include library
lib_deps = 
    papilio_my_library

; Build flags
build_flags = 
    -Wall
    -Wextra

; Upload settings
upload_speed = 921600
monitor_speed = 115200

; Test settings
test_speed = 115200
test_port = /dev/ttyUSB0  ; Adjust for your system
```

### Test Source (test_my_library.cpp)

```cpp
/**
 * Hardware tests for papilio_my_library
 * Standalone test project
 */

#include <Arduino.h>
#include <unity.h>
#include "my_library.h"  // Library under test

// Test setup
void setUp(void) {
    // Initialize before each test
    my_library_init();
}

void tearDown(void) {
    // Cleanup after each test
}

// Test cases
void test_basic_functionality(void) {
    TEST_ASSERT_TRUE(my_library_is_ready());
}

void test_read_write(void) {
    uint8_t write_val = 0x42;
    my_library_write(0, write_val);
    uint8_t read_val = my_library_read(0);
    TEST_ASSERT_EQUAL_HEX8(write_val, read_val);
}

// Test runner
void setup() {
    delay(2000);  // Wait for serial
    
    UNITY_BEGIN();
    RUN_TEST(test_basic_functionality);
    RUN_TEST(test_read_write);
    UNITY_END();
}

void loop() {
    // Tests run once
}
```

### Test Automation (run_hw_tests.py)

```python
#!/usr/bin/env python3
"""
Run hardware tests for papilio_my_library
Standalone test project approach
"""

import sys
import subprocess
import os

def main():
    # Change to test directory
    test_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(test_dir)
    
    print("="*60)
    print("Hardware Tests: papilio_my_library")
    print("="*60)
    
    # Clean previous build
    print("\nCleaning previous build...")
    subprocess.run(["pio", "run", "-t", "clean"], check=False)
    
    # Build and upload tests
    print("\nBuilding and uploading tests...")
    try:
        subprocess.run(["pio", "test", "-e", "esp32"], check=True)
        print("\n✅ Hardware tests PASSED")
        return 0
    except subprocess.CalledProcessError:
        print("\n❌ Hardware tests FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

### Pros and Cons

**Advantages**:
- ✅ Complete isolation - library and tests are independent
- ✅ Own dependencies - test-only libraries don't pollute main project
- ✅ Easy CI integration - straightforward to test library alone
- ✅ Clear structure - obvious what's library vs test
- ✅ Reusable - library can be used in any project without test baggage
- ✅ Parallel development - work on tests without affecting main project

**Disadvantages**:
- ❌ Duplicate configuration - some settings repeated
- ❌ Extra build - separate compilation for tests
- ❌ More overhead - multiple platformio.ini files
- ❌ Path complexity - need `lib_extra_dirs` to reference library

### When It Works Best

- Publishing libraries to PlatformIO registry
- Multiple projects using same library
- Strict separation of concerns needed
- CI/CD pipeline per library
- Library development separate from application

---

## Option B: Workspace Integration

### Structure

```
workspace/
├── platformio.ini              # Single project config
├── src/
│   └── main.cpp               # Main application
├── test/                      # PlatformIO test directory
│   ├── test_papilio_my_library/
│   │   └── test_my_library.cpp
│   └── test_other_module/
│       └── test_other.cpp
└── libs/                      # Local libraries
    └── papilio_my_library/
        ├── library.json
        ├── src/
        │   ├── my_library.cpp
        │   └── my_library.h
        ├── gateware/
        │   └── my_module.v
        └── tests/
            └── sim/           # Simulation tests stay in library
                ├── run_all_sims.py
                └── tb_my_module.v
```

### Workspace platformio.ini

```ini
; Main workspace project with integrated tests

[platformio]
default_envs = esp32
lib_dir = libs  ; Local libraries

[env:esp32]
platform = espressif32
board = esp32dev
framework = arduino

; Test configuration
test_framework = unity
test_build_src = yes  ; Include src/ in test builds

; Libraries (automatically found in libs/)
lib_deps = 
    ; External dependencies here

; Build flags
build_flags = 
    -Wall
    -Wextra

; Upload/monitor settings
upload_speed = 921600
monitor_speed = 115200
test_speed = 115200
```

### Test Source (test/test_papilio_my_library/test_my_library.cpp)

```cpp
/**
 * Hardware tests for papilio_my_library
 * Workspace integration approach
 */

#include <Arduino.h>
#include <unity.h>
#include "my_library.h"  // Found automatically in libs/

void setUp(void) {
    my_library_init();
}

void tearDown(void) {
    // Cleanup
}

void test_basic_functionality(void) {
    TEST_ASSERT_TRUE(my_library_is_ready());
}

void test_read_write(void) {
    uint8_t write_val = 0x42;
    my_library_write(0, write_val);
    uint8_t read_val = my_library_read(0);
    TEST_ASSERT_EQUAL_HEX8(write_val, read_val);
}

void setup() {
    delay(2000);
    UNITY_BEGIN();
    RUN_TEST(test_basic_functionality);
    RUN_TEST(test_read_write);
    UNITY_END();
}

void loop() {}
```

### Test Automation (workspace-level)

Create `run_hw_tests.py` at workspace root:

```python
#!/usr/bin/env python3
"""
Run hardware tests for workspace
Workspace integration approach
"""

import sys
import subprocess
import argparse

def main():
    parser = argparse.ArgumentParser(description="Run workspace hardware tests")
    parser.add_argument("--filter", help="Test name filter", default=None)
    args = parser.parse_args()
    
    print("="*60)
    print("Hardware Tests: Workspace")
    print("="*60)
    
    # Build command
    cmd = ["pio", "test", "-e", "esp32"]
    if args.filter:
        cmd.extend(["--filter", args.filter])
    
    # Run tests
    try:
        subprocess.run(cmd, check=True)
        print("\n✅ Hardware tests PASSED")
        return 0
    except subprocess.CalledProcessError:
        print("\n❌ Hardware tests FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

### Running Tests

```bash
# All hardware tests
pio test -e esp32

# Specific library tests
pio test -e esp32 --filter test_papilio_my_library

# Or use script
python run_hw_tests.py
python run_hw_tests.py --filter test_papilio_my_library
```

### Pros and Cons

**Advantages**:
- ✅ Unified build - single platformio.ini
- ✅ Less configuration - no duplicate settings
- ✅ Easier cross-library testing - test library interactions
- ✅ Simpler paths - libraries auto-discovered in libs/
- ✅ Application context - test library with real application
- ✅ Less overhead - fewer files and directories

**Disadvantages**:
- ❌ Coupling - tests tied to workspace project
- ❌ Mixed concerns - library and application together
- ❌ Harder CI - need to test entire workspace, not just library
- ❌ Less portable - library tests not self-contained
- ❌ Dependency pollution - test dependencies in main project

### When It Works Best

- Project-specific libraries (not reused elsewhere)
- Rapid development with frequent library changes
- Testing library + application integration
- Simple project structure preferred
- Single team working on integrated system

---

## Comparison

| Aspect | Option A: Standalone | Option B: Workspace |
|--------|---------------------|---------------------|
| **Isolation** | Complete | Shared |
| **Configuration** | Duplicate platformio.ini | Single platformio.ini |
| **Build Time** | Separate (slower) | Unified (faster) |
| **CI/CD** | Easy per-library | Workspace-level only |
| **Reusability** | High | Low |
| **Complexity** | Higher (more files) | Lower (fewer files) |
| **Library Publishing** | Easy | Hard |
| **Test Library Interactions** | Difficult | Easy |
| **Dependencies** | Isolated | Shared |
| **Best For** | Reusable libraries | Project-specific code |

---

## Migration Between Patterns

### From Standalone to Workspace

1. **Copy tests** to workspace `test/` directory:
   ```bash
   mkdir -p test/test_my_library
   cp libs/papilio_my_library/tests/hw/src/*.cpp test/test_my_library/
   ```

2. **Update includes** (should work without changes):
   ```cpp
   #include "my_library.h"  // Auto-discovered in libs/
   ```

3. **Remove standalone config**:
   ```bash
   rm libs/papilio_my_library/tests/hw/platformio.ini
   ```

4. **Run tests**:
   ```bash
   pio test -e esp32 --filter test_my_library
   ```

### From Workspace to Standalone

1. **Create test project**:
   ```bash
   mkdir -p libs/papilio_my_library/tests/hw/src
   ```

2. **Copy tests**:
   ```bash
   cp test/test_my_library/*.cpp libs/papilio_my_library/tests/hw/src/
   ```

3. **Create platformio.ini** in `tests/hw/`:
   ```ini
   [platformio]
   default_envs = esp32
   
   [env:esp32]
   platform = espressif32
   board = esp32dev
   framework = arduino
   test_framework = unity
   lib_extra_dirs = ../..
   lib_deps = papilio_my_library
   ```

4. **Create run_hw_tests.py**:
   ```python
   #!/usr/bin/env python3
   import sys
   import subprocess
   import os
   
   os.chdir(os.path.dirname(__file__))
   sys.exit(subprocess.run(["pio", "test", "-e", "esp32"]).returncode)
   ```

5. **Remove workspace tests**:
   ```bash
   rm -rf test/test_my_library
   ```

---

## Examples

### Example 1: Reusable SPI Slave Library (Standalone)

```
libs/papilio_spi_slave/
├── library.json
├── src/
│   ├── spi_slave.cpp
│   └── spi_slave.h
├── gateware/
│   └── spi_slave.v
├── tests/
│   ├── sim/
│   │   ├── run_all_sims.py
│   │   └── tb_spi_slave.v
│   └── hw/                        # ← Standalone test project
│       ├── platformio.ini
│       ├── run_hw_tests.py
│       └── src/
│           ├── test_spi_basic.cpp
│           └── test_spi_burst.cpp
└── run_all_tests.py
```

**Why standalone?**
- Library used in multiple projects
- Will be published to PlatformIO registry
- Needs independent CI/CD testing

### Example 2: Project-Specific Library (Workspace)

```
retrocade_project/
├── platformio.ini                 # ← Single config
├── src/
│   └── main.cpp
├── test/                          # ← All tests here
│   ├── test_video_controller/
│   │   └── test_video.cpp
│   └── test_audio_controller/
│       └── test_audio.cpp
└── libs/
    ├── video_controller/          # Project-specific
    │   ├── library.json
    │   ├── src/
    │   └── tests/sim/             # Only sim tests in library
    └── audio_controller/          # Project-specific
        ├── library.json
        ├── src/
        └── tests/sim/
```

**Why workspace?**
- Libraries are project-specific
- Need to test video + audio interaction
- Rapid development iteration
- Single unified build

### Example 3: Mixed Approach

```
workspace/
├── platformio.ini
├── src/
├── test/                          # Project tests
│   └── test_integration/
└── libs/
    ├── papilio_spi_slave/         # Reusable (standalone tests)
    │   ├── tests/
    │   │   ├── sim/
    │   │   └── hw/                # ← Own platformio.ini
    │   │       ├── platformio.ini
    │   │       └── src/
    └── project_specific_lib/      # Project-specific (workspace tests)
        ├── tests/
        │   └── sim/               # Only sim in library
        └── (hw tests in workspace test/)
```

**Why mixed?**
- Best of both worlds
- Reusable libraries stay independent
- Project-specific code uses workspace integration

---

## Summary

### Quick Decision Matrix

| Your Situation | Recommended Pattern |
|----------------|-------------------|
| Publishing library | Option A (Standalone) |
| Project-specific library | Option B (Workspace) |
| Multiple libraries, testing interactions | Option B (Workspace) |
| Library used across projects | Option A (Standalone) |
| Rapid development, single project | Option B (Workspace) |
| CI/CD per library | Option A (Standalone) |
| Unified build system | Option B (Workspace) |

### Key Takeaways

1. **Both patterns work** - choose based on your needs
2. **Standalone is default** for reusable libraries
3. **Workspace is simpler** for project-specific code
4. **Can mix approaches** in same workspace
5. **Can migrate** between patterns if needs change

### Simulation Tests

**Always in library**: Regardless of pattern choice, keep simulation tests in the library:
```
libs/papilio_xxx/tests/sim/
```

Simulation tests are:
- Fast (no hardware needed)
- Portable (work anywhere)
- Library-specific (test gateware modules)

Only hardware tests differ between patterns!
