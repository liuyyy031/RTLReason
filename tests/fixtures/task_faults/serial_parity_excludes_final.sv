module serial_parity (
  input wire clk, input wire rst, input wire start, input wire bit_valid,
  input wire bit_in, input wire finish, output reg busy, output reg parity, output reg done
);
  reg working;
  always @(posedge clk) begin
    if (rst) begin busy <= 0; parity <= 0; done <= 0; working <= 0; end
    else begin
      done <= 0;
      if (!busy && start) begin busy <= 1; working <= bit_valid ? bit_in : 0; end
      else if (busy && finish) begin parity <= working; done <= 1; busy <= 0; working <= 0; end
      else if (busy && bit_valid) working <= working ^ bit_in;
    end
  end
endmodule
