"""Per-room setup: camera, coated surfaces and things standing on the floor.
Coordinates are pixels in the original photo."""
import os
import numpy as np
from geo import Room, vp

PHOTOS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'img', 'photos') + os.sep


def line_y(p, slope):
    return lambda x: p[1] + slope * (x - p[0])


def garage_solid():
    W, H = 1200, 798
    v_right = vp(((860, 352.5), (1160, 335.5)), ((760, 497.5), (940, 533.5)))  # along the right wall
    door = line_y((160, 587.5), (542.5 - 587.5) / (600 - 160))                  # door bottom at the floor
    hy = v_right[1]
    x_door_vp = 160 + (hy - 587.5) / ((542.5 - 587.5) / (600 - 160))
    v_door = np.array([x_door_vp, hy, 1.0])
    room = Room(W, H, None, depth_vp=v_right, side_vp=v_door, height=4.56, f_from_vps=True)  # 16 ft door
    corner_x = 736
    corner = (corner_x, door(corner_x))
    sl_base = (corner[1] - v_right[1]) / (corner[0] - v_right[0])
    sl_top = (497.5 - v_right[1]) / (760 - v_right[0])
    rbase = line_y(corner, sl_base)
    rtop = line_y((760, 497.5), sl_top)
    ltop = line_y((40, 557.5), (554.5 - 559.5) / 60.0)
    xs = np.linspace(corner_x, W, 24)
    floor = [(0, H), (0, door(0)), (corner_x, door(corner_x))] + [(x, rbase(x)) for x in xs] + [(W, H)]
    rstem = [(x, rtop(x)) for x in xs] + [(x, rbase(x)) for x in xs[::-1]]
    lstem = [(0, ltop(0)), (117, ltop(117)), (117, door(117)), (0, door(0))]
    surfaces = [
        dict(kind='floor', poly=floor),
        dict(kind='wall', poly=rstem, along=room.b, base=(1000, rbase(1000))),
        dict(kind='wall', poly=lstem, along=room.a, base=(60, door(60))),
    ]
    holes = [
        # door jamb track foot and the bracket at the right jamb
        [(114, 560), (136, 560), (136, 600), (114, 600)],
        [(700, 515), (722, 515), (722, 545), (700, 545)],
        # shop vac
        [(1094, 548), (1132, 530), (1200, 520), (1200, 652), (1180, 652), (1150, 648), (1118, 640), (1104, 622), (1096, 590)],
    ]
    return dict(key='garage', name='Two-car garage', file='space-garage-solid.jpg', W=W, H=H, room=room,
                path=PHOTOS + 'space-garage-solid.jpg', surfaces=surfaces, holes=holes, extra_hole=yellow_bin,
                albedo_srgb=(118, 122, 124), median=5, env_k=41, diff_sigma=24, tile_ft=2.6, gloss_floor=0.004,
                eve=dict(amb=0.10, vig=0.35, gloss_keep=0.55,
                         lights=[dict(x=600, y=-260, sx=700, sy=620, k=0.42),   # ceiling fixture over the camera
                                 dict(x=712, y=96, sx=150, sy=120, k=0.30)],    # opener light
                         bulbs=[dict(x=712, y=128, r=11, k=0.8)],
                         spots=[dict(x=700, y=690, sx=26, sy=70, k=0.10)]))


def yellow_bin(photo):
    import cv2
    hsv = cv2.cvtColor(photo.astype(np.uint8), cv2.COLOR_RGB2HSV).astype(float)
    m = (hsv[..., 0] > 15) & (hsv[..., 0] < 40) & (hsv[..., 1] > 110) & (hsv[..., 2] > 90)
    box = np.zeros_like(m); box[505:620, 935:1095] = True
    m = (m & box).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    m = cv2.dilate(m, np.ones((3, 3), np.uint8))
    return cv2.GaussianBlur(m.astype(float), (0, 0), 0.7)


def garage_storage():
    W, H = 1200, 900
    v = vp(((350, 165), (0, 280)), ((905, 168), (1190, 345)))
    room = Room(W, H, 932.0, depth_vp=v, side_dir=(1, 0), height=3.46)  # 3 ft back door
    floor = [(0, 292), (40, 268), (130, 240), (220, 205), (300, 180), (350, 167), (905, 167), (1200, 352), (1200, H), (0, H)]
    import math
    drain = [(680 + 19.5 * math.cos(t), 400 + 6 * math.sin(t)) for t in [i * math.pi / 12 for i in range(24)]]
    return dict(key='garage2', name='Garage with storage', W=W, H=H, room=room,
                path=PHOTOS + 'job-garage-4.jpg', surfaces=[dict(kind='floor', poly=floor)], holes=[drain],
                albedo_srgb=(186, 178, 166), median=7, env_k=41, diff_sigma=24, tile_ft=2.6, gloss_floor=0.006,
                eve=dict(amb=0.13, vig=0.35, gloss_keep=0.5,
                         lights=[dict(x=600, y=-200, sx=650, sy=560, k=0.45),
                                 dict(x=250, y=40, sx=260, sy=200, k=0.10)],
                         bulbs=[], spots=[dict(x=600, y=560, sx=40, sy=150, k=0.06)]))


def basement():
    W, H = 970, 546
    room = Room(W, H, 680.0, depth_vp=(494, 129), side_dir=(1, 0), height=5.0)
    floor = [(0, 293), (130, 249), (200, 243), (468, 241), (470, 209), (695, 209), (842, 266), (828, H), (0, H)]
    holes = [
        [(398, 436), (432, 436), (434, 455), (396, 455)],   # post base plate
        [(436, 306), (452, 306), (453, 318), (435, 318)],
        [(452, 250), (464, 250), (465, 259), (451, 259)],
    ]
    return dict(key='basement', name='Finished basement', W=W, H=H, room=room,
                path=PHOTOS + 'job-basement-1.jpg', surfaces=[dict(kind='floor', poly=floor)], holes=holes,
                extra_hole=red_posts, albedo_srgb=(186, 176, 152), median=7, env_k=41, diff_sigma=22,
                tile_ft=2.6, gloss_floor=0.006,
                eve=dict(amb=0.16, vig=0.45, gloss_keep=0.95,
                         lights=[dict(x=210, y=40, sx=230, sy=260, k=0.32),
                                 dict(x=740, y=45, sx=230, sy=260, k=0.32),
                                 dict(x=640, y=70, sx=160, sy=200, k=0.18)],
                         bulbs=[dict(x=212, y=38, r=9, k=0.55), dict(x=742, y=42, r=9, k=0.55), dict(x=641, y=69, r=7, k=0.4)],
                         spots=[]))


def red_posts(photo):
    import cv2
    hsv = cv2.cvtColor(photo.astype(np.uint8), cv2.COLOR_RGB2HSV).astype(float)
    red = ((hsv[..., 0] < 12) | (hsv[..., 0] > 165)) & (hsv[..., 1] > 70) & (hsv[..., 2] > 25)
    box = np.zeros_like(red)
    box[:, 95:240] = True        # front post
    box[:, 385:475] = True       # back posts
    m = (red & box).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 3), np.uint8))
    # the front post is a solid column: fill each row between its outer red pixels
    for y in range(m.shape[0]):
        xs = np.where(m[y, 95:240])[0]
        if len(xs) > 6:
            m[y, 95 + xs.min():95 + xs.max() + 1] = 1
    m = cv2.dilate(m, np.ones((3, 3), np.uint8))
    return cv2.GaussianBlur(m.astype(float), (0, 0), 0.7)


def patio():
    W, H = 970, 546
    room = Room(W, H, 720.0, depth_vp=(470, -260), side_dir=(1, -0.06), height=5.0)
    region = [(0, 505), (40, 470), (300, 300), (330, 250), (560, 205), (660, 200), (690, 140),
              (760, 120), (970, 95), (970, H), (0, H)]
    return dict(key='patio', name='Covered patio', W=W, H=H, room=room,
                path=PHOTOS + 'job-patio-1.jpg', surfaces=[dict(kind='floor', poly=region)],
                holes=[[(650, 190), (735, 146), (970, 160), (970, 192), (935, 242), (820, 238), (660, 214)]],
                extra_hole=patio_furniture, albedo_srgb=(226, 204, 178), median=11, env_k=1, diff_sigma=5,
                tile_ft=2.6, gloss_floor=0.6, neutral_light=True,
                eve=dict(amb=0.12, vig=0.4, gloss_keep=0.4,
                         lights=[dict(x=300, y=-120, sx=520, sy=420, k=0.38),
                                 dict(x=900, y=40, sx=300, sy=260, k=0.12)],
                         bulbs=[], spots=[]))


def patio_furniture(photo):
    import cv2
    m = cv2.medianBlur(photo.astype(np.uint8), 7)
    hsv = cv2.cvtColor(m, cv2.COLOR_RGB2HSV).astype(float)
    S, V = hsv[..., 1] / 255, hsv[..., 2]
    Hh = hsv[..., 0]
    furn = (V < 92) | (S > 0.55) | ((S > 0.48) & (V < 125))
    floor = (~furn).astype(np.uint8)
    floor = cv2.morphologyEx(floor, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    floor = cv2.morphologyEx(floor, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(floor)
    keep = np.zeros_like(floor)
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] > 1500:
            keep[lab == i] = 1
    # fill small pockets inside the floor (dark chips, joints)
    inv = (1 - keep).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(inv)
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] < 400:
            keep[lab == i] = 1
    return cv2.GaussianBlur((1 - keep).astype(float), (0, 0), 0.6)
