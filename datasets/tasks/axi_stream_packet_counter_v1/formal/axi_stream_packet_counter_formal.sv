module axi_stream_packet_counter_formal;
  localparam integer COUNT_WIDTH = 3;
  localparam [COUNT_WIDTH-1:0] MAXIMUM = {COUNT_WIDTH{1'b1}};
  reg clk = 0;
  always @($global_clock) clk <= !clk;

  reg rst = 1;
  (* anyseq *) reg clear;
  (* anyseq *) reg tvalid;
  (* anyseq *) reg tready;
  (* anyseq *) reg tlast;
  wire [COUNT_WIDTH-1:0] beat_count;
  wire [COUNT_WIDTH-1:0] packet_count;

  axi_stream_packet_counter #(.COUNT_WIDTH(COUNT_WIDTH)) dut (.*);

  reg past_valid = 0;
  reg [COUNT_WIDTH-1:0] model_beat_count = 0;
  reg [COUNT_WIDTH-1:0] model_packet_count = 0;

  always @(posedge clk) begin
    past_valid <= 1;
    rst <= 0;

    if (past_valid) begin
      // O_BEAT_COUNT, O_PACKET_COUNT, O_SATURATION
      assert(beat_count == model_beat_count);
      assert(packet_count == model_packet_count);

      if ($past(rst)) begin
        // O_RESET
        assert(beat_count == 0 && packet_count == 0);
      end else if ($past(clear)) begin
        // O_CLEAR, including clear plus transfer
        assert(beat_count == 0 && packet_count == 0);
      end else if (!($past(tvalid) && $past(tready))) begin
        // O_TRANSFER_GATE, O_HOLD
        assert(beat_count == $past(beat_count));
        assert(packet_count == $past(packet_count));
      end
    end

    if (rst || clear) begin
      model_beat_count <= 0;
      model_packet_count <= 0;
    end else if (tvalid && tready) begin
      if (model_beat_count != MAXIMUM)
        model_beat_count <= model_beat_count + 1'b1;
      if (tlast && model_packet_count != MAXIMUM)
        model_packet_count <= model_packet_count + 1'b1;
    end
  end
endmodule
