module axi_stream_packet_counter #(
  parameter integer COUNT_WIDTH = 8
) (
  input wire clk, input wire rst, input wire clear,
  input wire tvalid, input wire tready, input wire tlast,
  output reg [COUNT_WIDTH-1:0] beat_count,
  output reg [COUNT_WIDTH-1:0] packet_count
);
  wire [COUNT_WIDTH-1:0] maximum = {COUNT_WIDTH{1'b1}};
  always @(posedge clk) begin
    if (rst || clear) begin
      beat_count <= 0;
      packet_count <= 0;
    end else if (tvalid) begin
      if (beat_count != maximum)
        beat_count <= beat_count + 1'b1;
      if (tlast && packet_count != maximum)
        packet_count <= packet_count + 1'b1;
    end
  end
endmodule
