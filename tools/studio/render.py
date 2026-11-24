"""Render one room's light passes.

    python3 render.py ROOM MODE WIDTH SAMPLES OUTDIR [border x0 y0 x1 y1]

MODE A: matte gray floor -> one EXR layer per light group (+ the floor mask) and meta.json.
MODE B: clear-coated black floor -> reflection layers per light group (optionally only inside a border).
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import lib  # noqa: E402
import rooms3d  # noqa: E402

room, mode, width, spp, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
border = [float(v) for v in sys.argv[7:11]] if len(sys.argv) > 6 and sys.argv[6] == 'border' else None
os.makedirs(out, exist_ok=True)

s = lib.reset()
info = rooms3d.ROOMS[room](mode)
W, H = width, int(round(width * 2 / 3))
r = s.render
r.resolution_x, r.resolution_y, r.resolution_percentage = W, H, 100
r.film_transparent = False
c = s.cycles
c.samples = spp
c.use_adaptive_sampling = True
c.adaptive_threshold = 0.02
c.use_denoising = False
c.max_bounces = 8
c.diffuse_bounces = 4
c.glossy_bounces = 3
c.transmission_bounces = 4
c.transparent_max_bounces = 8
c.sample_clamp_indirect = 6.0
c.caustics_reflective = False
c.caustics_refractive = False
c.blur_glossy = 1.0
c.use_light_tree = True
c.seed = 3
s.view_settings.view_transform = 'Standard'
vl = bpy.context.view_layer
vl.cycles.denoising_store_passes = True
aov = vl.aovs.add()
aov.name = 'floor'
aov.type = 'VALUE'
if border:
    r.use_border = True
    r.use_crop_to_border = True
    r.border_min_x, r.border_min_y, r.border_max_x, r.border_max_y = border

ng = bpy.data.node_groups.new('Comp', 'CompositorNodeTree')
s.compositing_node_group = ng
rl = ng.nodes.new('CompositorNodeRLayers')
fo = ng.nodes.new('CompositorNodeOutputFile')
fo.directory = out
fo.file_name = f'{room}_{mode}'
fo.format.file_format = 'OPEN_EXR_MULTILAYER'
fo.format.color_depth = '32'
for g in lib.GROUPS:
    dn = ng.nodes.new('CompositorNodeDenoise')
    ng.links.new(rl.outputs['Combined_' + g], dn.inputs['Image'])
    ng.links.new(rl.outputs['Denoising Albedo'], dn.inputs['Albedo'])
    ng.links.new(rl.outputs['Denoising Normal'], dn.inputs['Normal'])
    fo.file_output_items.new('RGBA', g)
    ng.links.new(dn.outputs['Image'], fo.inputs[g])
fo.file_output_items.new('FLOAT', 'floor')
ng.links.new(rl.outputs['floor'], fo.inputs['floor'])

t0 = time.time()
bpy.ops.render.render(write_still=False)
print(f'RENDERED {room} {mode} {W}x{H} spp={spp} in {time.time() - t0:.0f}s')

if mode == 'A':
    Hm = lib.floor_homography(info['camera'], W, H)
    json.dump(dict(name=info['name'], ceiling=info['ceiling'], lamps=info['lamps'], W=W, H=H,
                   floor=[float(v) for v in Hm.ravel()]), open(os.path.join(out, f'{room}_meta.json'), 'w'), indent=1)
