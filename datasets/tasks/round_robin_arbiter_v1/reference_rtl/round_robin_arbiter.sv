module round_robin_arbiter (
  input  wire       clk,
  input  wire       rst,
  input  wire [3:0] req,
  output reg  [3:0] grant
);
  reg [1:0] pointer;
  reg [3:0] grant_next;
  integer offset;
  integer index;
  reg found;

  always @* begin
    grant_next = 4'b0000;
    found = 1'b0;
    for (offset = 0; offset < 4; offset = offset + 1) begin
      index = pointer + offset;
      if (index >= 4)
        index = index - 4;
      if (!found && req[index]) begin
        grant_next[index] = 1'b1;
        found = 1'b1;
      end
    end
  end

  always @(posedge clk) begin
    if (rst) begin
      grant <= 4'b0000;
      pointer <= 2'd0;
    end else begin
      grant <= grant_next;
      if (grant_next[0]) pointer <= 2'd1;
      else if (grant_next[1]) pointer <= 2'd2;
      else if (grant_next[2]) pointer <= 2'd3;
      else if (grant_next[3]) pointer <= 2'd0;
    end
  end
endmodule
