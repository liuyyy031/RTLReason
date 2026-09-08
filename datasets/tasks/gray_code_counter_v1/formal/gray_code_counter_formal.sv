module gray_code_counter_formal;
  localparam integer WIDTH = 3;
  reg clk = 0;
  always @($global_clock) clk <= !clk;

  reg rst = 1;
  (* anyseq *) reg en;
  wire [WIDTH-1:0] gray;
  wire wrap;

  gray_code_counter #(.WIDTH(WIDTH)) dut (.*);

  reg past_valid = 0;
  reg [WIDTH-1:0] model_index = 0;
  reg model_wrap = 0;
  wire [WIDTH-1:0] model_gray = model_index ^ (model_index >> 1);

  always @(posedge clk) begin
    past_valid <= 1;
    rst <= 0;

    if (past_valid) begin
      assert(gray == model_gray);
      assert(wrap == model_wrap);

      if ($past(rst)) begin
        assert(gray == 0);
        assert(wrap == 0);
      end else if ($past(en)) begin
        assert((gray ^ $past(gray)) != 0);
        assert(
          ((gray ^ $past(gray)) & ((gray ^ $past(gray)) - 1'b1)) == 0
        );
      end else begin
        assert(gray == $past(gray));
        assert(wrap == 0);
      end
    end

    if (rst) begin
      model_index <= 0;
      model_wrap <= 0;
    end else if (en) begin
      model_wrap <= &model_index;
      model_index <= model_index + 1'b1;
    end else begin
      model_wrap <= 0;
    end
  end
endmodule
