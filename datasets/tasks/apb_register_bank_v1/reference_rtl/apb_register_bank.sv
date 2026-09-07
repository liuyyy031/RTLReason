module apb_register_bank(input wire clk,input wire rst,input wire psel,input wire penable,input wire pwrite,input wire[3:0]paddr,input wire[31:0]pwdata,output wire pready,output reg[31:0]prdata,output wire pslverr);
  reg[31:0]reg0,reg1;wire access=psel&&penable;wire valid_addr=(paddr==4'h0)||(paddr==4'h4);
  assign pready=1'b1;assign pslverr=access&&!valid_addr;
  always @* begin if(paddr==4'h0)prdata=reg0;else if(paddr==4'h4)prdata=reg1;else prdata=32'h0;end
  always @(posedge clk)begin
    if(rst)begin reg0<=0;reg1<=0;end
    else if(access&&pwrite)begin if(paddr==4'h0)reg0<=pwdata;else if(paddr==4'h4)reg1<=pwdata;end
  end
endmodule
