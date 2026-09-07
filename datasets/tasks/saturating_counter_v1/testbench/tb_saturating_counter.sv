module tb_saturating_counter;
  localparam integer WIDTH = 3;
  reg clk = 0;
  reg rst = 0;
  reg en = 0;
  reg up = 0;
  wire [WIDTH-1:0] count;
  wire at_min, at_max;
  integer errors = 0;

  saturating_counter #(.WIDTH(WIDTH)) dut (.*);
  always #5 clk = ~clk;

  task step;
    input next_rst, next_en, next_up;
    begin
      @(negedge clk); rst = next_rst; en = next_en; up = next_up;
      @(posedge clk); #1;
    end
  endtask

  task check;
    input condition;
    input [8*32-1:0] obligation;
    begin
      if (!condition) begin errors = errors + 1; $display("OBLIGATION_FAIL:%0s", obligation); end
    end
  endtask

  integer i;
  initial begin
    $dumpfile("saturating_counter.vcd"); $dumpvars(0, tb_saturating_counter);
    step(1, 1, 1); check(count == 0, "O_RESET"); check(at_min && !at_max, "O_FLAGS");
    step(0, 1, 0); check(count == 0, "O_SATURATE_MIN");
    step(0, 0, 1); check(count == 0, "O_HOLD");
    for (i = 1; i <= 7; i = i + 1) begin
      step(0, 1, 1); check(count == i[WIDTH-1:0], "O_INCREMENT");
    end
    check(at_max && !at_min, "O_FLAGS");
    step(0, 1, 1); check(count == 7, "O_SATURATE_MAX");
    step(0, 1, 0); check(count == 6, "O_DECREMENT");
    step(0, 0, 0); check(count == 6, "O_HOLD");
    if (errors == 0) begin $display("RTLREASON_RESULT:PASS"); $finish; end
    $fatal(1, "RTLREASON_RESULT:FAIL errors=%0d", errors);
  end
endmodule
