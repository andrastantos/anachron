from math import *

"""
Let's consider log->lin conversion under the following assumptions:

10-bit log scale numbers with 10th of a semi-note resolution.

Our input number is L. We cut it into two parts:

E = L / 120
M = L % 120

(Note: we don't have to actually do the divide and modulo, but that's besides the point for now)

E is the octave designator, that is it's the power of 2.

M is the logarithmic value between 1.0 and 2.0.

So, the linearized value of M is: mm = (2**(1/120))**M

We cut M into the top 4 and the bottom 3 bits. So: M = 2**3 * Mh + Ml. Putting that into the former:

mm = (2**(1/120))**(2**3 * Mh + Ml) = (2**(1/120))**(2**3 * Mh) * (2**(1/120))**Ml = (2**(1/15))**Mh * (2**(1/120))**Ml

"""

print("Ml map")
for Ml in range(8):
    mml = (2**(1/120))**(Ml)
    print(f"    {Ml}: {mml}")

print("Mh map")
for Mh in range(16):
    mmh = (2**(1/15))**(Mh)
    print(f"    {Mh}: {mmh}")

"""
What we can see is mml is always smaller then mmh.

This is great, because it allows for Bresenham algorithm to be applied, at least I *think*.

"""