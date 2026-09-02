module tb_round_robin_arbiter;
  reg clk = 0;
  reg rst = 0;
  reg [3:0] req = 0;
  wire [3:0] grant;
  integer errors = 0;
  round_robin_arbiter dut (.*);
  always #5 clk = ~clk;

  task step;
    input next_rst;
    input [3:0] next_req;
    begin
      @(negedge clk); rst = next_rst; req = next_req;
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
    $dumpfile("round_robin_arbiter.vcd");
    $dumpvars(0, tb_round_robin_arbiter);
    step(1, 4'b1111);
    check(grant == 0, "O_RESET");
    step(0, 4'b1010);
    check(grant == 4'b0010, "O_PRIORITY");
    check($onehot0(grant), "O_ONEHOT");
    check((grant & 4'b1010) == grant, "O_REQUESTED");
    step(0, 4'b1010);
    check(grant == 4'b1000, "O_ROTATE");
    step(0, 4'b0000);
    check(grant == 0, "O_IDLE");
    step(0, 4'b0101);
    check(grant == 4'b0001, "O_PRIORITY");
    step(0, 4'b0101);
    check(grant == 4'b0100, "O_ROTATE");

    if (errors == 0) begin
      $display("RTLREASON_RESULT:PASS");
      $finish;
    end
    $fatal(1, "RTLREASON_RESULT:FAIL errors=%0d", errors);
  end
endmodule
