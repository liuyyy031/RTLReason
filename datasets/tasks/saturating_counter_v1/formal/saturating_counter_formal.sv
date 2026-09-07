module saturating_counter_formal;
  localparam integer WIDTH = 3;
  reg clk = 0;
  always @($global_clock) clk <= !clk;
  reg rst = 1;
  (* anyseq *) reg en;
  (* anyseq *) reg up;
  wire [WIDTH-1:0] count;
  wire at_min, at_max;
  saturating_counter #(.WIDTH(WIDTH)) dut (.*);

  reg past_valid = 0;
  reg [WIDTH-1:0] model_count = 0;
  always @(posedge clk) begin
    past_valid <= 1;
    rst <= 0;
    if (past_valid) begin
      assert(count == model_count);
      assert(at_min == (count == 0));
      assert(at_max == (count == {WIDTH{1'b1}}));
    end
    if (rst) model_count <= 0;
    else if (en && up && model_count != {WIDTH{1'b1}}) model_count <= model_count + 1'b1;
    else if (en && !up && model_count != 0) model_count <= model_count - 1'b1;
  end
endmodule
