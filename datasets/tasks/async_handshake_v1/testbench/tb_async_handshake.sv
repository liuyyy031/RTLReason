module tb_async_handshake;
    reg src_clk = 0;
    reg dst_clk = 0;
    reg src_rst = 1;
    reg dst_rst = 1;
    reg src_send = 0;
    wire src_accept, src_busy, dst_pulse;
    integer delivered = 0;
    integer errors = 0;

    always #5 src_clk = ~src_clk;
    always #7 dst_clk = ~dst_clk;

    async_handshake dut (.*);

    always @(posedge dst_clk) begin
        if (dst_pulse)
            delivered = delivered + 1;
    end

    task check;
        input condition;
        input [8*32-1:0] obligation;
        begin
            if (!condition) begin
                errors = errors + 1;
                $display("OBLIGATION_FAIL:%0s", obligation);
            end
        end
    endtask

    task send_one;
        begin
            @(negedge src_clk);
            src_send = 1;
            #1;
            check(src_accept, "O_SOURCE_ACCEPT");
            @(posedge src_clk);
            #1;
            src_send = 0;
            check(src_busy, "O_ACK_RETURN");
        end
    endtask

    initial begin
        $dumpfile("async_handshake.vcd");
        $dumpvars(0, tb_async_handshake);
        repeat (2) @(posedge src_clk);
        repeat (2) @(posedge dst_clk);
        src_rst = 0;
        dst_rst = 0;
        @(negedge src_clk);
        #1;
        check(!src_busy && !dst_pulse, "O_RESET");

        send_one;
        @(negedge src_clk);
        src_send = 1;
        #1;
        check(!src_accept, "O_BUSY_GATING");
        @(posedge src_clk);
        #1;
        src_send = 0;
        repeat (8) @(posedge dst_clk);
        #1;
        check(delivered == 1, "O_EXACTLY_ONCE");
        check(!src_busy, "O_ACK_RETURN");

        send_one;
        repeat (8) @(posedge dst_clk);
        #1;
        check(delivered == 2, "O_EXACTLY_ONCE");
        check(!src_busy && !dst_pulse, "O_SINGLE_PULSE");
        if (errors == 0) begin
            $display("RTLREASON_RESULT:PASS");
            $finish;
        end
        $fatal(1, "RTLREASON_RESULT:FAIL errors=%0d", errors);
    end
endmodule
