module apb_register_bank (
  input  wire        clk,
  input  wire        rst,
  input  wire        psel,
  input  wire        penable,
  input  wire        pwrite,
  input  wire [3:0]  paddr,
  input  wire [31:0] pwdata,
  output wire        pready,
  output wire [31:0] prdata,
  output wire        pslverr
);

  reg [31:0] reg0;
  reg [31:0] reg1;

  // Synchronous update with highest priority reset
  always_ff @(posedge clk) begin
    if (rst) begin
      reg0 <= 32'd0;
      reg1 <= 32'd0;
    end else if (psel && penable && pwrite) begin
      if (paddr == 4'h0)      reg0 <= pwdata;
      else if (paddr == 4'h4) reg1 <= pwdata;
    end
  end

  // Always ready
  assign pready = 1'b1;

  // Combinational read data
  assign prdata = (paddr == 4'h0) ? reg0 :
                  (paddr == 4'h4) ? reg1 : 32'd0;

  // Error only on access-phase transfer to invalid address
  assign pslverr = (psel && penable && !(paddr == 4'h0 || paddr == 4'h4)) ? 1'b1 : 1'b0;

endmodule
