"""Print the Blender border (x0 y0 x1 y1, y measured from the bottom) around the floor mask, with a margin."""
import sys
import numpy as np
from mix import read
A = read(sys.argv[1])
f = A['floor'] > 0.01
H, W = f.shape
ys, xs = np.where(f)
pad = 4
x0, x1 = max(0, xs.min() - pad), min(W, xs.max() + 1 + pad)
y0, y1 = max(0, ys.min() - pad), min(H, ys.max() + 1 + pad)
print(f'{x0 / W:.5f} {1 - y1 / H:.5f} {x1 / W:.5f} {1 - y0 / H:.5f}')
