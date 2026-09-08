module tb_uart_rx;
    localparam integer CPB = 4;
    reg clk = 0, rst = 1, rx = 1;
    wire [7:0] data_out; wire data_valid, framing_error, busy;
    integer errors = 0, valid_count = 0;
    reg [7:0] last_data = 0; reg last_error = 0;
    always #5 clk = ~clk;
    uart_rx #(.CLKS_PER_BIT(CPB)) dut (.*);
    always @(posedge clk) if (data_valid) begin valid_count = valid_count + 1; last_data = data_out; last_error = framing_error; end
    task check; input c; input [8*32-1:0] o; begin if(!c) begin errors=errors+1; $display("OBLIGATION_FAIL:%0s",o); end end endtask
    task send_level; input value; begin @(negedge clk); rx=value; repeat(CPB) @(posedge clk); end endtask
    task send_frame; input [7:0] word; input stop; integer i; begin
        send_level(0); for(i=0;i<8;i=i+1) send_level(word[i]); send_level(stop);
    end endtask
    initial begin
        $dumpfile("uart_rx.vcd"); $dumpvars(0,tb_uart_rx);
        repeat(2) @(posedge clk); rst=0; #1; check(!busy&&!data_valid&&!framing_error,"O_RESET");
        send_frame(8'hA6,1); repeat(4) @(posedge clk); #1; check(valid_count==1&&last_data==8'hA6&&!last_error,"O_LSB_FIRST");
        check(!data_valid&&!framing_error,"O_VALID_PULSE");
        send_frame(8'h3C,0); @(negedge clk); rx=1; repeat(4) @(posedge clk); #1; check(valid_count==2&&last_data==8'h3C&&last_error,"O_FRAMING_ERROR");
        check(!busy,"O_BUSY");
        @(negedge clk); rx=0; repeat(1) @(posedge clk); @(negedge clk); rx=1; repeat(5) @(posedge clk); #1; check(!busy&&!data_valid,"O_START_CENTER");
        if(errors==0) begin $display("RTLREASON_RESULT:PASS"); $finish; end $fatal(1,"RTLREASON_RESULT:FAIL errors=%0d",errors);
    end
endmodule
