module signed_alu_flags_formal;
  localparam integer WIDTH = 4;
  (* anyconst *) wire [WIDTH-1:0] a;
  (* anyconst *) wire [WIDTH-1:0] b;
  (* anyconst *) wire [1:0] op;
  wire [WIDTH-1:0] result;
  wire zero;
  wire negative;
  wire carry;
  wire overflow;
  wire [WIDTH:0] add_extended = {1'b0, a} + {1'b0, b};

  signed_alu_flags #(.WIDTH(WIDTH)) dut (.*);

  always @* begin
    // O_ZERO, O_NEGATIVE, O_COMBINATIONAL
    assert(zero == (result == 0));
    assert(negative == result[WIDTH-1]);
    case (op)
      2'b00: begin
        // O_ADD_RESULT, O_CARRY, O_OVERFLOW
        assert(result == a + b);
        assert(carry == add_extended[WIDTH]);
        assert(
          overflow == ((~(a[WIDTH-1] ^ b[WIDTH-1]))
            && (result[WIDTH-1] ^ a[WIDTH-1]))
        );
      end
      2'b01: begin
        // O_SUB_RESULT, O_CARRY, O_OVERFLOW
        assert(result == a - b);
        assert(carry == (a >= b));
        assert(
          overflow == ((a[WIDTH-1] ^ b[WIDTH-1])
            && (result[WIDTH-1] ^ a[WIDTH-1]))
        );
      end
      2'b10: begin
        // O_LOGIC_RESULT
        assert(result == (a & b));
        assert(carry == 0 && overflow == 0);
      end
      2'b11: begin
        // O_LOGIC_RESULT
        assert(result == (a ^ b));
        assert(carry == 0 && overflow == 0);
      end
    endcase
  end
endmodule
