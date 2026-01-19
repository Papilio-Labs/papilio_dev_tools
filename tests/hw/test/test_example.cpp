/**
 * Example hardware test for Papilio Dev Tools
 * 
 * This is a minimal working example showing hardware test structure.
 * Use this as a template for your own hardware tests.
 * 
 * Tests use the Unity test framework included with PlatformIO.
 */

#include <Arduino.h>
#include <unity.h>

// Test setup (called before each test)
void setUp(void) {
    // Initialize hardware, reset state, etc.
}

// Test teardown (called after each test)
void tearDown(void) {
    // Cleanup, restore state, etc.
}

// Example test: Basic functionality
void test_basic_operation(void) {
    // This is a simple example test
    int expected = 42;
    int actual = 42;
    
    TEST_ASSERT_EQUAL(expected, actual);
}

// Example test: LED blink timing
void test_led_timing(void) {
    // Define LED pin (LED_BUILTIN may not be available on all boards)
    const int LED_PIN = 2;  // GPIO2 on ESP32
    
    // Turn on LED
    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, HIGH);
    
    // Measure timing
    unsigned long start = micros();
    delay(100);  // 100ms delay
    unsigned long duration = micros() - start;
    
    // Verify timing (allow 10% tolerance)
    TEST_ASSERT_GREATER_THAN(90000, duration);   // > 90ms
    TEST_ASSERT_LESS_THAN(110000, duration);     // < 110ms
    
    // Turn off LED
    digitalWrite(LED_PIN, LOW);
}

// Example test: Serial communication
void test_serial_ready(void) {
    // Verify Serial is initialized
    TEST_ASSERT_TRUE(Serial);
    
    // Verify baud rate (platform specific)
    #ifdef ESP32
    // ESP32 Serial is ready if object exists
    TEST_ASSERT_TRUE(Serial);
    #endif
}

// Example test: Hex values
void test_hex_values(void) {
    uint8_t expected = 0xAA;
    uint8_t actual = 0xAA;
    
    TEST_ASSERT_EQUAL_HEX8(expected, actual);
}

// Example test: Array comparison
void test_array_comparison(void) {
    uint8_t expected[] = {0x01, 0x02, 0x03, 0x04};
    uint8_t actual[] = {0x01, 0x02, 0x03, 0x04};
    
    TEST_ASSERT_EQUAL_HEX8_ARRAY(expected, actual, 4);
}

// Example test: Failure case (commented out to prevent test failures)
/*
void test_intentional_failure(void) {
    // This test will fail intentionally
    TEST_ASSERT_EQUAL(1, 2);
}
*/

// Main setup function
void setup() {
    // Wait for Serial (important for debugging)
    delay(2000);
    
    // Initialize Serial
    Serial.begin(115200);
    Serial.println("Starting tests...");
    
    // Start Unity test framework
    UNITY_BEGIN();
    
    // Run tests
    RUN_TEST(test_basic_operation);
    RUN_TEST(test_led_timing);
    RUN_TEST(test_serial_ready);
    RUN_TEST(test_hex_values);
    RUN_TEST(test_array_comparison);
    // RUN_TEST(test_intentional_failure);  // Uncomment to see failure
    
    // Finish Unity test framework
    UNITY_END();
    
    Serial.println("Tests complete!");
}

// Main loop (tests run once in setup)
void loop() {
    // Nothing to do here - tests run in setup()
}
