module tb_credit_flow_control;
    localparam integer MAX_CREDITS = 3;
    localparam integer CREDIT_WIDTH = $clog2(MAX_CREDITS+1);

    reg clk = 0;
    reg rst = 0;
    reg send_req = 0;
    reg credit_return = 0;
    wire send_accept;
    wire [CREDIT_WIDTH-1:0] credits;
    wire empty;
    wire full;
    wire min_send_accept;
    wire min_credits;
    wire min_empty;
    wire min_full;
    integer errors = 0;

    always #5 clk = ~clk;

    credit_flow_control #(.MAX_CREDITS(MAX_CREDITS)) dut (
        .clk(clk), .rst(rst), .send_req(send_req),
        .credit_return(credit_return), .send_accept(send_accept),
        .credits(credits), .empty(empty), .full(full)
    );

    credit_flow_control #(.MAX_CREDITS(1)) dut_min (
        .clk(clk), .rst(rst), .send_req(send_req),
        .credit_return(credit_return), .send_accept(min_send_accept),
        .credits(min_credits), .empty(min_empty), .full(min_full)
    );

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

    task apply_edge;
        input req_value;
        input return_value;
        input expected_accept;
        input [CREDIT_WIDTH-1:0] expected_credits;
        input [8*32-1:0] obligation;
        begin
            send_req = req_value;
            credit_return = return_value;
            #1;
            check(send_accept == expected_accept, obligation);
            @(posedge clk);
            #1;
            check(credits == expected_credits, obligation);
            check(empty == (expected_credits == 0), "O_FLAGS_RANGE");
            check(full == (expected_credits == MAX_CREDITS), "O_FLAGS_RANGE");
        end
    endtask

    initial begin
        $dumpfile("credit_flow_control.vcd");
        $dumpvars(0, tb_credit_flow_control);

        rst = 1;
        send_req = 1;
        credit_return = 1;
        #1;
        check(!send_accept && !min_send_accept, "O_RESET");
        @(posedge clk);
        #1;
        check(credits == MAX_CREDITS && full, "O_RESET");
        check(min_credits == 1 && min_full, "O_RESET");
        rst = 0;

        apply_edge(0, 1, 0, 3, "O_FULL_SATURATION");
        apply_edge(1, 0, 1, 2, "O_CONSUME");
        apply_edge(1, 1, 1, 2, "O_MIDDLE_SIMULTANEOUS");
        apply_edge(1, 0, 1, 1, "O_CURRENT_ACCEPT");
        apply_edge(1, 0, 1, 0, "O_CONSUME");
        apply_edge(1, 0, 0, 0, "O_CURRENT_ACCEPT");
        apply_edge(1, 1, 0, 1, "O_EMPTY_NO_LOOKAHEAD");
        apply_edge(0, 1, 0, 2, "O_RETURN");
        apply_edge(0, 1, 0, 3, "O_RETURN");
        apply_edge(1, 1, 1, 3, "O_FULL_SIMULTANEOUS");

        rst = 1;
        send_req = 0;
        credit_return = 0;
        @(posedge clk);
        #1;
        rst = 0;
        send_req = 1;
        credit_return = 1;
        #1;
        check(min_send_accept, "O_FULL_SIMULTANEOUS");
        @(posedge clk);
        #1;
        check(min_credits == 1 && min_full, "O_FULL_SIMULTANEOUS");
        send_req = 1;
        credit_return = 0;
        #1;
        check(min_send_accept, "O_CONSUME");
        @(posedge clk);
        #1;
        check(min_credits == 0 && min_empty, "O_FLAGS_RANGE");
        send_req = 1;
        credit_return = 1;
        #1;
        check(!min_send_accept, "O_EMPTY_NO_LOOKAHEAD");
        @(posedge clk);
        #1;
        check(min_credits == 1, "O_EMPTY_NO_LOOKAHEAD");

        if (errors == 0) begin
            $display("RTLREASON_RESULT:PASS");
            $finish;
        end
        $fatal(1, "RTLREASON_RESULT:FAIL errors=%0d", errors);
    end
endmodule
