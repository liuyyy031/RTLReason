module ready_valid_fifo2_formal;
  localparam integer DATA_WIDTH = 8;
  reg clk = 0;
  always @($global_clock) clk <= !clk;
  reg rst = 1;
  (* anyseq *) reg in_valid;
  wire in_ready;
  (* anyseq *) reg [DATA_WIDTH-1:0] in_data;
  wire out_valid;
  (* anyseq *) reg out_ready;
  wire [DATA_WIDTH-1:0] out_data;
  ready_valid_fifo2 #(.DATA_WIDTH(DATA_WIDTH)) dut (.*);

  reg past_valid = 0;
  reg [DATA_WIDTH-1:0] model_mem [0:1];
  reg model_read_ptr = 0;
  reg model_write_ptr = 0;
  reg [1:0] model_count = 0;
  wire model_valid = model_count != 0;
  wire model_output_transfer = model_valid && out_ready;
  wire model_ready = (model_count < 2) || model_output_transfer;
  wire model_input_transfer = in_valid && model_ready;

  always @(posedge clk) begin
    past_valid <= 1;
    rst <= 0;
    if (past_valid) begin
      assert(out_valid == model_valid);
      assert(in_ready == model_ready);
      assert(out_data == (model_valid ? model_mem[model_read_ptr] : 0));
      assert(model_count <= 2);
      if ($past(rst)) assert(!out_valid && out_data == 0);
    end

    if (rst) begin
      model_read_ptr <= 0;
      model_write_ptr <= 0;
      model_count <= 0;
    end else begin
      if (model_input_transfer) begin
        model_mem[model_write_ptr] <= in_data;
        model_write_ptr <= ~model_write_ptr;
      end
      if (model_output_transfer)
        model_read_ptr <= ~model_read_ptr;
      case ({model_input_transfer, model_output_transfer})
        2'b10: model_count <= model_count + 1'b1;
        2'b01: model_count <= model_count - 1'b1;
        default: model_count <= model_count;
      endcase
    end
  end
endmodule
