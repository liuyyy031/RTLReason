module spi_tx #(parameter integer HALF_PERIOD_CYCLES=2)(
 input wire clk,input wire rst,input wire start,input wire [7:0] data_in,
 output reg sclk,output reg mosi,output reg busy,output reg done);
 reg [7:0] word; reg [2:0] bit_index; integer half_count;
 always @(posedge clk) begin
  if(rst)begin sclk<=0;mosi<=0;busy<=0;done<=0;word<=0;bit_index<=0;half_count<=0;end
  else begin done<=0;
   if(start)begin word<=data_in;bit_index<=0;half_count<=0;sclk<=0;mosi<=data_in[7];busy<=1;end
   else if(busy)begin
    if(half_count==HALF_PERIOD_CYCLES-1)begin half_count<=0;
     if(!sclk)sclk<=1;else begin sclk<=0;
      if(bit_index==7)begin busy<=0;mosi<=0;done<=1;end
      else begin bit_index<=bit_index+1'b1;word<={word[6:0],1'b0};mosi<=word[6];end
     end
    end else half_count<=half_count+1;
   end else begin sclk<=0;mosi<=0;end
  end
 end
endmodule
