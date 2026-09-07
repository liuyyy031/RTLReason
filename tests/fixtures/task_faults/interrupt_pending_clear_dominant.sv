module interrupt_pending(input wire clk,input wire rst,input wire [3:0] irq,input wire [3:0] mask,input wire ack,output reg [3:0] pending,output wire valid,output reg [1:0] index);
  reg [3:0] selected;assign valid=|pending;always @* begin index=0;selected=0;if(pending[0])begin index=0;selected=1;end else if(pending[1])begin index=1;selected=2;end else if(pending[2])begin index=2;selected=4;end else if(pending[3])begin index=3;selected=8;end end
  always @(posedge clk)if(rst)pending<=0;else pending<=(pending|(irq&~mask))&~(ack?selected:0);
endmodule
