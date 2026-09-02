module fifo_sync #(
  parameter integer DATA_WIDTH = 8,
  parameter integer DEPTH = 4
) (
  input  wire                  clk,
  input  wire                  rst,
  input  wire                  wr_en,
  input  wire                  rd_en,
  input  wire [DATA_WIDTH-1:0] din,
  output reg  [DATA_WIDTH-1:0] dout,
  output wire                  full,
  output wire                  empty
);
  localparam integer ADDR_WIDTH = $clog2(DEPTH);

  reg [DATA_WIDTH-1:0] mem [0:DEPTH-1];
  reg [ADDR_WIDTH:0] read_ptr;
  reg [ADDR_WIDTH:0] write_ptr;

  wire same_address =
    (read_ptr[ADDR_WIDTH-1:0] == write_ptr[ADDR_WIDTH-1:0]);
  assign empty = same_address &&
    (read_ptr[ADDR_WIDTH] == write_ptr[ADDR_WIDTH]);
  assign full = same_address &&
    (read_ptr[ADDR_WIDTH] != write_ptr[ADDR_WIDTH]);

  wire read_accept  = rd_en && !empty;
  wire write_accept = wr_en && (!full || read_accept);

  function automatic [ADDR_WIDTH:0] increment_ptr;
    input [ADDR_WIDTH:0] ptr;
    begin
      if (ptr[ADDR_WIDTH-1:0] == DEPTH-1)
        increment_ptr = {~ptr[ADDR_WIDTH], {ADDR_WIDTH{1'b0}}};
      else
        increment_ptr = ptr + 1'b1;
    end
  endfunction

  always @(posedge clk) begin
    if (rst) begin
      read_ptr  <= {(ADDR_WIDTH+1){1'b0}};
      write_ptr <= {(ADDR_WIDTH+1){1'b0}};
      dout      <= {DATA_WIDTH{1'b0}};
    end else begin
      if (write_accept) begin
        mem[write_ptr[ADDR_WIDTH-1:0]] <= din;
        write_ptr <= increment_ptr(write_ptr);
      end
      if (read_accept) begin
        dout <= mem[read_ptr[ADDR_WIDTH-1:0]];
        read_ptr <= increment_ptr(read_ptr);
      end
    end
  end
endmodule
