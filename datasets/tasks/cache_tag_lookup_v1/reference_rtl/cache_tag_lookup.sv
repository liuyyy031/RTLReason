module cache_tag_lookup #(
 parameter integer WAYS=4, TAG_WIDTH=6, DATA_WIDTH=8)(
 input wire [TAG_WIDTH-1:0] lookup_tag,input wire [WAYS-1:0] valid,
 input wire [WAYS*TAG_WIDTH-1:0] tags,input wire [WAYS*DATA_WIDTH-1:0] data,
 output reg hit,output reg [$clog2(WAYS)-1:0] hit_way,
 output reg [DATA_WIDTH-1:0] hit_data);
 integer i; reg found;
 always @* begin
  hit=0;hit_way=0;hit_data=0;found=0;
  for(i=0;i<WAYS;i=i+1)
   if(!found && valid[i] && tags[i*TAG_WIDTH +: TAG_WIDTH]==lookup_tag)begin
    hit=1;hit_way=i;hit_data=data[i*DATA_WIDTH +: DATA_WIDTH];found=1;
   end
 end
endmodule
