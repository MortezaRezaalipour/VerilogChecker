module adder_i4_o3_wce2_tb;
reg [3:0]pi;
wire [2:0]po;
adder_i4_o3_wce2 dut (pi[3], pi[2], pi[1], pi[0], po[2], po[1], po[0]);
initial
begin
# 1 pi=4'b0000;
#1 $display("%b", po);
# 1 pi=4'b0010;
#1 $display("%b", po);
# 1 pi=4'b0001;
#1 $display("%b", po);
# 1 pi=4'b0011;
#1 $display("%b", po);
# 1 pi=4'b1000;
#1 $display("%b", po);
# 1 pi=4'b1010;
#1 $display("%b", po);
# 1 pi=4'b1001;
#1 $display("%b", po);
# 1 pi=4'b1011;
#1 $display("%b", po);
# 1 pi=4'b0100;
#1 $display("%b", po);
# 1 pi=4'b0110;
#1 $display("%b", po);
# 1 pi=4'b0101;
#1 $display("%b", po);
# 1 pi=4'b0111;
#1 $display("%b", po);
# 1 pi=4'b1100;
#1 $display("%b", po);
# 1 pi=4'b1110;
#1 $display("%b", po);
# 1 pi=4'b1101;
#1 $display("%b", po);
# 1 pi=4'b1111;
#1 $display("%b", po);
end
endmodule
