module rising_edge_detector (
  input  wire clk,
  input  wire rst,
  input  wire signal_in,
  output reg  pulse
);
  reg previous_sample;

  always @(posedge clk) begin
    if (rst) begin
      previous_sample <= 1'b0;
      pulse <= 1'b0;
    end else begin
      pulse <= signal_in && !previous_sample;
      previous_sample <= signal_in;
    end
  end
endmodule
