module stream_width_adapter(input wire clk,input wire rst,input wire in_valid,output wire in_ready,input wire [7:0] in_data,output reg out_valid,input wire out_ready,output reg [15:0] out_data);
  reg have_low;reg [7:0] low_byte;
  assign in_ready=!out_valid;
  always @(posedge clk) begin
    if(rst)begin have_low<=0;low_byte<=0;out_valid<=0;out_data<=0;end
    else if(out_valid)begin if(out_ready)out_valid<=0;end
    else if(in_valid)begin
      if(!have_low)begin low_byte<=in_data;have_low<=1;end
      else begin out_data<={in_data,low_byte};out_valid<=1;have_low<=0;end
    end
  end
endmodule
