module top(a, b, c);
input [1:0]a;
input [1:0]b;
output [2:0]c;

assign c = a + b;

endmodule