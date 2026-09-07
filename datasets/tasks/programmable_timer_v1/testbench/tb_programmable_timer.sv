module tb_programmable_timer;
  localparam integer WIDTH = 4;
  reg clk = 0, rst = 0, load = 0, enable = 0;
  reg [WIDTH-1:0] period = 0;
  wire [WIDTH-1:0] remaining;
  wire tick;
  integer errors = 0;
  programmable_timer #(.WIDTH(WIDTH)) dut (.*);
  always #5 clk = ~clk;
  task step;
    input nr, nl, ne; input [WIDTH-1:0] np;
    begin @(negedge clk); rst=nr; load=nl; enable=ne; period=np; @(posedge clk); #1; end
  endtask
  task check;
    input condition; input [8*32-1:0] obligation;
    begin if (!condition) begin errors=errors+1; $display("OBLIGATION_FAIL:%0s", obligation); end end
  endtask
  initial begin
    $dumpfile("programmable_timer.vcd"); $dumpvars(0, tb_programmable_timer);
    step(1,1,1,4); check(remaining==1 && !tick,"O_RESET"); check(remaining==1,"O_PRIORITY");
    step(0,1,1,3); check(remaining==3 && !tick,"O_LOAD"); check(remaining==3,"O_PRIORITY");
    step(0,0,1,0); check(remaining==2 && !tick,"O_COUNTDOWN");
    step(0,0,0,0); check(remaining==2 && !tick,"O_HOLD");
    step(0,0,1,0); check(remaining==1 && !tick,"O_COUNTDOWN");
    step(0,0,1,0); check(remaining==3 && tick,"O_EXPIRY");
    step(0,0,0,0); check(remaining==3 && !tick,"O_HOLD");
    step(0,1,0,0); check(remaining==1 && !tick,"O_ZERO_CLAMP");
    step(0,0,1,0); check(remaining==1 && tick,"O_EXPIRY");
    if(errors==0) begin $display("RTLREASON_RESULT:PASS"); $finish; end
    $fatal(1,"RTLREASON_RESULT:FAIL errors=%0d",errors);
  end
endmodule
