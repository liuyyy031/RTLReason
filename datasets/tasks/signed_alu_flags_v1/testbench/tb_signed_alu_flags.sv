module tb_signed_alu_flags;
  localparam integer WIDTH = 4;
  reg [WIDTH-1:0] a = 0;
  reg [WIDTH-1:0] b = 0;
  reg [1:0] op = 0;
  wire [WIDTH-1:0] result;
  wire zero;
  wire negative;
  wire carry;
  wire overflow;
  wire [1:0] result_min;
  wire zero_min;
  wire negative_min;
  wire carry_min;
  wire overflow_min;
  reg [WIDTH:0] expected_extended;
  reg [WIDTH-1:0] expected_result;
  reg expected_carry;
  reg expected_overflow;
  reg [2:0] expected_extended_min;
  reg [1:0] expected_result_min;
  reg expected_carry_min;
  reg expected_overflow_min;
  integer errors = 0;
  integer a_index;
  integer b_index;
  integer op_index;

  signed_alu_flags #(.WIDTH(WIDTH)) dut (.*);
  signed_alu_flags #(.WIDTH(2)) dut_min (
    .a(a[1:0]), .b(b[1:0]), .op(op),
    .result(result_min), .zero(zero_min), .negative(negative_min),
    .carry(carry_min), .overflow(overflow_min)
  );

  task check;
    input condition;
    input [8*32-1:0] obligation;
    begin
      if (!condition) begin
        errors = errors + 1;
        $display("OBLIGATION_FAIL:%0s", obligation);
      end
    end
  endtask

  initial begin
    $dumpfile("signed_alu_flags.vcd");
    $dumpvars(0, tb_signed_alu_flags);

    for (op_index = 0; op_index < 4; op_index = op_index + 1)
      for (a_index = 0; a_index < (1 << WIDTH); a_index = a_index + 1)
        for (b_index = 0; b_index < (1 << WIDTH); b_index = b_index + 1) begin
          a = a_index;
          b = b_index;
          op = op_index;
          #1;

          expected_extended = 0;
          expected_result = 0;
          expected_carry = 0;
          expected_overflow = 0;
          case (op)
            2'b00: begin
              expected_extended = {1'b0, a} + {1'b0, b};
              expected_result = expected_extended[WIDTH-1:0];
              expected_carry = expected_extended[WIDTH];
              expected_overflow = (~(a[WIDTH-1] ^ b[WIDTH-1]))
                && (expected_result[WIDTH-1] ^ a[WIDTH-1]);
              check(result == expected_result, "O_ADD_RESULT");
            end
            2'b01: begin
              expected_result = a - b;
              expected_carry = (a >= b);
              expected_overflow = (a[WIDTH-1] ^ b[WIDTH-1])
                && (expected_result[WIDTH-1] ^ a[WIDTH-1]);
              check(result == expected_result, "O_SUB_RESULT");
            end
            2'b10: begin
              expected_result = a & b;
              check(result == expected_result, "O_LOGIC_RESULT");
            end
            2'b11: begin
              expected_result = a ^ b;
              check(result == expected_result, "O_LOGIC_RESULT");
            end
          endcase
          check(carry == expected_carry, "O_CARRY");
          check(overflow == expected_overflow, "O_OVERFLOW");
          check(zero == (expected_result == 0), "O_ZERO");
          check(negative == expected_result[WIDTH-1], "O_NEGATIVE");

          expected_extended_min = 0;
          expected_result_min = 0;
          expected_carry_min = 0;
          expected_overflow_min = 0;
          case (op)
            2'b00: begin
              expected_extended_min = {1'b0, a[1:0]} + {1'b0, b[1:0]};
              expected_result_min = expected_extended_min[1:0];
              expected_carry_min = expected_extended_min[2];
              expected_overflow_min = (~(a[1] ^ b[1]))
                && (expected_result_min[1] ^ a[1]);
            end
            2'b01: begin
              expected_result_min = a[1:0] - b[1:0];
              expected_carry_min = (a[1:0] >= b[1:0]);
              expected_overflow_min = (a[1] ^ b[1])
                && (expected_result_min[1] ^ a[1]);
            end
            2'b10: expected_result_min = a[1:0] & b[1:0];
            2'b11: expected_result_min = a[1:0] ^ b[1:0];
          endcase
          check(result_min == expected_result_min, "O_COMBINATIONAL");
          check(carry_min == expected_carry_min, "O_CARRY");
          check(overflow_min == expected_overflow_min, "O_OVERFLOW");
          check(zero_min == (expected_result_min == 0), "O_ZERO");
          check(negative_min == expected_result_min[1], "O_NEGATIVE");
        end

    if (errors == 0) begin
      $display("RTLREASON_RESULT:PASS");
      $finish;
    end
    $fatal(1, "RTLREASON_RESULT:FAIL errors=%0d", errors);
  end
endmodule
