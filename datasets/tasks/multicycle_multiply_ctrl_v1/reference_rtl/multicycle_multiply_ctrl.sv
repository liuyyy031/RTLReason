module multicycle_multiply_ctrl #(parameter integer WIDTH=8)(input wire clk,input wire rst,input wire start,input wire[WIDTH-1:0]a,input wire[WIDTH-1:0]b,output reg busy,output reg done,output reg[2*WIDTH-1:0]result);
 localparam integer CW=(WIDTH<=1)?1:$clog2(WIDTH);reg[CW-1:0]iteration;reg[2*WIDTH-1:0]accumulator,multiplicand;reg[WIDTH-1:0]multiplier;reg[2*WIDTH-1:0]sum;
 always@* sum=accumulator+(multiplier[0]?multiplicand:{(2*WIDTH){1'b0}});
 always@(posedge clk)begin
  if(rst)begin busy<=0;done<=0;result<=0;iteration<=0;accumulator<=0;multiplicand<=0;multiplier<=0;end
  else begin done<=0;if(!busy)begin if(start)begin busy<=1;iteration<=0;accumulator<=0;multiplicand<={{WIDTH{1'b0}},a};multiplier<=b;end end
  else begin if(iteration==WIDTH-1)begin result<=sum;busy<=0;done<=1;end else begin accumulator<=sum;multiplicand<=multiplicand<<1;multiplier<=multiplier>>1;iteration<=iteration+1'b1;end end end
 end
endmodule
