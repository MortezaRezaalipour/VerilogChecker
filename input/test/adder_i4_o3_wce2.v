/* Generated by Yosys 0.9 (git sha1 1979e0b) */

module adder_i4_o3_wce2(pi0, pi1, pi2, pi3, po0, po1, po2);
  input pi0;
  input pi1;
  input pi2;
  input pi3;
  output po0;
  output po1;
  output po2;
  assign po0 = pi3 & pi1;
  assign po1 = ~(pi3 & pi1);
  assign po2 = pi3 ^ pi1;
endmodule
