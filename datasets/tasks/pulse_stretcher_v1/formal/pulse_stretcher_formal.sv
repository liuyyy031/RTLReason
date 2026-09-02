module pulse_stretcher_formal;
  localparam integer PULSE_CYCLES = 3;
  localparam integer COUNT_WIDTH = $clog2(PULSE_CYCLES + 1);
  reg clk = 0;
  always @($global_clock) clk <= !clk;
  reg rst = 1;
  (* anyseq *) reg trigger;
  wire active;
  pulse_stretcher #(.PULSE_CYCLES(PULSE_CYCLES)) dut (.*);

  reg past_valid = 0;
  reg model_active = 0;
  reg [COUNT_WIDTH-1:0] model_remaining = 0;

  always @(posedge clk) begin
    past_valid <= 1;
    rst <= 0;
    if (past_valid) begin
      assert(active == model_active);
      if ($past(rst)) assert(!active);
      if (!$past(rst) && $past(trigger)) assert(active);
    end

    if (rst) begin
      model_active <= 0;
      model_remaining <= 0;
    end else if (trigger) begin
      model_active <= 1;
      model_remaining <= PULSE_CYCLES;
    end else if (model_active) begin
      if (model_remaining == 1) begin
        model_active <= 0;
        model_remaining <= 0;
      end else begin
        model_remaining <= model_remaining - 1'b1;
      end
    end else begin
      model_active <= 0;
      model_remaining <= 0;
    end
  end
endmodule
