module serial_parity (
  input  wire clk,
  input  wire rst,
  input  wire start,
  input  wire bit_valid,
  input  wire bit_in,
  input  wire finish,
  output reg  busy,
  output reg  parity,
  output reg  done
);
  reg working;
  always @(posedge clk) begin
    if (rst) begin
      busy <= 1'b0;
      parity <= 1'b0;
      done <= 1'b0;
      working <= 1'b0;
    end else begin
      done <= 1'b0;
      if (!busy) begin
        if (start) begin
          working <= bit_valid ? bit_in : 1'b0;
          busy <= 1'b1;
        end
      end else begin
        if (finish) begin
          parity <= working ^ (bit_valid && bit_in);
          done <= 1'b1;
          busy <= 1'b0;
          working <= 1'b0;
        end else if (bit_valid) begin
          working <= working ^ bit_in;
        end
      end
    end
  end
endmodule
