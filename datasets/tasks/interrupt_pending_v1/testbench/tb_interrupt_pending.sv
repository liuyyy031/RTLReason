module tb_interrupt_pending;
  reg clk=0,rst=0,ack=0; reg [3:0] irq=0,mask=0; wire [3:0] pending; wire valid; wire [1:0] index; integer errors=0;
  interrupt_pending dut(.*); always #5 clk=~clk;
  task step; input nr,na; input [3:0] ni,nm; begin @(negedge clk);rst=nr;ack=na;irq=ni;mask=nm;@(posedge clk);#1;end endtask
  task check; input condition; input [8*32-1:0] obligation; begin if(!condition)begin errors=errors+1;$display("OBLIGATION_FAIL:%0s",obligation);end end endtask
  initial begin
    $dumpfile("interrupt_pending.vcd");$dumpvars(0,tb_interrupt_pending);
    step(1,1,4'hf,0);check(pending==0,"O_RESET");
    step(0,0,4'b1010,4'b1000);check(pending==4'b0010,"O_MASK");check(valid&&index==1,"O_PRIORITY");
    step(0,0,4'b0101,0);check(pending==4'b0111,"O_CAPTURE");check(index==0,"O_PRIORITY");
    step(0,1,4'b0000,0);check(pending==4'b0110,"O_ACK");check(index==1,"O_PRIORITY");
    step(0,1,4'b0010,0);check(pending==4'b0110,"O_SET_DOMINANT");
    step(0,1,4'b1000,0);check(pending==4'b1100,"O_ACCUMULATE");
    step(0,0,0,4'hf);check(pending==4'b1100,"O_MASK");
    if(errors==0)begin $display("RTLREASON_RESULT:PASS");$finish;end $fatal(1,"RTLREASON_RESULT:FAIL errors=%0d",errors);
  end
endmodule
