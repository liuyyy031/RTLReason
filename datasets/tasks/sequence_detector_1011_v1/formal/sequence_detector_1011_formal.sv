module sequence_detector_1011_formal;
  reg clk = 0;
  always @($global_clock) clk <= !clk;
  reg rst = 1;
  (* anyseq *) reg bit_valid;
  (* anyseq *) reg bit_in;
  wire match;
  sequence_detector_1011 dut (.*);

  localparam [1:0] NONE = 2'd0;
  localparam [1:0] P1   = 2'd1;
  localparam [1:0] P10  = 2'd2;
  localparam [1:0] P101 = 2'd3;
  reg [1:0] model_state = NONE;
  reg model_match = 0;
  reg past_valid = 0;

  always @(posedge clk) begin
    past_valid <= 1;
    rst <= 0;
    if (past_valid) begin
      assert(match == model_match);
      if ($past(rst)) assert(!match);
      if (!$past(rst) && !$past(bit_valid)) assert(!match);
    end

    if (rst) begin
      model_state <= NONE;
      model_match <= 0;
    end else begin
      model_match <= 0;
      if (bit_valid) begin
        case (model_state)
          NONE: model_state <= bit_in ? P1 : NONE;
          P1:   model_state <= bit_in ? P1 : P10;
          P10:  model_state <= bit_in ? P101 : NONE;
          P101: begin
            if (bit_in) begin
              model_state <= P1;
              model_match <= 1;
            end else begin
              model_state <= P10;
            end
          end
          default: model_state <= NONE;
        endcase
      end
    end
  end
endmodule
