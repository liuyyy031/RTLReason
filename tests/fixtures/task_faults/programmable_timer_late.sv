module programmable_timer #(
  parameter integer WIDTH=8
)(input wire clk,input wire rst,input wire load,input wire [WIDTH-1:0] period,input wire enable,
   output reg [WIDTH-1:0] remaining,output reg tick);
  reg [WIDTH-1:0] stored_period;
  wire [WIDTH-1:0] effective = period==0 ? 1 : period;
  always @(posedge clk) begin
    if(rst) begin stored_period<=1; remaining<=1; tick<=0; end
    else if(load) begin stored_period<=effective; remaining<=effective; tick<=0; end
    else if(enable) begin
      if(remaining==0) begin remaining<=stored_period; tick<=1; end
      else begin remaining<=remaining-1'b1; tick<=0; end
    end else tick<=0;
  end
endmodule
