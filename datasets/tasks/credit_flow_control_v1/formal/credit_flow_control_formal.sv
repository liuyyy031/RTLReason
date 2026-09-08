module credit_flow_control_formal;
    localparam integer MAX_CREDITS = 3;
    localparam integer CREDIT_WIDTH = $clog2(MAX_CREDITS+1);

    reg clk = 0;
    always @($global_clock) clk <= !clk;

    (* anyseq *) reg rst;
    (* anyseq *) reg send_req;
    (* anyseq *) reg credit_return;
    wire send_accept;
    wire [CREDIT_WIDTH-1:0] credits;
    wire empty;
    wire full;
    reg past_valid = 0;

    credit_flow_control #(.MAX_CREDITS(MAX_CREDITS)) dut (
        .clk(clk), .rst(rst), .send_req(send_req),
        .credit_return(credit_return), .send_accept(send_accept),
        .credits(credits), .empty(empty), .full(full)
    );

    always @(posedge clk) begin
        past_valid <= 1;
        if (!past_valid) begin
            assume(rst);
        end else begin
            assert(credits <= MAX_CREDITS);
            assert(empty == (credits == 0));
            assert(full == (credits == MAX_CREDITS));
            assert(send_accept == (!rst && send_req && credits != 0));

            if ($past(rst)) begin
                assert(credits == MAX_CREDITS);
            end else if ($past(send_accept) && !$past(credit_return)) begin
                assert(credits == $past(credits) - 1'b1);
            end else if (!$past(send_accept) && $past(credit_return)
                         && $past(credits) < MAX_CREDITS) begin
                assert(credits == $past(credits) + 1'b1);
            end else begin
                assert(credits == $past(credits));
            end

            if ($past(credits) == 0 && $past(send_req)
                && $past(credit_return) && !$past(rst)) begin
                assert(!$past(send_accept));
                assert(credits == 1);
            end
            if ($past(credits) == MAX_CREDITS && $past(send_req)
                && $past(credit_return) && !$past(rst)) begin
                assert($past(send_accept));
                assert(credits == MAX_CREDITS);
            end
        end
    end
endmodule
