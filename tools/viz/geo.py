"""Camera and floor-plane geometry for the photo visualizer.

Each room photo gets a pinhole camera (focal length f, principal point at the image center),
floor axes recovered from vanishing points, and a camera height. From that we get a 3x3 matrix
per surface that maps an image pixel to real-world surface coordinates in feet.
"""
import numpy as np


def hline(p, q):
    return np.cross([p[0], p[1], 1.0], [q[0], q[1], 1.0])


def vp(l1, l2):
    """Vanishing point of two image lines, each given as ((x,y),(x,y))."""
    v = np.cross(hline(*l1), hline(*l2))
    return v / v[2]


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


class Room:
    def __init__(self, W, H, f, depth_vp=None, side_vp=None, side_dir=None, height=5.0, f_from_vps=False):
        self.W, self.H = W, H
        c = np.array([W / 2.0, H / 2.0])
        if f_from_vps:
            f = float(np.sqrt(-np.dot(np.asarray(depth_vp[:2]) - c, np.asarray(side_vp[:2]) - c)))
        self.f = f
        self.K = np.array([[f, 0, c[0]], [0, f, c[1]], [0, 0, 1.0]])
        self.Ki = np.linalg.inv(self.K)
        b = unit(self.Ki @ np.array([depth_vp[0], depth_vp[1], 1.0]))  # away from camera along the floor
        if side_vp is not None:
            a = unit(self.Ki @ np.array([side_vp[0], side_vp[1], 1.0]))
        else:
            a = unit([side_dir[0], side_dir[1], 0.0])
        a = unit(a - np.dot(a, b) * b)  # make the two floor axes exactly perpendicular
        if a[0] < 0:
            a = -a  # +u runs to the right in the image
        n = unit(np.cross(a, b))
        # camera y points down in the image; the floor normal must point up (negative camera y)
        if n[1] > 0:
            n = -n
        self.a, self.b, self.n, self.h = a, b, n, height
        # floor: n.X = -h ;  (u, v, 1) ~ [a; b; -n/h] K^-1 p
        self.Hfloor = np.vstack([a, b, -n / height]) @ self.Ki

    def ray(self, px, py):
        return self.Ki @ np.array([px, py, 1.0])

    def floor_point(self, px, py):
        r = self.ray(px, py)
        s = -self.h / np.dot(self.n, r)
        return s * r

    def floor_uv(self, px, py):
        q = self.Hfloor @ np.array([px, py, 1.0])
        return q[:2] / q[2]

    def wall_H(self, along, base_px):
        """Vertical wall through the floor point under base_px, running along unit vector `along`.
        Returns a matrix mapping pixels to (distance along wall, height above floor) in feet."""
        along = unit(along - np.dot(along, self.n) * self.n)
        w = unit(np.cross(along, self.n))
        X0 = self.floor_point(*base_px)
        d = np.dot(w, X0)
        M = np.vstack([along, self.n + (self.h / d) * w, w / d])
        return M @ self.Ki

    def project(self, X):
        p = self.K @ X
        return p[:2] / p[2]

    def floor_to_px(self, u, v):
        X = u * self.a + v * self.b - self.h * self.n
        return self.project(X)
