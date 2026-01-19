`timescale 1ns / 1ps

/**
 * Example testbench for Papilio Dev Tools
 * 
 * This is a minimal working example showing testbench structure.
 * Use this as a template for your own testbenches.
 */

module tb_example;
    // Signals
    reg clk = 0;
    reg rst = 1;
    reg [7:0] counter = 0;
    
    // Clock generation (50MHz = 20ns period)
    initial begin
        clk = 0;
        forever #10 clk = ~clk;
    end
    
    // Simple counter logic (the "DUT" for this example)
    always @(posedge clk or posedge rst) begin
        if (rst)
            counter <= 0;
        else
            counter <= counter + 1;
    end
    
    // Test sequence
    initial begin
        // VCD dump for waveform analysis
        $dumpfile("tb_example.vcd");
        $dumpvars(0, tb_example);
        
        $display("=== Example Testbench Start ===");
        
        // Test 1: Reset
        $display("Test 1: Reset");
        rst = 1;
        #100;  // Hold reset for 100ns
        
        if (counter != 0) begin
            $error("Counter should be 0 during reset!");
            $finish;
        end
        
        $display("  PASS: Counter held at 0 during reset");
        
        // Test 2: Counting
        $display("Test 2: Counting");
        rst = 0;
        #50;  // Wait after reset
        
        if (counter == 0) begin
            $error("Counter should start incrementing!");
            $finish;
        end
        
        $display("  PASS: Counter started incrementing");
        
        // Test 3: Count to 10
        $display("Test 3: Wait for counter to reach 10");
        
        while (counter < 10) begin
            @(posedge clk);
        end
        
        $display("  PASS: Counter reached 10 at time %0t", $time);
        
        // Test complete
        $display("=== All Tests Passed ===");
        $finish;
    end
    
    // Timeout protection (1us)
    initial begin
        #1000000;
        $error("Test timeout!");
        $finish;
    end
    
    // Optional: Monitor counter value
    always @(posedge clk) begin
        if (!rst && counter < 15) begin
            $display("  Time %0t: counter = %d", $time, counter);
        end
    end

endmodule
