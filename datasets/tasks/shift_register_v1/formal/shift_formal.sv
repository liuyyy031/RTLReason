module shift_formal;
  localparam integer WIDTH = 4;
  reg clk = 0;
  always @($global_clock) clk <= !clk;
  reg rst = 1;
  (* anyseq *) reg en;
  (* anyseq *) reg serial_in;
  wire [WIDTH-1:0] q;
  wire serial_out;
  shift_register #(.WIDTH(WIDTH)) dut (.*);

  reg past_valid = 0;
  reg [WIDTH-1:0] model_q = 0;
  always @(posedge clk) begin
    past_valid <= 1;
    rst <= 0;
    if (past_valid) begin
      assert(q == model_q);
      assert(serial_out == q[WIDTH-1]);
      if ($past(rst)) assert(q == 0);
    end
    if (rst)
      model_q <= 0;
    else if (en)
      model_q <= {model_q[WIDTH-2:0], serial_in};
  end
endmodule
