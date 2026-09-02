module tb_token_bucket;
  localparam integer CAPACITY = 3;
  reg clk = 0;
  reg rst = 0;
  reg req = 0;
  wire grant;
  wire [$clog2(CAPACITY+1)-1:0] tokens;
  integer errors = 0;
  token_bucket #(.CAPACITY(CAPACITY)) dut (.*);
  always #5 clk = ~clk;

  task step;
    input next_rst;
    input next_req;
    input integer expected_tokens;
    input expected_grant;
    input [8*32-1:0] obligation;
    begin
      @(negedge clk); rst = next_rst; req = next_req;
      @(posedge clk); #1;
      if (tokens !== expected_tokens || grant !== expected_grant) begin
        errors = errors + 1;
        $display("OBLIGATION_FAIL:%0s", obligation);
      end
      if (tokens > CAPACITY) begin
        errors = errors + 1;
        $display("OBLIGATION_FAIL:O_RANGE");
      end
    end
  endtask

  initial begin
    $dumpfile("token_bucket.vcd");
    $dumpvars(0, tb_token_bucket);

    step(1, 1, 0, 0, "O_RESET");

    // Empty request cannot use the token added on the same edge.
    step(0, 1, 1, 0, "O_EMPTY_NO_LOOKAHEAD");
    step(0, 0, 2, 0, "O_REPLENISH");

    // Middle occupancy accepts add and consume together.
    step(0, 1, 2, 1, "O_MIDDLE_SIMULTANEOUS");
    step(0, 0, 3, 0, "O_GRANT_PULSE");

    // Full occupancy blocks add, so a request decreases the count.
    step(0, 1, 2, 1, "O_FULL_CONSUME");
    step(0, 1, 2, 1, "O_MIDDLE_SIMULTANEOUS");
    step(0, 0, 3, 0, "O_REPLENISH");
    step(0, 0, 3, 0, "O_RANGE");

    step(1, 1, 0, 0, "O_RESET");
    step(0, 0, 1, 0, "O_REPLENISH");

    if (errors == 0) begin
      $display("RTLREASON_RESULT:PASS");
      $finish;
    end
    $fatal(1, "RTLREASON_RESULT:FAIL errors=%0d", errors);
  end
endmodule
