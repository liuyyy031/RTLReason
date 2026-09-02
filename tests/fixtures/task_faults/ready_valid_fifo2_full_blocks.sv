module ready_valid_fifo2 #(
  parameter integer DATA_WIDTH = 8
) (
  input wire clk, rst, in_valid,
  output wire in_ready,
  input wire [DATA_WIDTH-1:0] in_data,
  output wire out_valid,
  input wire out_ready,
  output wire [DATA_WIDTH-1:0] out_data
);
  reg [DATA_WIDTH-1:0] mem [0:1];
  reg read_ptr, write_ptr;
  reg [1:0] count;
  assign out_valid = count != 0;
  assign in_ready = count < 2;
  wire push = in_valid && in_ready;
  wire pop = out_valid && out_ready;
  assign out_data = out_valid ? mem[read_ptr] : 0;
  always @(posedge clk) begin
    if (rst) begin read_ptr <= 0; write_ptr <= 0; count <= 0; end
    else begin
      if (push) begin mem[write_ptr] <= in_data; write_ptr <= ~write_ptr; end
      if (pop) read_ptr <= ~read_ptr;
      case ({push, pop})
        2'b10: count <= count + 1'b1;
        2'b01: count <= count - 1'b1;
      endcase
    end
  end
endmodule
