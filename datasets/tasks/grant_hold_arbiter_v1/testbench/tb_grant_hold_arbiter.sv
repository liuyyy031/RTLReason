module tb_grant_hold_arbiter;
  reg clk = 0;
  reg rst = 0;
  reg [3:0] req = 0;
  reg accept = 0;
  wire [3:0] grant;
  integer errors = 0;
  grant_hold_arbiter dut (.*);
  always #5 clk = ~clk;

  task step;
    input next_rst;
    input [3:0] next_req;
    input next_accept;
    input [3:0] expected_grant;
    input [8*32-1:0] obligation;
    begin
      @(negedge clk); rst = next_rst; req = next_req; accept = next_accept;
      @(posedge clk); #1;
      if (grant !== expected_grant) begin
        errors = errors + 1;
        $display("OBLIGATION_FAIL:%0s", obligation);
      end
      if (grant != 0 && (grant & (grant - 1'b1)) != 0) begin
        errors = errors + 1;
        $display("OBLIGATION_FAIL:O_ONEHOT");
      end
    end
  endtask

  initial begin
    $dumpfile("grant_hold_arbiter.vcd");
    $dumpvars(0, tb_grant_hold_arbiter);

    step(1, 4'b1111, 1, 4'b0000, "O_RESET");
    step(0, 4'b1010, 0, 4'b0010, "O_PRIORITY");

    // Grant remains stable even when the winner withdraws.
    step(0, 4'b0001, 0, 4'b0010, "O_HOLD");
    step(0, 4'b1000, 0, 4'b0010, "O_HOLD");

    // Completion clears only; request 3 is selected one edge later.
    step(0, 4'b1000, 1, 4'b0000, "O_NO_REPLACE");
    step(0, 4'b1000, 0, 4'b1000, "O_IDLE_SELECT");
    step(0, 4'b0000, 1, 4'b0000, "O_ACCEPT_CLEAR");

    // Idle accept does not block selection, and priority is lowest index.
    step(0, 4'b1101, 1, 4'b0001, "O_IDLE_ACCEPT");
    step(0, 4'b0000, 0, 4'b0001, "O_HOLD");
    step(0, 4'b0000, 1, 4'b0000, "O_ACCEPT_CLEAR");
    step(0, 4'b0000, 0, 4'b0000, "O_IDLE_SELECT");

    if (errors == 0) begin
      $display("RTLREASON_RESULT:PASS");
      $finish;
    end
    $fatal(1, "RTLREASON_RESULT:FAIL errors=%0d", errors);
  end
endmodule
