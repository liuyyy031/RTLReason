module tb_counter_enable;
  localparam integer WIDTH = 4;
  reg clk = 0;
  reg rst = 0;
  reg en = 0;
  reg load = 0;
  reg [WIDTH-1:0] load_value = 0;
  wire [WIDTH-1:0] count;
  wire overflow;
  integer errors = 0;

  counter_enable #(.WIDTH(WIDTH)) dut (.*);
  always #5 clk = ~clk;

  task step;
    input next_rst;
    input next_load;
    input next_en;
    input [WIDTH-1:0] next_value;
    begin
      @(negedge clk);
      rst = next_rst; load = next_load; en = next_en; load_value = next_value;
      @(posedge clk); #1;
    end
  endtask

  task check;
    input condition;
    input [8*32-1:0] obligation;
    begin
      if (!condition) begin
        errors = errors + 1;
        $display("OBLIGATION_FAIL:%0s", obligation);
      end
    end
  endtask

  initial begin
    $dumpfile("counter_enable.vcd");
    $dumpvars(0, tb_counter_enable);

    step(1, 1, 1, 4'hA);
    check(count == 0 && overflow == 0, "O_RESET");
    check(count == 0, "O_PRIORITY");

    step(0, 1, 1, 4'hE);
    check(count == 4'hE && overflow == 0, "O_LOAD");
    check(count == 4'hE, "O_PRIORITY");

    step(0, 0, 1, 0);
    check(count == 4'hF && overflow == 0, "O_INCREMENT");
    step(0, 0, 1, 0);
    check(count == 0 && overflow == 1, "O_OVERFLOW");
    step(0, 0, 0, 0);
    check(count == 0 && overflow == 0, "O_HOLD");
    check(overflow == 0, "O_OVERFLOW");

    if (errors == 0) begin
      $display("RTLREASON_RESULT:PASS");
      $finish;
    end
    $fatal(1, "RTLREASON_RESULT:FAIL errors=%0d", errors);
  end
endmodule
