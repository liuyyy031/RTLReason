module tb_multicycle_multiply_ctrl;localparam WIDTH=4;reg clk=0,rst=1,start=0;reg[WIDTH-1:0]a=0,b=0;wire busy,done;wire[2*WIDTH-1:0]result;wire min_busy,min_done;wire[1:0]min_result;integer errors=0,i;always#5 clk=~clk;multicycle_multiply_ctrl #(.WIDTH(WIDTH))dut(.*);multicycle_multiply_ctrl #(.WIDTH(1))dut_min(.clk(clk),.rst(rst),.start(start),.a(a[0]),.b(b[0]),.busy(min_busy),.done(min_done),.result(min_result));
 task check;input c;input[8*32-1:0]o;begin if(!c)begin errors=errors+1;$display("OBLIGATION_FAIL:%0s",o);end end endtask
 initial begin $dumpfile("multicycle_multiply_ctrl.vcd");$dumpvars(0,tb_multicycle_multiply_ctrl);repeat(2)@(posedge clk);rst=0;@(negedge clk);a=3;b=5;start=1;@(posedge clk);#1;start=0;check(busy&&!done&&result==0,"O_ACCEPT");
  for(i=0;i<WIDTH-1;i=i+1)begin @(posedge clk);#1;check(busy&&!done&&result==0,"O_RESULT_STABLE");if(i==0)begin check(!min_busy&&min_done&&min_result==1,"O_WIDTH_ONE");a=15;b=15;start=1;end else start=0;end
  @(posedge clk);#1;check(!busy&&done&&result==15,"O_ATOMIC_COMMIT");@(posedge clk);#1;check(!done&&result==15,"O_DONE_PULSE");
  @(negedge clk);a=0;b=9;start=1;@(posedge clk);#1;start=0;repeat(WIDTH)@(posedge clk);#1;check(done&&result==0,"O_ITERATION_COUNT");
  rst=1;@(posedge clk);#1;check(!busy&&!done&&result==0,"O_RESET");if(errors==0)begin $display("RTLREASON_RESULT:PASS");$finish;end $fatal(1,"RTLREASON_RESULT:FAIL errors=%0d",errors);end
endmodule
