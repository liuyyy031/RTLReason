module tb_serial_parity;
  reg clk = 0, rst = 0, start = 0, bit_valid = 0, bit_in = 0, finish = 0;
  wire busy, parity, done;
  integer errors = 0;
  serial_parity dut (.*);
  always #5 clk = ~clk;

  task step;
    input ns, nv, nb, nf;
    begin
      @(negedge clk); start = ns; bit_valid = nv; bit_in = nb; finish = nf;
      @(posedge clk); #1;
    end
  endtask
  task check;
    input condition; input [8*32-1:0] obligation;
    begin if (!condition) begin errors = errors + 1; $display("OBLIGATION_FAIL:%0s", obligation); end end
  endtask

  initial begin
    $dumpfile("serial_parity.vcd"); $dumpvars(0, tb_serial_parity);
    @(negedge clk); rst = 1; start = 1; bit_valid = 1; bit_in = 1; finish = 1;
    @(posedge clk); #1; rst = 0;
    check(!busy && !parity && !done, "O_RESET");
    step(0, 1, 1, 1); check(!busy && !done && !parity, "O_GATING");
    step(1, 1, 1, 0); check(busy, "O_START");
    step(1, 1, 0, 0); check(busy, "O_GATING");
    step(0, 1, 1, 0); check(busy, "O_ACCUMULATE");
    step(0, 1, 1, 1); check(!busy && done && parity, "O_FINAL_BIT"); check(done, "O_DONE");
    step(0, 0, 0, 0); check(!done && parity, "O_RESULT_HOLD");
    step(1, 0, 0, 0); check(busy, "O_START");
    step(0, 0, 0, 1); check(!busy && done && !parity, "O_DONE");
    if (errors == 0) begin $display("RTLREASON_RESULT:PASS"); $finish; end
    $fatal(1, "RTLREASON_RESULT:FAIL errors=%0d", errors);
  end
endmodule
