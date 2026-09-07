module tb_stream_width_adapter;
  reg clk=0,rst=0,in_valid=0,out_ready=0;reg[7:0]in_data=0;wire in_ready,out_valid;wire[15:0]out_data;integer errors=0;
  stream_width_adapter dut(.*);always #5 clk=~clk;
  task step;input next_rst,next_valid,next_out_ready;input[7:0]next_data;begin @(negedge clk);rst=next_rst;in_valid=next_valid;in_data=next_data;out_ready=next_out_ready;@(posedge clk);#1;end endtask
  task check;input condition;input[8*32-1:0]obligation;begin if(!condition)begin errors=errors+1;$display("OBLIGATION_FAIL:%0s",obligation);end end endtask
  initial begin
    $dumpfile("stream_width_adapter.vcd");$dumpvars(0,tb_stream_width_adapter);
    step(1,1,1,8'haa);check(!out_valid&&out_data==0&&in_ready,"O_RESET");
    step(0,1,0,8'h34);check(!out_valid&&in_ready,"O_FIRST_BYTE");
    step(0,1,0,8'h12);check(out_valid&&out_data==16'h1234&&!in_ready,"O_PACK_ORDER");check(!in_ready,"O_READY");
    step(0,1,0,8'hff);check(out_valid&&out_data==16'h1234,"O_BACKPRESSURE");
    step(0,1,1,8'h56);check(!out_valid&&out_data==16'h1234&&in_ready,"O_NO_REPLACEMENT");check(!out_valid,"O_OUTPUT_TRANSFER");
    step(0,1,0,8'h56);check(!out_valid,"O_FIRST_BYTE");step(0,1,0,8'h78);check(out_valid&&out_data==16'h7856,"O_PACK_ORDER");
    if(errors==0)begin $display("RTLREASON_RESULT:PASS");$finish;end $fatal(1,"RTLREASON_RESULT:FAIL errors=%0d",errors);
  end
endmodule
