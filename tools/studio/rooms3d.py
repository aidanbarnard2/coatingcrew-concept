"""The three visualizer rooms. Each builder returns dict(name, label_ceiling, label_lamps, camera)."""
import math
import random
from lib import (box, cyl, sphere, pbr, wood, emitter, floor_material, wall_x, wall_y, window_frame_x,
                 window_frame_y, sun, area, point, portal, camera)

R = random.Random(7)

# shared materials
def M():
    return dict(
        drywall=pbr('drywall', (0.80, 0.79, 0.76), rough=0.9, bump=0.06, bump_scale=420, spec=0.3),
        drywall_warm=pbr('drywall_warm', (0.74, 0.70, 0.63), rough=0.9, bump=0.06, bump_scale=420, spec=0.3),
        ceiling=pbr('ceiling', (0.86, 0.86, 0.85), rough=0.95, bump=0.08, bump_scale=300, spec=0.2),
        trim=pbr('trim', (0.88, 0.88, 0.86), rough=0.35, spec=0.5),
        metal=pbr('metal', (0.62, 0.63, 0.64), rough=0.35, metal=1.0),
        galv=pbr('galv', (0.55, 0.56, 0.57), rough=0.45, metal=1.0, var=0.15, var_scale=30),
        black=pbr('black', (0.03, 0.03, 0.035), rough=0.5),
        darkplastic=pbr('darkplastic', (0.05, 0.05, 0.055), rough=0.45),
        yellow=pbr('yellow', (0.75, 0.55, 0.02), rough=0.4),
        grayplastic=pbr('grayplastic', (0.32, 0.33, 0.34), rough=0.5),
        blueplastic=pbr('blueplastic', (0.04, 0.12, 0.35), rough=0.45),
        greenplastic=pbr('greenplastic', (0.05, 0.18, 0.08), rough=0.45),
        whiteapp=pbr('whiteapp', (0.82, 0.82, 0.80), rough=0.25, coat=0.5),
        door_steel=pbr('door_steel', (0.85, 0.85, 0.84), rough=0.4, bump=0.02, bump_scale=60),
        grass=pbr('grass', (0.11, 0.15, 0.05), rough=0.95, var=0.5, var_scale=0.8, bump=0.3, bump_scale=80),
        concrete_out=pbr('concrete_out', (0.42, 0.41, 0.39), rough=0.9, var=0.2, var_scale=3, bump=0.1, bump_scale=60),
        siding=pbr('siding', (0.62, 0.60, 0.55), rough=0.8, var=0.1, var_scale=2),
        fence=wood('fence', (0.36, 0.25, 0.15), ring_scale=2.0, rough=0.8),
        bark=pbr('bark', (0.12, 0.09, 0.07), rough=0.9, bump=0.4, bump_scale=30),
        leaves=pbr('leaves', (0.05, 0.1, 0.03), rough=0.8, var=0.6, var_scale=3, bump=0.8, bump_scale=18, translucent=0.2),
        bench=wood('bench', (0.55, 0.38, 0.22), ring_scale=4, rough=0.5),
        osb=pbr('osb', (0.55, 0.43, 0.27), rough=0.85, var=0.35, var_scale=40, bump=0.2, bump_scale=60),
        pegboard=pbr('pegboard', (0.45, 0.31, 0.18), rough=0.8, var=0.1, var_scale=10),
        glass_lens=emitter('lens_soft', 1.0),
    )


def outdoors(m, W, D, extra=()):
    """Ground, a fence line and a few trees, so windows look out onto a yard, not a void."""
    box('ground', -40, -40, -0.08, 40, 40, -0.02, m['grass'])
    for i, (x, y, s) in enumerate(extra):
        cyl(f'trunk{i}', x, y, -0.02, 3.0 * s, 0.12 * s, m['bark'], seg=12)
        for j in range(22):
            a = R.uniform(0, 6.283); rr = R.uniform(0, 1.5) * s
            sphere(f'canopy{i}_{j}', x + rr * math.cos(a), y + rr * math.sin(a), (3.6 + R.uniform(-0.8, 1.6)) * s,
                   R.uniform(0.55, 1.0) * s, m['leaves'], seg=12, scale=(1, 1, R.uniform(0.7, 1.0)))


def ceiling_box(m, W, D, H, mat=None):
    box('ceiling', -0.3, -0.3, H, W + 0.3, D + 0.3, H + 0.12, mat or m['ceiling'])


def baseboards(m, W, D, skip=()):
    t, h = 0.015, 0.09
    if 'left' not in skip:
        box('bb_l', 0, 0, 0, t, D, h, m['trim'])
    if 'right' not in skip:
        box('bb_r', W - t, 0, 0, W, D, h, m['trim'])
    if 'far' not in skip:
        box('bb_f', 0, D - t, 0, W, D, h, m['trim'])


def outlet(name, x, y, z, face, m):
    """Small wall plate. face: 'L','R','F' (which wall it sits on)."""
    if face == 'L':
        box(name, x, y - 0.035, z - 0.06, x + 0.008, y + 0.035, z + 0.06, m['trim'], bevel=0.002)
    elif face == 'R':
        box(name, x - 0.008, y - 0.035, z - 0.06, x, y + 0.035, z + 0.06, m['trim'], bevel=0.002)
    else:
        box(name, x - 0.035, y - 0.008, z - 0.06, x + 0.035, y, z + 0.06, m['trim'], bevel=0.002)


def interior_door_on_y_wall(name, x_face, ya, yb, m, side='R'):
    """Closed door slab plus casing on a wall that runs along Y (left or right wall)."""
    s = -1 if side == 'R' else 1
    xf = x_face
    door = pbr('door_paint', (0.83, 0.82, 0.79), rough=0.35, spec=0.5)
    box(name + '_slab', xf + s * 0.0, ya, 0.01, xf + s * 0.035, yb, 2.03, door, bevel=0.004)
    for i, (za, zb) in enumerate([(0.25, 0.95), (1.1, 1.85)]):
        box(f'{name}_pnl{i}', xf + s * 0.035, ya + 0.12, za, xf + s * 0.045, yb - 0.12, zb, door, bevel=0.006)
    box(name + '_c1', xf, ya - 0.07, 0, xf + s * 0.018, ya, 2.1, m['trim'], bevel=0.003)
    box(name + '_c2', xf, yb, 0, xf + s * 0.018, yb + 0.07, 2.1, m['trim'], bevel=0.003)
    box(name + '_c3', xf, ya - 0.07, 2.03, xf + s * 0.018, yb + 0.07, 2.1, m['trim'], bevel=0.003)
    knob_y = yb - 0.08 if side == 'R' else ya + 0.08
    sphere(name + '_knob', xf + s * 0.075, knob_y, 0.95, 0.03, m['metal'], seg=16)


# ======================================================================= GARAGE
def garage(mode):
    m = M()
    W, D, H = 6.8, 7.3, 2.9
    box('floor', -0.2, -0.2, -0.05, W + 0.2, D + 0.2, 0.0, floor_material(mode))
    outdoors(m, W, D, extra=[(-12, -6, 1.8), (-8, 24, 2.2), (16, -2, 2.0), (3, 30, 2.4), (15, 22, 1.9), (-6, 34, 2.1)])
    box('driveway', 0.4, D, -0.05, W - 0.4, D + 9, -0.01, m['concrete_out'])
    box('neighbor', -19, -2, -0.02, -16, 14, 5, m['siding'])
    box('neighbor2', W + 16, -2, -0.02, W + 19, 14, 5, m['siding'])
    for i in range(30):
        box(f'fence_l{i}', -3.5, -1 + i * 0.5, -0.02, -3.45, -1 + i * 0.5 + 0.46, 1.8, m['fence'])
    # walls
    lw = [(5.55, 6.4, 1.15, 2.05)]
    rw = [(5.45, 6.3, 1.15, 2.05)]
    wall_y('wl', -0.3, D + 0.3, 0, 0.16, H, m['drywall'], holes=lw, inside=-1)
    wall_y('wr', -0.3, D + 0.3, W, 0.16, H, m['drywall'], holes=rw, inside=+1)
    wall_x('wb', -0.3, W + 0.3, 0, 0.16, H, m['drywall'], inside=-1)
    door_open = (0.95, 5.85, 0.0, 2.15)
    wall_x('wf', -0.3, W + 0.3, D, 0.16, H, m['drywall'], holes=[door_open], inside=+1)
    ceiling_box(m, W, D, H)
    for (ya, yb, za, zb) in lw:
        window_frame_y('wlf', 0.0, ya, yb, za, zb, m['trim'], depth=0.12, bars=1)
        box('wl_sill', -0.02, ya - 0.04, za - 0.03, 0.05, yb + 0.04, za, m['trim'])
        portal(-0.08, (ya + yb) / 2, (za + zb) / 2, yb - ya, zb - za, normal=(1, 0, 0))
    for (ya, yb, za, zb) in rw:
        window_frame_y('wrf', W, ya, yb, za, zb, m['trim'], depth=0.12, bars=1)
        box('wr_sill', W - 0.05, ya - 0.04, za - 0.03, W + 0.02, yb + 0.04, za, m['trim'])
        portal(W + 0.08, (ya + yb) / 2, (za + zb) / 2, yb - ya, zb - za, normal=(-1, 0, 0))
    # garage door: four sections on the inside of the opening, windows in the top one
    y0, y1 = D - 0.075, D - 0.03
    secs = [(0.0, 0.535), (0.545, 1.08), (1.09, 1.625), (1.635, 2.2)]
    xa, xb = 0.85, 5.95
    wins = []
    for i in range(4):
        cx = xa + (xb - xa) * (i + 0.5) / 4
        wins.append((cx - 0.42, cx + 0.42))
    for k, (za, zb) in enumerate(secs):
        if k < 3:
            box(f'gd{k}', xa, y0, za, xb, y1, zb, m['door_steel'], bevel=0.006)
            # embossed long panels seen from inside as shallow ribs
            box(f'gd{k}_rib', xa + 0.02, y0 - 0.012, (za + zb) / 2 - 0.035, xb - 0.02, y0, (za + zb) / 2 + 0.035, m['galv'])
        else:
            wza, wzb = za + 0.17, za + 0.45
            xs = [xa] + [v for w in wins for v in w] + [xb]
            for j in range(0, len(xs) - 1, 2):
                box(f'gd3_p{j}', xs[j], y0, za, xs[j + 1], y1, zb, m['door_steel'], bevel=0.004)
            for j, (wa, wb) in enumerate(wins):
                box(f'gd3_b{j}', wa, y0, za, wb, y1, wza, m['door_steel'])
                box(f'gd3_t{j}', wa, y0, wzb, wb, y1, zb, m['door_steel'])
                window_frame_x(f'gdw{j}', y0 + 0.02, wa, wb, wza, wzb, m['trim'], depth=0.06, bars=0)
            portal((xa + xb) / 2, D + 0.2, (wza + wzb) / 2, xb - xa, 0.4, normal=(0, -1, 0))
        # hinges
        if k > 0:
            for hx in (xa + 0.06, (xa + xb) / 2, xb - 0.06):
                box(f'hinge{k}_{hx:.1f}', hx - 0.04, y0 - 0.02, za - 0.05, hx + 0.04, y0, za + 0.05, m['galv'])
    for tx in (xa - 0.06, xb + 0.06):
        box(f'vtrack{tx:.1f}', tx - 0.035, D - 0.12, 0, tx + 0.035, D - 0.02, 2.28, m['galv'])
        box(f'htrack{tx:.1f}', tx - 0.035, D - 3.3, 2.26, tx + 0.035, D - 0.02, 2.34, m['galv'])
        box(f'hang{tx:.1f}', tx - 0.02, D - 3.3, 2.34, tx + 0.02, D - 3.26, H, m['galv'])
    box('torsion_tube', 0.75, D - 0.18, 2.44, 6.05, D - 0.14, 2.48, m['galv'])
    for sx in (2.2, 3.3, 4.6):
        box(f'spring{sx}', sx - 0.35, D - 0.20, 2.42, sx + 0.35, D - 0.12, 2.50, m['black'], bevel=0.02)
    # opener: rail down the middle, motor unit, light (Work lights group)
    ox = (xa + xb) / 2
    box('rail', ox - 0.03, D - 3.6, 2.56, ox + 0.03, D - 0.25, 2.62, m['galv'])
    box('rail_hang', ox - 0.015, D - 0.3, 2.62, ox + 0.015, D - 0.25, H, m['galv'])
    box('opener', ox - 0.2, D - 4.0, 2.42, ox + 0.2, D - 3.55, 2.66, m['darkplastic'], bevel=0.02)
    box('opener_lens', ox - 0.12, D - 3.95, 2.405, ox + 0.12, D - 3.65, 2.42, emitter('opener_bulb', 6.0), group='lamps')
    point('opener_light', 'lamps', ox, D - 3.8, 2.33, 60, radius=0.06)
    for sx in (-0.15, 0.15):
        box(f'op_strap{sx}', ox + sx - 0.015, D - 3.8, 2.66, ox + sx + 0.015, D - 3.76, H, m['galv'])
    # LED shop lights (Ceiling lights group)
    for i, (lx, ly) in enumerate([(2.1, 2.3), (4.7, 2.3), (2.1, 4.9), (4.7, 4.9)]):
        box(f'led{i}_h', lx - 0.62, ly - 0.08, H - 0.05, lx + 0.62, ly + 0.08, H, m['trim'], bevel=0.005)
        box(f'led{i}_l', lx - 0.6, ly - 0.06, H - 0.056, lx + 0.6, ly + 0.06, H - 0.05, emitter('led_lens', 9.0), group='ceiling')
        area(f'led{i}', 'ceiling', lx, ly, H - 0.06, 1.2, 0.12, 260)
    # shelving with bins along the left wall
    sx0, sx1, sy0, sy1 = 0.02, 0.52, 3.4, 4.45
    for (px, py) in [(sx0, sy0), (sx1 - 0.035, sy0), (sx0, sy1 - 0.035), (sx1 - 0.035, sy1 - 0.035)]:
        box(f'post{px:.2f}{py:.2f}', px, py, 0, px + 0.035, py + 0.035, 1.9, m['black'])
    colors = ['darkplastic', 'grayplastic', 'darkplastic', 'blueplastic', 'grayplastic']
    for k, z in enumerate([0.12, 0.58, 1.04, 1.5, 1.88]):
        box(f'shelf{k}', sx0, sy0, z, sx1, sy1, z + 0.02, m['osb'])
        if k < 4:
            nb = 1 + (k % 2)
            for b in range(nb):
                ya = sy0 + 0.04 + b * 0.5
                c = colors[(k + b) % len(colors)]
                hgt = 0.30 + 0.06 * ((k + b) % 2)
                box(f'bin{k}{b}', sx0 + 0.03, ya, z + 0.02, sx1 - 0.04, ya + 0.46, z + 0.02 + hgt, m[c], bevel=0.015)
                lid = 'yellow' if c == 'darkplastic' else c
                box(f'lid{k}{b}', sx0 + 0.02, ya - 0.01, z + 0.02 + hgt, sx1 - 0.03, ya + 0.47, z + 0.05 + hgt, m[lid], bevel=0.01)
    # fridge and carts near the door, left side
    box('cart1', 0.08, 6.55, 0, 0.75, 7.15, 1.08, m['greenplastic'], bevel=0.03)
    box('cart1l', 0.05, 6.53, 1.08, 0.78, 7.17, 1.12, m['greenplastic'], bevel=0.015)
    box('cart2', W - 0.75, 6.5, 0, W - 0.1, 7.1, 1.08, m['blueplastic'], bevel=0.03)
    box('cart2l', W - 0.78, 6.48, 1.08, W - 0.07, 7.12, 1.12, m['blueplastic'], bevel=0.015)
    # workbench and pegboard on the right wall
    bx0 = W - 0.66
    box('bench_top', bx0, 3.5, 0.86, W, 5.0, 0.92, m['bench'], bevel=0.005)
    box('bench_cab', bx0 + 0.04, 3.55, 0.0, W, 4.95, 0.86, m['grayplastic'], bevel=0.008)
    for i in range(4):
        box(f'drawer{i}', bx0 + 0.03, 3.6 + i * 0.34, 0.5, bx0 + 0.045, 3.9 + i * 0.34, 0.8, m['galv'], bevel=0.004)
    box('pegboard', W - 0.02, 3.5, 1.02, W, 5.0, 1.95, m['pegboard'])
    for i, (ty, tz, h_) in enumerate([(3.7, 1.5, 0.3), (3.95, 1.45, 0.4), (4.3, 1.55, 0.25), (4.6, 1.4, 0.35)]):
        box(f'tool{i}', W - 0.05, ty - 0.02, tz - h_ / 2, W - 0.02, ty + 0.02, tz + h_ / 2, m['black'], bevel=0.005)
    box('bench_shelf', W - 0.3, 3.5, 1.98, W, 5.0, 2.0, m['osb'])
    box('bench_led', W - 0.28, 3.55, 1.972, W - 0.24, 4.95, 1.98, emitter('strip', 8.0), group='lamps')
    area('bench_light', 'lamps', W - 0.26, 4.25, 1.965, 0.04, 1.4, 50)
    box('panel', W - 0.1, 2.85, 1.2, W, 3.3, 1.85, m['grayplastic'], bevel=0.004)
    interior_door_on_y_wall('housedoor', 0.0, 4.6, 5.45, m, side='L')
    outlet('o1', 0.0, 3.2, 1.1, 'L', m); outlet('o2', W, 5.2, 1.1, 'R', m); outlet('sw1', 0.0, 5.6, 1.2, 'L', m)
    # suns: garage door faces south (+Y), left wall east, right wall west
    sun('sun_am', 100, 27)
    sun('sun_noon', 172, 46)
    sun('sun_pm', 262, 24)
    cam = camera(2.7, 0.32, 1.45, yaw_deg=-6, lens=17.0, shift_y=-0.11)
    return dict(name='Two-car garage', ceiling='Shop lights', lamps='Opener and bench lights', camera=cam)


# ===================================================================== BASEMENT
def basement(mode):
    m = M()
    W, D, H = 6.2, 8.0, 2.45
    box('floor', -0.2, -0.2, -0.05, W + 0.2, D + 0.2, 0.0, floor_material(mode))
    # window well outside the egress window on the far wall
    ww = (1.3, 2.4, 1.15, 2.1)
    wall_y('wl', -0.3, D + 0.3, 0, 0.2, H, m['drywall_warm'], inside=-1)
    wall_y('wr', -0.3, D + 0.3, W, 0.2, H, m['drywall_warm'], inside=+1)
    wall_x('wb', -0.3, W + 0.3, 0, 0.2, H, m['drywall_warm'], inside=-1)
    wall_x('wf', -0.3, W + 0.3, D, 0.2, H, m['drywall_warm'], holes=[ww], inside=+1)
    ceiling_box(m, W, D, H)
    xa, xb, za, zb = ww
    window_frame_x('egress', D + 0.02, xa, xb, za, zb, m['trim'], depth=0.1, bars=0, mull=1)
    box('egress_sill', xa - 0.04, D - 0.03, za - 0.03, xb + 0.04, D + 0.2, za, m['trim'])
    box('well_floor', xa - 0.4, D + 0.2, 0.9, xb + 0.4, D + 1.3, za - 0.02, pbr('gravel', (0.35, 0.33, 0.3), rough=0.95, bump=0.6, bump_scale=120))
    box('well_l', xa - 0.45, D + 0.2, 0.9, xa - 0.4, D + 1.3, 2.35, m['galv'])
    box('well_r', xb + 0.4, D + 0.2, 0.9, xb + 0.45, D + 1.3, 2.35, m['galv'])
    box('well_b', xa - 0.45, D + 1.25, 0.9, xb + 0.45, D + 1.3, 2.35, m['galv'])
    portal((xa + xb) / 2, D + 0.3, (za + zb) / 2, xb - xa, zb - za, normal=(0, -1, 0))
    g, gz0, gz1 = m['grass'], 2.1, 2.16
    box('gw', -40, -40, gz0, -0.25, 40, gz1, g); box('ge', W + 0.25, -40, gz0, 40, 40, gz1, g)
    box('gs', -0.25, -40, gz0, W + 0.25, -0.25, gz1, g)
    box('gn1', -0.25, D + 0.25, gz0, xa - 0.45, 40, gz1, g); box('gn2', xb + 0.45, D + 0.25, gz0, W + 0.25, 40, gz1, g)
    box('gn3', xa - 0.45, D + 1.3, gz0, xb + 0.45, 40, gz1, g)
    outdoors(m, W, D, extra=[(2, D + 7, 1.2), (-4, D + 10, 1.3), (8, D + 9, 1.1)])
    for t in [o for o in __import__('bpy').data.objects if o.name.startswith(('trunk', 'canopy'))]:
        t.location.z += 2.2
    # soffit along the right side (duct run) and baseboards
    box('soffit', W - 0.55, -0.3, H - 0.32, W, D + 0.3, H, m['ceiling'])
    baseboards(m, W, D)
    # TV wall (left) with console
    box('console', 0.0, 3.8, 0, 0.45, 5.9, 0.52, wood('walnut', (0.28, 0.17, 0.1), ring_scale=5, rough=0.4), bevel=0.008)
    for i in range(3):
        box(f'con_door{i}', 0.45, 3.86 + i * 0.68, 0.06, 0.455, 4.5 + i * 0.68, 0.46, wood('walnut', (0.28, 0.17, 0.1)), bevel=0.003)
    box('tv', 0.0, 4.2, 1.0, 0.06, 5.55, 1.77, pbr('tvglass', (0.01, 0.01, 0.012), rough=0.08, spec=0.6), bevel=0.004)
    box('soundbar', 0.06, 4.45, 0.6, 0.16, 5.3, 0.68, m['black'], bevel=0.01)
    # sectional sofa on the right, facing the TV
    fab = pbr('sofa_fab', (0.22, 0.24, 0.27), rough=0.95, sheen=0.4, bump=0.25, bump_scale=160)
    cush = pbr('cush_fab', (0.26, 0.28, 0.31), rough=0.95, sheen=0.4, bump=0.25, bump_scale=160)
    sx0 = W - 0.98
    box('sofa_base', sx0, 3.0, 0.1, W - 0.02, 6.6, 0.42, fab, bevel=0.04)
    box('sofa_back', W - 0.25, 3.0, 0.4, W - 0.02, 6.6, 0.88, fab, bevel=0.06)
    box('sofa_arm1', sx0, 2.8, 0.1, W - 0.02, 3.02, 0.64, fab, bevel=0.06)
    box('chaise', sx0 - 0.75, 5.75, 0.1, sx0 + 0.2, 6.6, 0.42, fab, bevel=0.04)
    box('sofa_arm2', sx0 - 0.75, 6.6, 0.1, W - 0.02, 6.82, 0.64, fab, bevel=0.06)
    for i in range(3):
        box(f'seat{i}', sx0 + 0.02, 3.05 + i * 0.9, 0.42, W - 0.27, 3.93 + i * 0.9, 0.56, cush, bevel=0.06)
        box(f'backc{i}', W - 0.45, 3.06 + i * 0.9, 0.55, W - 0.24, 3.92 + i * 0.9, 0.98, cush, bevel=0.08)
    box('pillow1', W - 0.5, 3.15, 0.56, W - 0.32, 3.55, 0.92, pbr('pillow_rust', (0.45, 0.16, 0.07), rough=0.95, sheen=0.5), bevel=0.07)
    for leg in [(sx0 + 0.05, 3.05), (W - 0.1, 3.05), (sx0 - 0.7, 6.5), (W - 0.1, 6.7)]:
        box(f'leg{leg[0]:.1f}{leg[1]:.1f}', leg[0], leg[1], 0, leg[0] + 0.05, leg[1] + 0.05, 0.1, m['black'])
    # coffee table and side table with lamp
    oak = wood('oak', (0.55, 0.4, 0.25), ring_scale=4, rough=0.45)
    box('ctable', 2.9, 3.9, 0.38, 4.0, 5.3, 0.43, oak, bevel=0.008)
    for (tx, ty) in [(2.95, 3.95), (3.9, 3.95), (2.95, 5.2), (3.9, 5.2)]:
        box(f'ctl{tx}{ty}', tx, ty, 0, tx + 0.05, ty + 0.05, 0.38, m['black'])
    box('book1', 3.2, 4.2, 0.43, 3.5, 4.42, 0.47, pbr('book_r', (0.5, 0.12, 0.08), rough=0.7), bevel=0.003)
    cyl('mug', 3.7, 4.9, 0.43, 0.53, 0.045, m['whiteapp'], seg=20)
    box('stable', W - 0.55, 6.9, 0, W - 0.08, 7.35, 0.6, oak, bevel=0.006)
    cyl('lamp_base', W - 0.31, 7.12, 0.6, 0.95, 0.06, pbr('ceramic', (0.75, 0.72, 0.66), rough=0.3), seg=24)
    shade = pbr('shade', (0.92, 0.88, 0.78), rough=0.9, translucent=0.65)
    cyl('lamp_shade', W - 0.31, 7.12, 0.92, 1.22, 0.19, shade, seg=32)
    import bpy
    sh = bpy.data.objects['lamp_shade']
    point('table_lamp', 'lamps', W - 0.31, 7.12, 1.08, 40, radius=0.04)
    # floor lamp by the chaise
    cyl('fl_base', 0.35, 3.25, 0, 0.03, 0.16, m['black'], seg=24)
    cyl('fl_pole', 0.35, 3.25, 0.03, 1.5, 0.014, m['black'], seg=12)
    cyl('fl_shade', 0.35, 3.25, 1.38, 1.68, 0.22, shade, seg=32)
    point('floor_lamp', 'lamps', 0.35, 3.25, 1.52, 55, radius=0.05)
    # steel post, art, utility door, rug-free floor
    cyl('post', 2.3, 6.0, 0, H, 0.045, pbr('post_paint', (0.12, 0.12, 0.13), rough=0.4), seg=20)
    box('post_plate', 2.2, 5.9, 0, 2.4, 6.1, 0.012, m['black'])
    art = pbr('art', (0.55, 0.45, 0.32), rough=0.7, var=0.9, var_scale=2.5)
    box('art', W - 0.04, 3.6, 1.25, W, 5.4, 1.95, art, bevel=0.004)
    box('art_frame', W - 0.035, 3.57, 1.22, W - 0.005, 5.43, 1.98, m['black'])
    box('art2', 3.2, D - 0.03, 1.2, 4.2, D, 1.85, pbr('art2', (0.25, 0.35, 0.42), rough=0.7, var=0.8, var_scale=3), bevel=0.003)
    interior_door_on_y_wall('util', W - 0.0, 7.0, 7.85, m, side='R')
    outlet('o1', 0.0, 3.5, 0.3, 'L', m); outlet('sw', W, 6.95, 1.2, 'R', m)
    # recessed cans (Ceiling lights)
    for i, (cx, cy) in enumerate([(1.5, 2.0), (3.9, 2.0), (1.5, 4.4), (3.9, 4.4), (1.5, 6.8), (3.9, 6.8)]):
        cyl(f'can{i}_trim', cx, cy, H - 0.008, H, 0.09, m['trim'], seg=32)
        cyl(f'can{i}_lens', cx, cy, H - 0.012, H - 0.008, 0.065, emitter('can_lens', 12.0), seg=32, group='ceiling')
        point(f'can{i}', 'ceiling', cx, cy, H - 0.03, 70, radius=0.05, spot=120, blend=0.6)
    sun('sun_am', 120, 14)   # far wall faces south: low morning sun only grazes the well
    sun('sun_noon', 180, 30)
    sun('sun_pm', 240, 16)
    cam = camera(4.75, 0.35, 1.35, yaw_deg=10, lens=17.0, shift_y=-0.1)
    return dict(name='Finished basement', ceiling='Recessed lights', lamps='Lamps', camera=cam)


# ===================================================================== SUNROOM
def sunroom(mode):
    import bpy
    m = M()
    W, D, H = 5.2, 4.6, 2.7
    box('floor', -0.2, -0.2, -0.05, W + 0.2, D + 0.2, 0.0, floor_material(mode))
    outdoors(m, W, D, extra=[(-14, -9, 2.0), (-9, 27, 2.4), (3, 31, 2.2), (14, 26, 2.3), (20, -8, 1.9), (-24, 9, 2.1), (9, 36, 2.6)])
    for i in range(12):
        box(f'hedge{i}', -8 + i * 2.0, 8.6, -0.02, -6.05 + i * 2.0, 9.6, 1.5 + 0.35 * R.random(), m['leaves'], bevel=0.25)
    for i in range(46):
        box(f'fence{i}', -6 + i * 0.4, 8.0, -0.02, -6 + i * 0.4 + 0.36, 8.04, 1.8, m['fence'])
    box('patio_out', -0.5, D, -0.05, W + 0.5, D + 2.0, -0.015, m['concrete_out'])
    sill, top = 0.75, 2.25
    white = pbr('sun_trim', (0.9, 0.9, 0.88), rough=0.4)
    # left (east) windows
    lwin = [(0.35, 1.55), (1.7, 2.9), (3.05, 4.25)]
    wall_y('wl', -0.3, D + 0.3, 0, 0.16, H, white, holes=[(a, b, sill, top) for a, b in lwin], inside=-1)
    fwin = [(0.3, 1.45), (1.6, 2.75), (2.9, 4.05), (4.2, 4.95)]
    wall_x('wf', -0.3, W + 0.3, D, 0.16, H, white, holes=[(a, b, sill, top) for a, b in fwin], inside=+1)
    rwin = [(1.9, 3.1), (3.25, 4.35)]
    wall_y('wr', -0.3, D + 0.3, W, 0.16, H, white, holes=[(a, b, sill, top) for a, b in rwin], inside=+1)
    wall_x('wb', -0.3, W + 0.3, 0, 0.16, H, m['siding'], inside=-1)
    for i, (a, b) in enumerate(lwin):
        window_frame_y(f'lw{i}', 0.0, a, b, sill, top, white, depth=0.1, bars=0, mull=1)
        portal(-0.1, (a + b) / 2, (sill + top) / 2, b - a, top - sill, normal=(1, 0, 0))
    for i, (a, b) in enumerate(fwin):
        window_frame_x(f'fw{i}', D, a, b, sill, top, white, depth=0.1, bars=0, mull=1)
        portal((a + b) / 2, D + 0.1, (sill + top) / 2, b - a, top - sill, normal=(0, -1, 0))
    for i, (a, b) in enumerate(rwin):
        window_frame_y(f'rw{i}', W, a, b, sill, top, white, depth=0.1, bars=0, mull=1)
        portal(W + 0.1, (a + b) / 2, (sill + top) / 2, b - a, top - sill, normal=(-1, 0, 0))
    # window sills and wainscot caps
    box('cap_l', 0, -0.0, sill - 0.03, 0.12, D, sill, white)
    box('cap_f', 0, D - 0.12, sill - 0.03, W, D, sill, white)
    box('cap_r', W - 0.12, 1.5, sill - 0.03, W, D, sill, white)
    baseboards(m, W, D)
    # wood plank ceiling with a beam
    pine = wood('pine', (0.66, 0.48, 0.3), ring_scale=2.5, rough=0.55)
    ceiling_box(m, W, D, H, mat=pine)
    for i in range(int(W / 0.14)):
        box(f'seam{i}', i * 0.14, -0.3, H - 0.002, i * 0.14 + 0.006, D + 0.3, H, pbr('seam', (0.2, 0.13, 0.08), rough=0.8))
    box('beam', -0.1, D / 2 - 0.09, H - 0.2, W + 0.1, D / 2 + 0.09, H, wood('beam', (0.5, 0.34, 0.2), ring_scale=2, rough=0.6), bevel=0.01)
    # ceiling fan with light kit (Ceiling light group)
    fx, fy = W / 2, D / 2 + 0.3
    cyl('fan_rod', fx, fy, H - 0.4, H, 0.015, m['black'], seg=12)
    cyl('fan_motor', fx, fy, H - 0.5, H - 0.38, 0.11, m['black'], seg=32)
    for k in range(5):
        a = k * 2 * math.pi / 5
        o = box(f'blade{k}', 0.12, -0.07, -0.006, 0.72, 0.07, 0.006, wood('blade', (0.32, 0.2, 0.12), rough=0.5), bevel=0.003)
        o.location = (fx, fy, H - 0.45)
        o.rotation_euler = (math.radians(8), 0, a)
    sphere('fan_glass', fx, fy, H - 0.55, 0.12, emitter('fan_bulb', 5.0, (1, 1, 1)), group='ceiling', scale=(1, 1, 0.55))
    point('fan_light', 'ceiling', fx, fy, H - 0.6, 140, radius=0.08)
    # string lights along the top of the left and far windows (Lamps group)
    bulb = emitter('string_bulb', 14.0)
    n = 0
    for (p0, p1) in [((0.08, 0.2), (0.08, D - 0.1)), ((0.1, D - 0.08), (W - 0.1, D - 0.08))]:
        L = math.dist(p0, p1)
        cnt = int(L / 0.32)
        for i in range(cnt + 1):
            t = i / cnt
            x = p0[0] + (p1[0] - p0[0]) * t
            y = p0[1] + (p1[1] - p0[1]) * t
            seg = (t * 3) % 1
            z = H - 0.32 - 0.12 * math.sin(math.pi * seg)
            sphere(f'sb{n}', x, y, z, 0.022, bulb, group='lamps', seg=10)
            n += 1
    point('string_fill1', 'lamps', 0.3, D / 2, H - 0.45, 30, radius=0.5)
    point('string_fill2', 'lamps', W / 2, D - 0.3, H - 0.45, 30, radius=0.5)
    # furniture: two armchairs, side table with lamp, plants
    wick = pbr('wicker', (0.36, 0.24, 0.14), rough=0.8, bump=0.8, bump_scale=90, var=0.2, var_scale=40)
    cream = pbr('cream', (0.78, 0.74, 0.64), rough=0.95, sheen=0.5, bump=0.15, bump_scale=200)
    for i, (cx, cy, rot) in enumerate([(1.0, 3.35, -20), (2.55, 3.65, 15)]):
        parts = [
            box(f'ch{i}_base', -0.42, -0.4, 0.08, 0.42, 0.4, 0.42, wick, bevel=0.03),
            box(f'ch{i}_back', -0.42, 0.25, 0.08, 0.42, 0.42, 0.9, wick, bevel=0.04),
            box(f'ch{i}_al', -0.45, -0.4, 0.08, -0.32, 0.42, 0.66, wick, bevel=0.04),
            box(f'ch{i}_ar', 0.32, -0.4, 0.08, 0.45, 0.42, 0.66, wick, bevel=0.04),
            box(f'ch{i}_seat', -0.32, -0.38, 0.42, 0.32, 0.25, 0.53, cream, bevel=0.05),
            box(f'ch{i}_bc', -0.32, 0.12, 0.45, 0.32, 0.28, 0.85, cream, bevel=0.06),
        ]
        for (lx, ly) in [(-0.38, -0.36), (0.34, -0.36), (-0.38, 0.34), (0.34, 0.34)]:
            parts.append(box(f'ch{i}_leg{lx}{ly}', lx, ly, 0, lx + 0.05, ly + 0.05, 0.08, wick))
        for p in parts:
            p.location = (cx, cy, 0)
            p.rotation_euler = (0, 0, math.radians(180 + rot))
    cyl('rtable_top', 1.85, 3.05, 0.55, 0.58, 0.3, pbr('rt_top', (0.85, 0.84, 0.8), rough=0.25, coat=0.6), seg=40)
    cyl('rtable_leg', 1.85, 3.05, 0.0, 0.55, 0.03, m['black'], seg=12)
    cyl('rtable_foot', 1.85, 3.05, 0.0, 0.02, 0.2, m['black'], seg=24)
    cyl('tl_base', 4.6, 3.95, 0.62, 0.92, 0.05, pbr('ceramic_blue', (0.18, 0.3, 0.42), rough=0.25), seg=24)
    box('stand', 4.35, 3.7, 0, 4.85, 4.2, 0.62, wood('stand', (0.42, 0.28, 0.16)), bevel=0.006)
    shade = pbr('shade2', (0.93, 0.9, 0.82), rough=0.9, translucent=0.65)
    cyl('tl_shade', 4.6, 3.95, 0.88, 1.12, 0.17, shade, seg=32)
    point('table_lamp', 'lamps', 4.6, 3.95, 1.0, 35, radius=0.04)
    terra = pbr('terracotta', (0.55, 0.26, 0.14), rough=0.8, var=0.15, var_scale=10)
    leaf = pbr('plant', (0.08, 0.2, 0.06), rough=0.55, var=0.3, var_scale=6, translucent=0.2)
    for i, (px, py, s) in enumerate([(0.35, 4.2, 1.0), (4.85, 1.95, 0.8), (0.3, 0.6, 1.2)]):
        cyl(f'pot{i}', px, py, 0, 0.34 * s, 0.17 * s, terra, seg=24)
        for k in range(9):
            a = k * 2.399
            lf = box(f'leaf{i}_{k}', -0.025 * s, -0.004, 0, 0.025 * s, 0.004, (0.45 + 0.35 * R.random()) * s, leaf, bevel=0.003)
            lf.location = (px + 0.05 * s * math.cos(a), py + 0.05 * s * math.sin(a), 0.3 * s)
            lf.rotation_euler = (math.radians(R.uniform(-14, 14)), math.radians(R.uniform(-14, 14)), a)
    # suns: far wall faces south, left wall east, right wall west
    sun('sun_am', 95, 24)
    sun('sun_noon', 170, 42)
    sun('sun_pm', 262, 18)
    cam = camera(4.35, 0.3, 1.4, yaw_deg=14, lens=17.0, shift_y=-0.1)
    return dict(name='Sunroom', ceiling='Ceiling fan light', lamps='Lamp and string lights', camera=cam)


ROOMS = {'garage': garage, 'basement': basement, 'sunroom': sunroom}
