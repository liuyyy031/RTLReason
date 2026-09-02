module sequence_detector_1011 (
  input  wire clk,
  input  wire rst,
  input  wire bit_valid,
  input  wire bit_in,
  output reg  match
);
  localparam [1:0] NONE = 2'd0;
  localparam [1:0] P1   = 2'd1;
  localparam [1:0] P10  = 2'd2;
  localparam [1:0] P101 = 2'd3;
  reg [1:0] state;

  always @(posedge clk) begin
    if (rst) begin
      state <= NONE;
      match <= 1'b0;
    end else begin
      match <= 1'b0;
      if (bit_valid) begin
        case (state)
          NONE: state <= bit_in ? P1 : NONE;
          P1:   state <= bit_in ? P1 : P10;
          P10:  state <= bit_in ? P101 : NONE;
          P101: begin
            if (bit_in) begin
              state <= P1;
              match <= 1'b1;
            end else begin
              state <= P10;
            end
          end
          default: state <= NONE;
        endcase
      end
    end
  end
endmodule
