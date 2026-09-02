module token_bucket_formal;
  localparam integer CAPACITY = 3;
  localparam integer TOKEN_WIDTH = $clog2(CAPACITY + 1);
  reg clk = 0;
  always @($global_clock) clk <= !clk;
  reg rst = 1;
  (* anyseq *) reg req;
  wire grant;
  wire [TOKEN_WIDTH-1:0] tokens;
  token_bucket #(.CAPACITY(CAPACITY)) dut (.*);

  reg past_valid = 0;
  reg model_grant = 0;
  reg [TOKEN_WIDTH-1:0] model_tokens = 0;
  reg model_add;
  reg model_take;

  always @(posedge clk) begin
    past_valid <= 1;
    rst <= 0;
    if (past_valid) begin
      assert(tokens == model_tokens);
      assert(grant == model_grant);
      assert(tokens <= CAPACITY);
      if ($past(rst)) assert(tokens == 0 && !grant);
    end

    if (rst) begin
      model_tokens <= 0;
      model_grant <= 0;
    end else begin
      model_add = model_tokens < CAPACITY;
      model_take = req && model_tokens != 0;
      model_grant <= model_take;
      case ({model_add, model_take})
        2'b10: model_tokens <= model_tokens + 1'b1;
        2'b01: model_tokens <= model_tokens - 1'b1;
        default: model_tokens <= model_tokens;
      endcase
    end
  end
endmodule
