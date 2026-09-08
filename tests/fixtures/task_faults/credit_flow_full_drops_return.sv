module credit_flow_control #(
    parameter integer MAX_CREDITS = 3
) (
    input wire clk, input wire rst, input wire send_req,
    input wire credit_return, output wire send_accept,
    output reg [$clog2(MAX_CREDITS+1)-1:0] credits,
    output wire empty, output wire full
);
    assign empty = (credits == 0);
    assign full = (credits == MAX_CREDITS);
    assign send_accept = !rst && send_req && !empty;
    always @(posedge clk) begin
        if (rst)
            credits <= MAX_CREDITS;
        else if (send_accept)
            credits <= credits - 1'b1;
        else if (credit_return && !full)
            credits <= credits + 1'b1;
    end
endmodule
