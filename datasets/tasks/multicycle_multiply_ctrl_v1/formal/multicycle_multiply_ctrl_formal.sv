module multicycle_multiply_ctrl_formal;
 localparam WIDTH=4;reg clk=0;always@($global_clock)clk<=!clk;reg rst=1;(*anyseq*)reg start;(*anyseq*)reg[WIDTH-1:0]a,b;wire busy,done;wire[2*WIDTH-1:0]result;
 reg model_busy=0,model_done=0,past_valid=0;reg[2:0]remaining=0;reg[WIDTH-1:0]captured_a=0,captured_b=0;reg[2*WIDTH-1:0]model_result=0;
 multicycle_multiply_ctrl #(.WIDTH(WIDTH))dut(.*);
 always@(posedge clk)begin
  past_valid<=1;rst<=0;
  if(past_valid)begin assert(busy==model_busy);assert(done==model_done);assert(result==model_result);assert(!(done&&busy));assert(!(done&&$past(done)));end
  if(rst)begin model_busy<=0;model_done<=0;model_result<=0;remaining<=0;captured_a<=0;captured_b<=0;end
  else begin model_done<=0;if(!model_busy)begin if(start)begin model_busy<=1;remaining<=WIDTH;captured_a<=a;captured_b<=b;end end
  else if(remaining==1)begin model_result<=captured_a*captured_b;model_busy<=0;model_done<=1;remaining<=0;end else remaining<=remaining-1'b1;end
 end
endmodule
