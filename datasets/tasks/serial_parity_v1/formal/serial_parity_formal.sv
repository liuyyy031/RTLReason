module serial_parity_formal;
  reg clk = 0;
  always @($global_clock) clk <= !clk;
  reg rst = 1;
  (* anyseq *) reg start, bit_valid, bit_in, finish;
  wire busy, parity, done;
  serial_parity dut (.*);

  reg past_valid = 0;
  reg model_busy = 0, model_parity = 0, model_done = 0, model_working = 0;
  always @(posedge clk) begin
    past_valid <= 1;
    rst <= 0;
    if (past_valid) begin
      assert(busy == model_busy);
      assert(parity == model_parity);
      assert(done == model_done);
    end
    if (rst) begin
      model_busy <= 0; model_parity <= 0; model_done <= 0; model_working <= 0;
    end else begin
      model_done <= 0;
      if (!model_busy) begin
        if (start) begin model_busy <= 1; model_working <= bit_valid ? bit_in : 0; end
      end else if (finish) begin
        model_parity <= model_working ^ (bit_valid && bit_in);
        model_done <= 1; model_busy <= 0; model_working <= 0;
      end else if (bit_valid) model_working <= model_working ^ bit_in;
    end
  end
endmodule
