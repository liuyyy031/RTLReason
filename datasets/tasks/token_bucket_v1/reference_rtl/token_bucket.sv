module token_bucket #(
  parameter integer CAPACITY = 3
) (
  input  wire clk,
  input  wire rst,
  input  wire req,
  output reg  grant,
  output reg  [$clog2(CAPACITY+1)-1:0] tokens
);
  wire add_token = tokens < CAPACITY;
  wire take_token = req && tokens != 0;

  always @(posedge clk) begin
    if (rst) begin
      tokens <= 0;
      grant <= 1'b0;
    end else begin
      grant <= take_token;
      case ({add_token, take_token})
        2'b10: tokens <= tokens + 1'b1;
        2'b01: tokens <= tokens - 1'b1;
        default: tokens <= tokens;
      endcase
    end
  end
endmodule
