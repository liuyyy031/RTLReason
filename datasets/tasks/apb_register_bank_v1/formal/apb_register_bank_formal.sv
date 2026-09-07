module apb_register_bank_formal;
  reg clk=0;always @($global_clock)clk<=!clk;reg rst=1;(* anyseq *)reg psel,penable,pwrite;(* anyseq *)reg[3:0]paddr;(* anyseq *)reg[31:0]pwdata;wire pready;wire[31:0]prdata;wire pslverr;apb_register_bank dut(.*);
  reg past_valid=0;reg[31:0]model0=0,model1=0;
  always @(posedge clk)begin
    past_valid<=1;rst<=0;
    if(past_valid)begin assert(pready);assert(pslverr==((psel&&penable)&&!(paddr==0||paddr==4)));if(paddr==0)assert(prdata==model0);else if(paddr==4)assert(prdata==model1);else assert(prdata==0);end
    if(rst)begin model0<=0;model1<=0;end else if(psel&&penable&&pwrite)begin if(paddr==0)model0<=pwdata;else if(paddr==4)model1<=pwdata;end
  end
endmodule
