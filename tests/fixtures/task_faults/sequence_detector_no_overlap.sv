module sequence_detector_1011 (
  input wire clk,
  input wire rst,
  input wire bit_valid,
  input wire bit_in,
  output reg match
);
  reg [1:0] state;
  always @(posedge clk) begin
    if (rst) begin
      state <= 0;
      match <= 0;
    end else begin
      match <= 0;
      if (bit_valid) begin
        case (state)
          0: state <= bit_in ? 1 : 0;
          1: state <= bit_in ? 1 : 2;
          2: state <= bit_in ? 3 : 0;
          3: if (bit_in) begin
               match <= 1;
               state <= 0;
             end else state <= 2;
        endcase
      end
    end
  end
endmodule
