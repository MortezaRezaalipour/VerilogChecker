module adder_i12_o7_approx(a, b, c);
input [5:0]a;
input [5:0]b;
output [6:0]c;

assign c = a + b;
assign c[6] = 1'b0;
endmodule