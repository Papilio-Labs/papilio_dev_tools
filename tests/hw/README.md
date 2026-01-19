# Hardware Tests

Example hardware test structure for Papilio libraries.

## Contents

- `platformio.ini` - Standalone test project configuration
- `src/test_example.cpp` - Example hardware test
- `run_hw_tests.py` - Automated test runner

## Running Tests

```bash
# Run hardware tests
python run_hw_tests.py

# Or use PlatformIO directly
pio test -e esp32

# Or use library-level runner
python ../../run_all_tests.py --hw-only
```

## Test Structure

This is a **standalone test project** (Option A from INTEGRATION_PATTERNS.md):
- Complete isolation from main project
- Own dependencies
- Easy CI integration
- Self-contained testing

### Alternative: Workspace Integration

See [../../docs/INTEGRATION_PATTERNS.md](../../docs/INTEGRATION_PATTERNS.md) for Option B (workspace integration pattern).

## Writing New Tests

Create test files in `src/test_*.cpp`:

```cpp
#include <Arduino.h>
#include <unity.h>

void setUp(void) {
    // Setup before each test
}

void tearDown(void) {
    // Cleanup after each test
}

void test_function_name(void) {
    TEST_ASSERT_TRUE(condition);
    TEST_ASSERT_EQUAL(expected, actual);
}

void setup() {
    delay(2000);  // Wait for serial
    
    UNITY_BEGIN();
    RUN_TEST(test_function_name);
    UNITY_END();
}

void loop() {
    // Tests run once
}
```

## Unity Assertions

Common assertions:
- `TEST_ASSERT_TRUE(condition)`
- `TEST_ASSERT_FALSE(condition)`
- `TEST_ASSERT_EQUAL(expected, actual)`
- `TEST_ASSERT_EQUAL_HEX8(expected, actual)`
- `TEST_ASSERT_EQUAL_HEX8_ARRAY(expected, actual, count)`
- `TEST_ASSERT_LESS_THAN(threshold, actual)`
- `TEST_ASSERT_GREATER_THAN(threshold, actual)`

## See Also

- [../../AI_SKILL.md](../../AI_SKILL.md) - Hardware testing workflows
- [../../docs/TESTING_GUIDE.md](../../docs/TESTING_GUIDE.md) - Testing best practices
- [../../docs/INTEGRATION_PATTERNS.md](../../docs/INTEGRATION_PATTERNS.md) - Integration patterns
