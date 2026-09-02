module round_robin_arbiter (
  input wire clk, rst,
  input wire [3:0] req,
  output reg [3:0] grant
);
  always @(posedge clk) begin
    if (rst) grant <= 0;
    else if (req[0]) grant <= 4'b0001;
    else if (req[1]) grant <= 4'b0010;
    else if (req[2]) grant <= 4'b0100;
    else if (req[3]) grant <= 4'b1000;
    else grant <= 0;
  end
endmodule
