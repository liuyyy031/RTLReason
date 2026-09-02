module arbiter_formal;
  reg clk = 0;
  always @($global_clock) clk <= !clk;
  reg rst = 1;
  (* anyseq *) reg [3:0] req;
  wire [3:0] grant;
  round_robin_arbiter dut (.*);

  reg past_valid = 0;
  reg [1:0] model_pointer = 0;
  reg [3:0] model_grant = 0;
  reg [3:0] selected;
  integer offset;
  integer index;
  reg found;

  always @* begin
    selected = 0;
    found = 0;
    for (offset = 0; offset < 4; offset = offset + 1) begin
      index = model_pointer + offset;
      if (index >= 4) index = index - 4;
      if (!found && req[index]) begin
        selected[index] = 1;
        found = 1;
      end
    end
  end

  always @(posedge clk) begin
    past_valid <= 1;
    rst <= 0;
    if (past_valid) begin
      assert(grant == model_grant);
      assert($onehot0(grant));
      if ($past(rst)) assert(grant == 0);
    end
    if (rst) begin
      model_pointer <= 0;
      model_grant <= 0;
    end else begin
      model_grant <= selected;
      if (selected[0]) model_pointer <= 1;
      else if (selected[1]) model_pointer <= 2;
      else if (selected[2]) model_pointer <= 3;
      else if (selected[3]) model_pointer <= 0;
    end
  end
endmodule
