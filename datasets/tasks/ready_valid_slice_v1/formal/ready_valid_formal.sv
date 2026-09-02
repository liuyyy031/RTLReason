module ready_valid_formal;
  localparam integer DATA_WIDTH = 8;
  reg clk = 0;
  always @($global_clock) clk <= !clk;
  reg rst = 1;
  (* anyseq *) reg in_valid;
  wire in_ready;
  (* anyseq *) reg [DATA_WIDTH-1:0] in_data;
  wire out_valid;
  (* anyseq *) reg out_ready;
  wire [DATA_WIDTH-1:0] out_data;
  ready_valid_slice #(.DATA_WIDTH(DATA_WIDTH)) dut (.*);

  reg past_valid = 0;
  reg model_valid = 0;
  reg [DATA_WIDTH-1:0] model_data = 0;
  wire model_ready = !model_valid || out_ready;

  always @(posedge clk) begin
    past_valid <= 1;
    rst <= 0;
    if (past_valid) begin
      assert(out_valid == model_valid);
      assert(out_data == model_data);
      assert(in_ready == model_ready);
      if ($past(rst)) begin
        assert(!out_valid);
        assert(out_data == 0);
      end
    end
    if (rst) begin
      model_valid <= 0;
      model_data <= 0;
    end else if (model_ready) begin
      model_valid <= in_valid;
      if (in_valid) model_data <= in_data;
    end
  end
endmodule
