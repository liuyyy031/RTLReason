module request_ack_timeout #(
  parameter integer TIMEOUT_CYCLES = 4
) (
  input  wire clk,
  input  wire rst,
  input  wire req,
  input  wire ack,
  output reg  busy,
  output reg  done,
  output reg  timeout
);
  localparam integer REM_WIDTH = $clog2(TIMEOUT_CYCLES + 1);
  reg [REM_WIDTH-1:0] remaining;

  always @(posedge clk) begin
    if (rst) begin
      busy <= 1'b0;
      done <= 1'b0;
      timeout <= 1'b0;
      remaining <= {REM_WIDTH{1'b0}};
    end else begin
      done <= 1'b0;
      timeout <= 1'b0;
      if (!busy) begin
        if (req) begin
          busy <= 1'b1;
          remaining <= TIMEOUT_CYCLES;
        end
      end else if (ack) begin
        busy <= 1'b0;
        done <= 1'b1;
        remaining <= {REM_WIDTH{1'b0}};
      end else if (remaining == 1) begin
        busy <= 1'b0;
        timeout <= 1'b1;
        remaining <= {REM_WIDTH{1'b0}};
      end else begin
        remaining <= remaining - 1'b1;
      end
    end
  end
endmodule
