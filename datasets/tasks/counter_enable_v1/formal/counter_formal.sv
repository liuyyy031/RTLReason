module counter_formal;
  localparam integer WIDTH = 4;
  reg clk = 0;
  always @($global_clock) clk <= !clk;
  reg rst = 1;
  (* anyseq *) reg en;
  (* anyseq *) reg load;
  (* anyseq *) reg [WIDTH-1:0] load_value;
  wire [WIDTH-1:0] count;
  wire overflow;

  counter_enable #(.WIDTH(WIDTH)) dut (.*);

  reg past_valid = 0;
  reg [WIDTH-1:0] model_count = 0;
  reg model_overflow = 0;

  always @(posedge clk) begin
    past_valid <= 1;
    rst <= 0;
    if (past_valid) begin
      assert(count == model_count);
      assert(overflow == model_overflow);
      if ($past(rst)) begin
        assert(count == 0);
        assert(overflow == 0);
      end
    end

    if (rst) begin
      model_count <= 0;
      model_overflow <= 0;
    end else if (load) begin
      model_count <= load_value;
      model_overflow <= 0;
    end else if (en) begin
      model_overflow <= &model_count;
      model_count <= model_count + 1'b1;
    end else begin
      model_overflow <= 0;
    end
  end
endmodule
