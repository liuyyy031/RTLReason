module async_handshake_formal;
    reg src_clk = 0;
    reg dst_clk = 0;
    reg phase = 0;
    always @($global_clock) begin
        src_clk <= !src_clk;
        phase <= !phase;
        if (phase)
            dst_clk <= !dst_clk;
    end

    reg src_rst = 1;
    reg dst_rst = 1;
    (* anyseq *) reg src_send;
    wire src_accept, src_busy, dst_pulse;
    reg source_started = 0;
    reg destination_started = 0;

    async_handshake dut (.*);

    always @(posedge src_clk) begin
        source_started <= 1;
        src_rst <= 0;
        if (source_started) begin
            assert(src_accept == (src_send && !src_busy));
            if (src_busy && src_send)
                assert(!src_accept);
        end
    end

    always @(posedge dst_clk) begin
        destination_started <= 1;
        dst_rst <= 0;
        if (destination_started) begin
            if ($past(dst_pulse))
                assert(!dst_pulse);
        end
    end

    always @(*) begin
        assume(!src_rst || !src_busy);
        assume(!dst_rst || !src_busy);
        assert(!(src_rst && src_accept));
    end
endmodule
