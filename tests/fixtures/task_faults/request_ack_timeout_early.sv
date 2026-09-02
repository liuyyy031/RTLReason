module request_ack_timeout #(
  parameter integer TIMEOUT_CYCLES = 4
) (
  input wire clk, rst, req, ack,
  output reg busy, done, timeout
);
  localparam integer REM_WIDTH = $clog2(TIMEOUT_CYCLES + 1);
  reg [REM_WIDTH-1:0] remaining;
  always @(posedge clk) begin
    if (rst) begin busy <= 0; done <= 0; timeout <= 0; remaining <= 0; end
    else begin
      done <= 0; timeout <= 0;
      if (!busy && req) begin
        busy <= 1;
        remaining <= TIMEOUT_CYCLES - 1;
      end else if (busy && ack) begin
        busy <= 0; done <= 1;
      end else if (busy && remaining == 1) begin
        busy <= 0; timeout <= 1;
      end else if (busy) remaining <= remaining - 1'b1;
    end
  end
endmodule
