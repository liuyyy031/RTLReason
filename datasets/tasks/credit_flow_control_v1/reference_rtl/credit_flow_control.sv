module credit_flow_control #(
    parameter integer MAX_CREDITS = 3
) (
    input  wire clk,
    input  wire rst,
    input  wire send_req,
    input  wire credit_return,
    output wire send_accept,
    output reg  [$clog2(MAX_CREDITS+1)-1:0] credits,
    output wire empty,
    output wire full
);
    assign empty = (credits == 0);
    assign full = (credits == MAX_CREDITS);
    assign send_accept = !rst && send_req && !empty;

    always @(posedge clk) begin
        if (rst) begin
            credits <= MAX_CREDITS;
        end else begin
            case ({send_accept, credit_return})
                2'b10: credits <= credits - 1'b1;
                2'b01: begin
                    if (!full)
                        credits <= credits + 1'b1;
                end
                default: credits <= credits;
            endcase
        end
    end
endmodule
