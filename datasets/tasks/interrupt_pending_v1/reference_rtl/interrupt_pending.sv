module interrupt_pending(
  input wire clk,input wire rst,input wire [3:0] irq,input wire [3:0] mask,input wire ack,
  output reg [3:0] pending,output wire valid,output reg [1:0] index
);
  reg [3:0] ack_onehot;
  assign valid = |pending;
  always @* begin
    index = 2'd0; ack_onehot = 4'b0000;
    if (pending[0]) begin index=0; ack_onehot=4'b0001; end
    else if (pending[1]) begin index=1; ack_onehot=4'b0010; end
    else if (pending[2]) begin index=2; ack_onehot=4'b0100; end
    else if (pending[3]) begin index=3; ack_onehot=4'b1000; end
  end
  always @(posedge clk) begin
    if (rst) pending <= 4'b0000;
    else pending <= (pending & ~(ack ? ack_onehot : 4'b0000)) | (irq & ~mask);
  end
endmodule
