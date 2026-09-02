module tb_request_ack_timeout;
  localparam integer TIMEOUT_CYCLES = 3;
  reg clk = 0;
  reg rst = 0;
  reg req = 0;
  reg ack = 0;
  wire busy, done, timeout;
  integer errors = 0;
  request_ack_timeout #(.TIMEOUT_CYCLES(TIMEOUT_CYCLES)) dut (.*);
  always #5 clk = ~clk;

  task step;
    input next_rst;
    input next_req;
    input next_ack;
    begin
      @(negedge clk); rst = next_rst; req = next_req; ack = next_ack;
      @(posedge clk); #1;
    end
  endtask

  task check;
    input condition;
    input [8*40-1:0] obligation;
    begin
      if (!condition) begin
        errors = errors + 1;
        $display("OBLIGATION_FAIL:%0s", obligation);
      end
    end
  endtask

  initial begin
    $dumpfile("request_ack_timeout.vcd");
    $dumpvars(0, tb_request_ack_timeout);
    step(1, 1, 1);
    check(!busy && !done && !timeout, "O_RESET");

    step(0, 1, 1);
    check(busy && !done && !timeout, "O_INITIAL_ACK_IGNORED");
    step(0, 0, 1);
    check(!busy && done && !timeout, "O_ACK_COMPLETE");
    step(0, 0, 0);
    check(!done && !timeout, "O_PULSES");

    step(0, 1, 0);
    check(busy, "O_REQUEST_ACCEPT");
    step(0, 1, 0);
    check(busy && !timeout, "O_BUSY_REQUEST_IGNORED");
    check(!done && !timeout, "O_TIMEOUT_EXACT");
    step(0, 0, 0);
    check(busy && !timeout, "O_TIMEOUT_EXACT");
    step(0, 0, 0);
    check(!busy && timeout && !done, "O_TIMEOUT_EXACT");
    step(0, 0, 0);
    check(!timeout, "O_PULSES");

    step(0, 1, 0);
    step(0, 0, 0);
    step(0, 0, 0);
    step(0, 1, 1);
    check(!busy && done && !timeout, "O_ACK_PRIORITY");
    check(!busy, "O_BUSY_REQUEST_IGNORED");
    step(0, 1, 0);
    check(busy && !done && !timeout, "O_REQUEST_ACCEPT");

    if (errors == 0) begin
      $display("RTLREASON_RESULT:PASS");
      $finish;
    end
    $fatal(1, "RTLREASON_RESULT:FAIL errors=%0d", errors);
  end
endmodule
