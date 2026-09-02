module shift_register #(
  parameter integer WIDTH = 8
) (
  input  wire             clk,
  input  wire             rst,
  input  wire             en,
  input  wire             serial_in,
  output reg  [WIDTH-1:0] q,
  output wire             serial_out
);
  assign serial_out = q[WIDTH-1];

  always @(posedge clk) begin
    if (rst)
      q <= {WIDTH{1'b0}};
    else if (en)
      q <= {q[WIDTH-2:0], serial_in};
  end
endmodule
