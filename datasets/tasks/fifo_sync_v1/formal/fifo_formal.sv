module fifo_formal;
  localparam integer DATA_WIDTH = 8;
  localparam integer DEPTH = 4;
  localparam integer ADDR_WIDTH = $clog2(DEPTH);

  // Derive a conventional design clock from the formal global clock.  Using
  // the global clock directly on the shadow memory turns its writes into
  // unsupported global-clock memory cells in Yosys.
  reg clk = 1'b0;
  always @($global_clock)
    clk <= !clk;
  reg rst = 1'b1;
  (* anyseq *) reg wr_en;
  (* anyseq *) reg rd_en;
  (* anyseq *) reg [DATA_WIDTH-1:0] din;
  wire [DATA_WIDTH-1:0] dout;
  wire full;
  wire empty;

  fifo_sync #(.DATA_WIDTH(DATA_WIDTH), .DEPTH(DEPTH)) dut (
    .clk(clk), .rst(rst), .wr_en(wr_en), .rd_en(rd_en), .din(din),
    .dout(dout), .full(full), .empty(empty)
  );

  reg past_valid = 1'b0;
  reg [DATA_WIDTH-1:0] model_mem [0:DEPTH-1];
  reg [ADDR_WIDTH-1:0] model_read_ptr = 0;
  reg [ADDR_WIDTH-1:0] model_write_ptr = 0;
  reg [ADDR_WIDTH:0] model_count = 0;
  reg expected_valid = 1'b0;
  reg [DATA_WIDTH-1:0] expected_dout = 0;

  wire model_empty = (model_count == 0);
  wire model_full = (model_count == DEPTH);
  wire model_read_accept = rd_en && !model_empty;
  wire model_write_accept = wr_en && (!model_full || model_read_accept);

  function automatic [ADDR_WIDTH-1:0] next_ptr;
    input [ADDR_WIDTH-1:0] ptr;
    begin
      if (ptr == DEPTH-1)
        next_ptr = 0;
      else
        next_ptr = ptr + 1'b1;
    end
  endfunction

  always @(posedge clk) begin
    past_valid <= 1'b1;
    rst <= 1'b0;

    if (past_valid) begin
      assert(full == model_full);
      assert(empty == model_empty);
      assert(!(full && empty));
      assert(model_count <= DEPTH);
      if (expected_valid)
        assert(dout == expected_dout);
      if ($past(rst)) begin
        assert(empty);
        assert(!full);
        assert(dout == 0);
      end
    end

    if (rst) begin
      model_read_ptr <= 0;
      model_write_ptr <= 0;
      model_count <= 0;
      expected_valid <= 1'b0;
      expected_dout <= 0;
    end else begin
      expected_valid <= model_read_accept;
      if (model_read_accept) begin
        expected_dout <= model_mem[model_read_ptr];
        model_read_ptr <= next_ptr(model_read_ptr);
      end
      if (model_write_accept) begin
        model_mem[model_write_ptr] <= din;
        model_write_ptr <= next_ptr(model_write_ptr);
      end
      case ({model_write_accept, model_read_accept})
        2'b10: model_count <= model_count + 1'b1;
        2'b01: model_count <= model_count - 1'b1;
        default: model_count <= model_count;
      endcase
    end
  end
endmodule
