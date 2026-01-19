`timescale 1ns / 1ps

module tb_simple;
    reg clk = 0;
    
    initial begin
        $display("Simple test");
        #100;
        $finish;
    end
endmodule
