module stream_width_adapter_formal;
  reg clk=0;always @($global_clock)clk<=!clk;reg rst=1;(* anyseq *)reg in_valid,out_ready;(* anyseq *)reg[7:0]in_data;wire in_ready,out_valid;wire[15:0]out_data;stream_width_adapter dut(.*);
  reg past_valid=0,model_have_low=0,model_out_valid=0;reg[7:0]model_low=0;reg[15:0]model_out_data=0;
  always @(posedge clk)begin
    past_valid<=1;rst<=0;if(past_valid)begin assert(in_ready==!out_valid);assert(out_valid==model_out_valid);assert(out_data==model_out_data);end
    if(rst)begin model_have_low<=0;model_low<=0;model_out_valid<=0;model_out_data<=0;end
    else if(model_out_valid)begin if(out_ready)model_out_valid<=0;end
    else if(in_valid)begin if(!model_have_low)begin model_low<=in_data;model_have_low<=1;end else begin model_out_data<={in_data,model_low};model_out_valid<=1;model_have_low<=0;end end
  end
endmodule
