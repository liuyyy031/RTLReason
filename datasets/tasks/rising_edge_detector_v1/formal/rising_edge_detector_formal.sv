module rising_edge_detector_formal;
  reg clk = 0;
  always @($global_clock) clk <= !clk;
  reg rst = 1;
  (* anyseq *) reg signal_in;
  wire pulse;

  rising_edge_detector dut (.*);

  reg past_valid = 0;
  reg model_previous = 0;
  reg model_pulse = 0;

  always @(posedge clk) begin
    past_valid <= 1;
    rst <= 0;

    if (past_valid) begin
      assert(pulse == model_pulse);
      if ($past(rst)) assert(!pulse);
    end

    if (rst) begin
      model_previous <= 0;
      model_pulse <= 0;
    end else begin
      model_pulse <= signal_in && !model_previous;
      model_previous <= signal_in;
    end
  end
endmodule
