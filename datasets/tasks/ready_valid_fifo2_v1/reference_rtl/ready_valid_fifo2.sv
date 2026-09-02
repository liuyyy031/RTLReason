module ready_valid_fifo2 #(
  parameter integer DATA_WIDTH = 8
) (
  input  wire                  clk,
  input  wire                  rst,
  input  wire                  in_valid,
  output wire                  in_ready,
  input  wire [DATA_WIDTH-1:0] in_data,
  output wire                  out_valid,
  input  wire                  out_ready,
  output wire [DATA_WIDTH-1:0] out_data
);
  reg [DATA_WIDTH-1:0] mem [0:1];
  reg read_ptr;
  reg write_ptr;
  reg [1:0] count;

  assign out_valid = count != 0;
  wire output_transfer = out_valid && out_ready;
  assign in_ready = (count < 2) || output_transfer;
  wire input_transfer = in_valid && in_ready;
  assign out_data = out_valid ? mem[read_ptr] : {DATA_WIDTH{1'b0}};

  always @(posedge clk) begin
    if (rst) begin
      read_ptr <= 1'b0;
      write_ptr <= 1'b0;
      count <= 2'd0;
    end else begin
      if (input_transfer) begin
        mem[write_ptr] <= in_data;
        write_ptr <= ~write_ptr;
      end
      if (output_transfer)
        read_ptr <= ~read_ptr;
      case ({input_transfer, output_transfer})
        2'b10: count <= count + 1'b1;
        2'b01: count <= count - 1'b1;
        default: count <= count;
      endcase
    end
  end
endmodule
