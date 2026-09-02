module grant_hold_arbiter (
  input  wire       clk,
  input  wire       rst,
  input  wire [3:0] req,
  input  wire       accept,
  output reg  [3:0] grant
);
  function automatic [3:0] select_lowest;
    input [3:0] requests;
    begin
      casex (requests)
        4'b???1: select_lowest = 4'b0001;
        4'b??10: select_lowest = 4'b0010;
        4'b?100: select_lowest = 4'b0100;
        4'b1000: select_lowest = 4'b1000;
        default: select_lowest = 4'b0000;
      endcase
    end
  endfunction

  always @(posedge clk) begin
    if (rst) begin
      grant <= 4'b0000;
    end else if (grant != 4'b0000) begin
      if (accept)
        grant <= 4'b0000;
    end else begin
      grant <= select_lowest(req);
    end
  end
endmodule
