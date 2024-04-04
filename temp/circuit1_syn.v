/* Generated by Yosys 0.34+27 (git sha1 7d30f716e, clang 10.0.0-4ubuntu1 -fPIC -Os) */

module adder_i4_o3_wce2(in0, in1, in2, in3, out0, out1, out2);
  wire _00_;
  wire _01_;
  wire _02_;
  wire _03_;
  input in0;
  wire in0;
  input in1;
  wire in1;
  input in2;
  wire in2;
  input in3;
  wire in3;
  output out0;
  wire out0;
  output out1;
  wire out1;
  output out2;
  wire out2;
  assign _02_ = ~in1;
  assign _03_ = ~in3;
  assign out1 = ~(in1 & in3);
  assign out0 = ~out1;
  assign _00_ = ~(_02_ & _03_);
  assign _01_ = ~(out1 & _00_);
  assign out2 = ~_01_;
endmodule

