module shift_register #(
  parameter integer WIDTH = 8
) (
  input wire clk, rst, en, serial_in,
  output reg [WIDTH-1:0] q,
  output wire serial_out
);
  assign serial_out = q[WIDTH-1];
  always @(posedge clk) begin
    if (rst) q <= 0;
    else if (en) q <= {serial_in, q[WIDTH-1:1]};
  end
endmodule
