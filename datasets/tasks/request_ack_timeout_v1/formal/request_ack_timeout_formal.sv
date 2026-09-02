module request_ack_timeout_formal;
  localparam integer TIMEOUT_CYCLES = 3;
  localparam integer REM_WIDTH = $clog2(TIMEOUT_CYCLES + 1);
  reg clk = 0;
  always @($global_clock) clk <= !clk;
  reg rst = 1;
  (* anyseq *) reg req;
  (* anyseq *) reg ack;
  wire busy, done, timeout;
  request_ack_timeout #(.TIMEOUT_CYCLES(TIMEOUT_CYCLES)) dut (.*);

  reg past_valid = 0;
  reg model_busy = 0;
  reg model_done = 0;
  reg model_timeout = 0;
  reg [REM_WIDTH-1:0] model_remaining = 0;

  always @(posedge clk) begin
    past_valid <= 1;
    rst <= 0;
    if (past_valid) begin
      assert(busy == model_busy);
      assert(done == model_done);
      assert(timeout == model_timeout);
      assert(!(done && timeout));
      if ($past(rst)) assert(!busy && !done && !timeout);
    end

    if (rst) begin
      model_busy <= 0;
      model_done <= 0;
      model_timeout <= 0;
      model_remaining <= 0;
    end else begin
      model_done <= 0;
      model_timeout <= 0;
      if (!model_busy) begin
        if (req) begin
          model_busy <= 1;
          model_remaining <= TIMEOUT_CYCLES;
        end
      end else if (ack) begin
        model_busy <= 0;
        model_done <= 1;
        model_remaining <= 0;
      end else if (model_remaining == 1) begin
        model_busy <= 0;
        model_timeout <= 1;
        model_remaining <= 0;
      end else begin
        model_remaining <= model_remaining - 1'b1;
      end
    end
  end
endmodule
