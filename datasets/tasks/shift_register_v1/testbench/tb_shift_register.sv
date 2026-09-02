module tb_shift_register;
  localparam integer WIDTH = 4;
  reg clk = 0;
  reg rst = 0;
  reg en = 0;
  reg serial_in = 0;
  wire [WIDTH-1:0] q;
  wire serial_out;
  integer errors = 0;

  shift_register #(.WIDTH(WIDTH)) dut (.*);
  always #5 clk = ~clk;

  task step;
    input next_rst;
    input next_en;
    input next_bit;
    begin
      @(negedge clk);
      rst = next_rst; en = next_en; serial_in = next_bit;
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
    $dumpfile("shift_register.vcd");
    $dumpvars(0, tb_shift_register);
    step(1, 1, 1);
    check(q == 0, "O_RESET");
    check(q == 0, "O_PRIORITY");

    step(0, 1, 1); check(q == 4'b0001, "O_SHIFT");
    step(0, 1, 0); check(q == 4'b0010, "O_DIRECTION");
    step(0, 1, 1); check(q == 4'b0101, "O_SHIFT");
    step(0, 1, 1); check(q == 4'b1011, "O_DIRECTION");
    check(serial_out == 1, "O_SERIAL_OUT");
    step(0, 0, 0);
    check(q == 4'b1011, "O_HOLD");
    check(serial_out == q[3], "O_SERIAL_OUT");

    if (errors == 0) begin
      $display("RTLREASON_RESULT:PASS");
      $finish;
    end
    $fatal(1, "RTLREASON_RESULT:FAIL errors=%0d", errors);
  end
endmodule
