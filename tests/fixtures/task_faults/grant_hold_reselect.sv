module grant_hold_arbiter (
  input wire clk,
  input wire rst,
  input wire [3:0] req,
  input wire accept,
  output reg [3:0] grant
);
  function automatic [3:0] choose;
    input [3:0] r;
    begin
      if (r[0]) choose = 4'b0001;
      else if (r[1]) choose = 4'b0010;
      else if (r[2]) choose = 4'b0100;
      else if (r[3]) choose = 4'b1000;
      else choose = 0;
    end
  endfunction
  always @(posedge clk) begin
    if (rst) grant <= 0;
    else if (accept) grant <= 0;
    else grant <= choose(req);
  end
endmodule
