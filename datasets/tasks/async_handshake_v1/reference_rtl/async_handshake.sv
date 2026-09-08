module async_handshake (
    input wire src_clk, input wire src_rst, input wire src_send,
    output wire src_accept, output wire src_busy,
    input wire dst_clk, input wire dst_rst, output reg dst_pulse
);
    reg req_toggle;
    reg ack_toggle;
    reg req_sync_1, req_sync_2, req_seen;
    reg ack_sync_1, ack_sync_2;

    assign src_busy = !src_rst && (req_toggle != ack_sync_2);
    assign src_accept = !src_rst && src_send && !src_busy;

    always @(posedge src_clk) begin
        if (src_rst) begin
            req_toggle <= 1'b0;
            ack_sync_1 <= 1'b0;
            ack_sync_2 <= 1'b0;
        end else begin
            ack_sync_1 <= ack_toggle;
            ack_sync_2 <= ack_sync_1;
            if (src_accept)
                req_toggle <= !req_toggle;
        end
    end

    always @(posedge dst_clk) begin
        if (dst_rst) begin
            req_sync_1 <= 1'b0;
            req_sync_2 <= 1'b0;
            req_seen <= 1'b0;
            ack_toggle <= 1'b0;
            dst_pulse <= 1'b0;
        end else begin
            req_sync_1 <= req_toggle;
            req_sync_2 <= req_sync_1;
            dst_pulse <= (req_sync_2 != req_seen);
            if (req_sync_2 != req_seen) begin
                req_seen <= req_sync_2;
                ack_toggle <= req_sync_2;
            end
        end
    end
endmodule
