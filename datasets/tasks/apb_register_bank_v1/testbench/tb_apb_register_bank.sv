module tb_apb_register_bank;
  reg clk=0,rst=0,psel=0,penable=0,pwrite=0;reg[3:0]paddr=0;reg[31:0]pwdata=0;wire pready;wire[31:0]prdata;wire pslverr;integer errors=0;
  apb_register_bank dut(.*);always #5 clk=~clk;
  task step;input nr,ns,ne,nw;input[3:0]na;input[31:0]nd;begin @(negedge clk);rst=nr;psel=ns;penable=ne;pwrite=nw;paddr=na;pwdata=nd;#1;if(!pready)begin errors=errors+1;$display("OBLIGATION_FAIL:O_READY");end @(posedge clk);#1;end endtask
  task check;input condition;input[8*32-1:0]obligation;begin if(!condition)begin errors=errors+1;$display("OBLIGATION_FAIL:%0s",obligation);end end endtask
  initial begin
    $dumpfile("apb_register_bank.vcd");$dumpvars(0,tb_apb_register_bank);
    step(1,1,1,1,0,32'hdeadbeef);check(prdata==0,"O_RESET");
    step(0,1,0,1,0,32'h11112222);check(prdata==0,"O_ACCESS_PHASE");check(!pslverr,"O_ERROR_GATING");
    step(0,1,1,1,0,32'h11112222);check(prdata==32'h11112222,"O_WRITE_DECODE");
    step(0,1,1,1,4,32'h33334444);check(prdata==32'h33334444,"O_WRITE_DECODE");
    step(0,1,1,0,0,0);check(prdata==32'h11112222&&!pslverr,"O_READBACK");
    step(0,1,1,0,4,0);check(prdata==32'h33334444,"O_READBACK");
    step(0,1,0,1,0,32'haaaa5555);check(prdata==32'h11112222,"O_ACCESS_PHASE");
    step(0,1,1,1,8,32'hffffffff);check(pslverr&&prdata==0,"O_INVALID_ADDRESS");
    step(0,0,0,0,8,0);check(!pslverr,"O_ERROR_GATING");
    step(0,1,1,0,0,0);check(prdata==32'h11112222,"O_WRITE_READ_SEPARATION");step(0,1,1,0,4,0);check(prdata==32'h33334444,"O_WRITE_READ_SEPARATION");
    if(errors==0)begin $display("RTLREASON_RESULT:PASS");$finish;end $fatal(1,"RTLREASON_RESULT:FAIL errors=%0d",errors);
  end
endmodule
