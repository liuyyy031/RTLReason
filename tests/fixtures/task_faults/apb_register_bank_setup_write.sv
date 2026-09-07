module apb_register_bank(input wire clk,input wire rst,input wire psel,input wire penable,input wire pwrite,input wire[3:0]paddr,input wire[31:0]pwdata,output wire pready,output reg[31:0]prdata,output wire pslverr);
  reg[31:0]reg0,reg1;wire access=psel&&penable;wire valid_addr=paddr==0||paddr==4;assign pready=1;assign pslverr=access&&!valid_addr;always@*if(paddr==0)prdata=reg0;else if(paddr==4)prdata=reg1;else prdata=0;
  always@(posedge clk)if(rst)begin reg0<=0;reg1<=0;end else if(psel&&pwrite)begin if(paddr==0)reg0<=pwdata;else if(paddr==4)reg1<=pwdata;end
endmodule
