module signed_alu_flags #(
  parameter integer WIDTH = 8
) (
  input  wire [WIDTH-1:0] a,
  input  wire [WIDTH-1:0] b,
  input  wire [1:0]       op,
  output reg  [WIDTH-1:0] result,
  output reg              zero,
  output reg              negative,
  output reg              carry,
  output reg              overflow
);
  reg [WIDTH:0] extended;

  always @* begin
    result = {WIDTH{1'b0}};
    extended = {(WIDTH+1){1'b0}};
    carry = 1'b0;
    overflow = 1'b0;
    case (op)
      2'b00: begin
        extended = {1'b0, a} + {1'b0, b};
        result = extended[WIDTH-1:0];
        carry = extended[WIDTH];
        overflow = (~(a[WIDTH-1] ^ b[WIDTH-1]))
          && (result[WIDTH-1] ^ a[WIDTH-1]);
      end
      2'b01: begin
        result = a - b;
        carry = (a >= b);
        overflow = (a[WIDTH-1] ^ b[WIDTH-1])
          && (result[WIDTH-1] ^ a[WIDTH-1]);
      end
      2'b10: result = a & b;
      2'b11: result = a ^ b;
    endcase
    zero = (result == {WIDTH{1'b0}});
    negative = result[WIDTH-1];
  end
endmodule
