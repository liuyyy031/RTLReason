module debounce_filter_formal;
  localparam integer STABLE_CYCLES = 3;
  localparam integer COUNT_WIDTH = $clog2(STABLE_CYCLES + 1);
  reg clk = 0;
  always @($global_clock) clk <= !clk;
  reg rst = 1;
  (* anyseq *) reg noisy_in;
  wire debounced;
  wire changed;
  debounce_filter #(.STABLE_CYCLES(STABLE_CYCLES)) dut (.*);

  reg past_valid = 0;
  reg model_debounced = 0;
  reg model_changed = 0;
  reg [COUNT_WIDTH-1:0] model_consecutive = 0;

  always @(posedge clk) begin
    past_valid <= 1;
    rst <= 0;
    if (past_valid) begin
      assert(debounced == model_debounced);
      assert(changed == model_changed);
      if ($past(rst)) assert(!debounced && !changed);
      if (changed) assert(debounced != $past(debounced));
    end

    if (rst) begin
      model_debounced <= 0;
      model_changed <= 0;
      model_consecutive <= 0;
    end else begin
      model_changed <= 0;
      if (noisy_in == model_debounced) begin
        model_consecutive <= 0;
      end else if (model_consecutive == STABLE_CYCLES - 1) begin
        model_debounced <= noisy_in;
        model_changed <= 1;
        model_consecutive <= 0;
      end else begin
        model_consecutive <= model_consecutive + 1'b1;
      end
    end
  end
endmodule
