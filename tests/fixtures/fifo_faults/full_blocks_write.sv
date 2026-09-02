// Deliberate fault: a currently-full FIFO rejects the simultaneous write.
module fifo_sync #(
  parameter integer DATA_WIDTH = 8,
  parameter integer DEPTH = 4
) (
  input wire clk, input wire rst, input wire wr_en, input wire rd_en,
  input wire [DATA_WIDTH-1:0] din, output reg [DATA_WIDTH-1:0] dout,
  output wire full, output wire empty
);
  localparam integer ADDR_WIDTH = $clog2(DEPTH);
  reg [DATA_WIDTH-1:0] mem [0:DEPTH-1];
  reg [ADDR_WIDTH-1:0] read_ptr, write_ptr;
  reg [ADDR_WIDTH:0] count;
  assign empty = (count == 0);
  assign full = (count == DEPTH);
  wire read_accept = rd_en && !empty;
  wire write_accept = wr_en && !full;
  function automatic [ADDR_WIDTH-1:0] next_ptr(input [ADDR_WIDTH-1:0] ptr);
    next_ptr = (ptr == DEPTH-1) ? 0 : ptr + 1'b1;
  endfunction
  always @(posedge clk) begin
    if (rst) begin
      read_ptr <= 0; write_ptr <= 0; count <= 0; dout <= 0;
    end else begin
      if (write_accept) begin mem[write_ptr] <= din; write_ptr <= next_ptr(write_ptr); end
      if (read_accept) begin dout <= mem[read_ptr]; read_ptr <= next_ptr(read_ptr); end
      case ({write_accept, read_accept})
        2'b10: count <= count + 1'b1;
        2'b01: count <= count - 1'b1;
        default: count <= count;
      endcase
    end
  end
endmodule
