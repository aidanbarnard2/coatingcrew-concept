"""Small scene-building kit for the floor visualizer rooms (Blender / Cycles, run headless through bpy).

Conventions: meters, Z up, floor at z=0. The camera sits near y=0 looking toward +Y, so +X is to the right in the picture.
Every light belongs to a light group; the site mixes the groups live, so each is rendered with plain white light.
"""
import math
import bpy
from mathutils import Vector, Matrix

GROUPS = ['sun_am', 'sun_noon', 'sun_pm', 'sky', 'ceiling', 'lamps']


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    s.cycles.device = 'CPU'
    vl = bpy.context.view_layer
    for g in GROUPS:
        vl.lightgroups.add(name=g)
    w = bpy.data.worlds.new('World')
    s.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (1, 1, 1, 1)
    bg.inputs['Strength'].default_value = 1.0
    w.lightgroup = 'sky'
    nt = w.node_tree
    lp = nt.nodes.new('ShaderNodeLightPath')
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY_ADD'
    mul.inputs[1].default_value = 1.5   # camera rays see the sky 2.5x brighter
    mul.inputs[2].default_value = 1.0
    nt.links.new(lp.outputs['Is Camera Ray'], mul.inputs[0])
    nt.links.new(mul.outputs[0], bg.inputs['Strength'])
    return s


# ---------------------------------------------------------------- materials
_mats = {}


def _principled(m):
    nt = m.node_tree
    return nt, nt.nodes['Principled BSDF'], nt.nodes['Material Output']


def pbr(name, color, rough=0.5, metal=0.0, var=0.0, var_scale=6.0, bump=0.0, bump_scale=300.0, spec=0.5,
        sheen=0.0, coat=0.0, translucent=0.0, emit=None):
    """Principled material with optional color variation (noise), fine bump, sheen and translucency."""
    if name in _mats:
        return _mats[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt, bs, out = _principled(m)
    L = nt.links
    bs.inputs['Base Color'].default_value = (*color, 1)
    bs.inputs['Roughness'].default_value = rough
    bs.inputs['Metallic'].default_value = metal
    bs.inputs['Specular IOR Level'].default_value = spec
    if sheen:
        bs.inputs['Sheen Weight'].default_value = sheen
    if coat:
        bs.inputs['Coat Weight'].default_value = coat
        bs.inputs['Coat Roughness'].default_value = 0.05
    if var:
        tc = nt.nodes.new('ShaderNodeTexCoord')
        nz = nt.nodes.new('ShaderNodeTexNoise')
        nz.inputs['Scale'].default_value = var_scale
        nz.inputs['Detail'].default_value = 6
        L.new(tc.outputs['Object'], nz.inputs['Vector'])
        mix = nt.nodes.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        mix.inputs['Factor'].default_value = 1.0
        a = tuple(max(0, c * (1 - var)) for c in color)
        b = tuple(min(1, c * (1 + var)) for c in color)
        mix.inputs['A'].default_value = (*a, 1)
        mix.inputs['B'].default_value = (*b, 1)
        L.new(nz.outputs['Fac'], mix.inputs['Factor'])
        L.new(mix.outputs['Result'], bs.inputs['Base Color'])
    if bump:
        tc = nt.nodes.new('ShaderNodeTexCoord')
        nz = nt.nodes.new('ShaderNodeTexNoise')
        nz.inputs['Scale'].default_value = bump_scale
        nz.inputs['Detail'].default_value = 2
        L.new(tc.outputs['Object'], nz.inputs['Vector'])
        bp = nt.nodes.new('ShaderNodeBump')
        bp.inputs['Strength'].default_value = bump
        bp.inputs['Distance'].default_value = 0.002
        L.new(nz.outputs['Fac'], bp.inputs['Height'])
        L.new(bp.outputs['Normal'], bs.inputs['Normal'])
    if translucent:
        tr = nt.nodes.new('ShaderNodeBsdfTranslucent')
        tr.inputs['Color'].default_value = (*color, 1)
        mx = nt.nodes.new('ShaderNodeMixShader')
        mx.inputs['Fac'].default_value = translucent
        L.new(bs.outputs['BSDF'], mx.inputs[1])
        L.new(tr.outputs['BSDF'], mx.inputs[2])
        L.new(mx.outputs['Shader'], out.inputs['Surface'])
    if emit is not None:
        bs.inputs['Emission Color'].default_value = (1, 1, 1, 1)
        bs.inputs['Emission Strength'].default_value = emit
    _mats[name] = m
    return m


def wood(name, color, ring_scale=3.0, rough=0.45, planks=None):
    """Wood: wave texture grain, optional plank seams along X."""
    if name in _mats:
        return _mats[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt, bs, out = _principled(m)
    L = nt.links
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (1, 12, 1)
    L.new(tc.outputs['Object'], mp.inputs['Vector'])
    wv = nt.nodes.new('ShaderNodeTexWave')
    wv.wave_type = 'BANDS'
    wv.bands_direction = 'X'
    wv.inputs['Scale'].default_value = ring_scale
    wv.inputs['Distortion'].default_value = 6
    wv.inputs['Detail'].default_value = 3
    L.new(mp.outputs['Vector'], wv.inputs['Vector'])
    cr = nt.nodes.new('ShaderNodeValToRGB')
    cr.color_ramp.elements[0].color = (*[c * 0.72 for c in color], 1)
    cr.color_ramp.elements[1].color = (*color, 1)
    L.new(wv.outputs['Fac'], cr.inputs['Fac'])
    L.new(cr.outputs['Color'], bs.inputs['Base Color'])
    bs.inputs['Roughness'].default_value = rough
    _mats[name] = m
    return m


def emitter(name, strength=1.0, color=(1, 1, 1)):
    if name in _mats:
        return _mats[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type == 'BSDF_PRINCIPLED':
            nt.nodes.remove(n)
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (*color, 1)
    em.inputs['Strength'].default_value = strength
    nt.links.new(em.outputs['Emission'], nt.nodes['Material Output'].inputs['Surface'])
    _mats[name] = m
    return m


def floor_material(mode):
    """mode 'A': matte 50% gray (the site divides it back out). mode 'B': black with a clear coat (reflections only).
    Both write the 'floor' AOV so the site knows which pixels are coated floor."""
    m = bpy.data.materials.new('Floor_' + mode)
    m.use_nodes = True
    nt, bs, out = _principled(m)
    if mode == 'A':
        bs.inputs['Base Color'].default_value = (0.5, 0.5, 0.5, 1)
        bs.inputs['Roughness'].default_value = 1.0
        bs.inputs['Specular IOR Level'].default_value = 0.0
    else:
        bs.inputs['Base Color'].default_value = (0, 0, 0, 1)
        bs.inputs['Roughness'].default_value = 0.07
        bs.inputs['Specular IOR Level'].default_value = 0.5
    a = nt.nodes.new('ShaderNodeOutputAOV')
    a.aov_name = 'floor'
    a.inputs['Value'].default_value = 1.0
    return m


# ---------------------------------------------------------------- geometry
def _obj(name, mesh, mat, group=None):
    o = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(o)
    if mat is not None:
        o.data.materials.append(mat)
    if group:
        o.lightgroup = group
    return o


def box(name, x0, y0, z0, x1, y1, z1, mat, bevel=0.0, group=None):
    """Axis-aligned box from corner (x0,y0,z0) to (x1,y1,z1)."""
    x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(v, [], f)
    me.update()
    o = _obj(name, me, mat, group)
    if bevel:
        b = o.modifiers.new('bev', 'BEVEL')
        b.width = bevel
        b.segments = 3
        b.limit_method = 'NONE'
        b.harden_normals = False
    return o


def cyl(name, x, y, z0, z1, r, mat, seg=32, group=None, axis='Z'):
    me = bpy.data.meshes.new(name)
    v, f = [], []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        v.append((r * math.cos(a), r * math.sin(a), 0))
        v.append((r * math.cos(a), r * math.sin(a), z1 - z0))
    for i in range(seg):
        j = (i + 1) % seg
        f.append((2 * i, 2 * j, 2 * j + 1, 2 * i + 1))
    f.append(tuple(2 * i for i in range(seg))[::-1])
    f.append(tuple(2 * i + 1 for i in range(seg)))
    me.from_pydata(v, [], f)
    for p in me.polygons:
        p.use_smooth = len(p.vertices) == 4
    me.update()
    o = _obj(name, me, mat, group)
    if axis == 'Z':
        o.location = (x, y, z0)
    elif axis == 'X':
        o.rotation_euler = (0, math.pi / 2, 0)
        o.location = (z0, x, y)
    elif axis == 'Y':
        o.rotation_euler = (-math.pi / 2, 0, 0)
        o.location = (x, z0, y)
    return o


def sphere(name, x, y, z, r, mat, group=None, seg=24, scale=(1, 1, 1)):
    me = bpy.data.meshes.new(name)
    v, f = [], []
    rings = seg // 2
    for i in range(rings + 1):
        th = math.pi * i / rings
        for j in range(seg):
            ph = 2 * math.pi * j / seg
            v.append((r * math.sin(th) * math.cos(ph), r * math.sin(th) * math.sin(ph), r * math.cos(th)))
    for i in range(rings):
        for j in range(seg):
            a = i * seg + j; b = i * seg + (j + 1) % seg
            f.append((a, b, b + seg, a + seg))
    me.from_pydata(v, [], f)
    for p in me.polygons:
        p.use_smooth = True
    me.update()
    o = _obj(name, me, mat, group)
    o.location = (x, y, z)
    o.scale = scale
    return o


def wall_x(name, x0, x1, y, t, h, mat, holes=(), inside=+1):
    """Wall running along X at depth y (thickness t going away from the room by `inside`), with rectangular holes
    given as (xa, xb, za, zb). Built from solid pieces so light passes through the holes."""
    ya, yb = (y, y + t) if inside > 0 else (y - t, y)
    pieces = []
    xs = sorted(set([x0, x1] + [h_[0] for h_ in holes] + [h_[1] for h_ in holes]))
    for i in range(len(xs) - 1):
        a, b = xs[i], xs[i + 1]
        zs = [(0, h)]
        for (xa, xb, za, zb) in holes:
            if xa <= a and b <= xb:
                zs = [(0, za), (zb, h)]
        for (za, zb) in zs:
            if zb - za > 1e-4:
                pieces.append(box(f'{name}_{i}_{za:.2f}', a, ya, za, b, yb, zb, mat))
    return pieces


def wall_y(name, y0, y1, x, t, h, mat, holes=(), inside=+1):
    """Wall running along Y at x; holes as (ya, yb, za, zb)."""
    xa, xb = (x, x + t) if inside > 0 else (x - t, x)
    pieces = []
    ys = sorted(set([y0, y1] + [h_[0] for h_ in holes] + [h_[1] for h_ in holes]))
    for i in range(len(ys) - 1):
        a, b = ys[i], ys[i + 1]
        zs = [(0, h)]
        for (ya, yb, za, zb) in holes:
            if ya <= a and b <= yb:
                zs = [(0, za), (zb, h)]
        for (za, zb) in zs:
            if zb - za > 1e-4:
                pieces.append(box(f'{name}_{i}_{za:.2f}', xa, a, za, xb, b, zb, mat))
    return pieces


def window_frame_y(name, x, ya, yb, za, zb, mat, depth=0.06, bars=1, mull=0, t=0.05):
    """Window frame in a wall along Y at x (frame members only, no glass)."""
    box(name + '_l', x - depth / 2, ya, za, x + depth / 2, ya + t, zb, mat)
    box(name + '_r', x - depth / 2, yb - t, za, x + depth / 2, yb, zb, mat)
    box(name + '_b', x - depth / 2, ya, za, x + depth / 2, yb, za + t, mat)
    box(name + '_t', x - depth / 2, ya, zb - t, x + depth / 2, yb, zb, mat)
    for i in range(1, bars + 1):
        z = za + (zb - za) * i / (bars + 1)
        box(f'{name}_h{i}', x - depth / 3, ya, z - 0.015, x + depth / 3, yb, z + 0.015, mat)
    for i in range(1, mull + 1):
        y = ya + (yb - ya) * i / (mull + 1)
        box(f'{name}_v{i}', x - depth / 3, y - 0.015, za, x + depth / 3, y + 0.015, zb, mat)


def window_frame_x(name, y, xa, xb, za, zb, mat, depth=0.06, bars=1, mull=0, t=0.05):
    box(name + '_l', xa, y - depth / 2, za, xa + t, y + depth / 2, zb, mat)
    box(name + '_r', xb - t, y - depth / 2, za, xb, y + depth / 2, zb, mat)
    box(name + '_b', xa, y - depth / 2, za, xb, y + depth / 2, za + t, mat)
    box(name + '_t', xa, y - depth / 2, zb - t, xb, y + depth / 2, zb, mat)
    for i in range(1, bars + 1):
        z = za + (zb - za) * i / (bars + 1)
        box(f'{name}_h{i}', xa, y - depth / 3, z - 0.015, xb, y + depth / 3, z + 0.015, mat)
    for i in range(1, mull + 1):
        xm = xa + (xb - xa) * i / (mull + 1)
        box(f'{name}_v{i}', xm - 0.015, y - depth / 3, za, xm + 0.015, y + depth / 3, zb, mat)


# ---------------------------------------------------------------- lights
def sun(group, azimuth_deg, elevation_deg, angle_deg=0.8):
    """azimuth: compass bearing the sun stands at (0 = north (-Y), 90 = east (-X), 180 = south (+Y), 270 = west (+X))."""
    az, el = math.radians(azimuth_deg), math.radians(elevation_deg)
    # direction from the scene toward the sun
    to_sun = Vector((-math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
    d = bpy.data.lights.new(group, 'SUN')
    d.energy = 1.0
    d.angle = math.radians(angle_deg)
    o = bpy.data.objects.new(group, d)
    bpy.context.scene.collection.objects.link(o)
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(to_sun)
    o.lightgroup = group
    return o


def area(name, group, x, y, z, sx, sy, power, normal=(0, 0, -1), portal=False, visible=False):
    d = bpy.data.lights.new(name, 'AREA')
    d.shape = 'RECTANGLE'
    d.size = sx
    d.size_y = sy
    d.energy = power
    if portal:
        d.cycles.is_portal = True
    o = bpy.data.objects.new(name, d)
    bpy.context.scene.collection.objects.link(o)
    o.location = (x, y, z)
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = Vector((0, 0, -1)).rotation_difference(Vector(normal))
    o.visible_camera = visible
    if group:
        o.lightgroup = group
    return o


def point(name, group, x, y, z, power, radius=0.05, spot=None, blend=0.6, aim=(0, 0, -1)):
    d = bpy.data.lights.new(name, 'SPOT' if spot else 'POINT')
    d.energy = power
    d.shadow_soft_size = radius
    if spot:
        d.spot_size = math.radians(spot)
        d.spot_blend = blend
    o = bpy.data.objects.new(name, d)
    bpy.context.scene.collection.objects.link(o)
    o.location = (x, y, z)
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = Vector((0, 0, -1)).rotation_difference(Vector(aim))
    o.visible_camera = False
    o.lightgroup = group
    return o


def portal(x, y, z, sx, sy, normal):
    """Window portal: tells Cycles to sample the sky through this opening (much less noise indoors)."""
    return area('portal', None, x, y, z, sx, sy, 0, normal=normal, portal=True)


# ---------------------------------------------------------------- camera
def camera(x, y, z, yaw_deg=0.0, lens=20.0, shift_y=-0.12, shift_x=0.0):
    c = bpy.data.cameras.new('cam')
    c.lens = lens
    c.sensor_width = 36
    c.sensor_fit = 'HORIZONTAL'
    c.shift_y = shift_y
    c.shift_x = shift_x
    c.clip_start = 0.05
    c.clip_end = 200
    o = bpy.data.objects.new('cam', c)
    bpy.context.scene.collection.objects.link(o)
    o.location = (x, y, z)
    o.rotation_euler = (math.pi / 2, 0, math.radians(yaw_deg))
    bpy.context.scene.camera = o
    return o


def floor_homography(cam, W, H, unit=3.28084):
    """3x3 matrix mapping image pixels (origin top-left, y down) to floor coordinates (feet, z=0 plane)."""
    import numpy as np
    c = cam.data
    f = c.lens / c.sensor_width * W
    cx = W / 2 - c.shift_x * W
    cy = H / 2 + c.shift_y * W
    M = np.array(cam.matrix_world.inverted())   # world -> camera
    R, t = M[:3, :3], M[:3, 3]
    Kp = np.array([[f, 0, -cx], [0, -f, -cy], [0, 0, -1.0]])
    Hw2p = Kp @ np.column_stack([R[:, 0], R[:, 1], t])
    Hp2w = np.linalg.inv(Hw2p)
    Hp2w = np.diag([unit, unit, 1.0]) @ Hp2w
    return Hp2w / np.abs(Hp2w).max()
