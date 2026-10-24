"""Render the nine looping 3D backdrops behind the cinema reels, one PNG sequence per reel.

    blender -b --factory-startup -P scripts/blender/render_reels.py -- <out_dir> [reel_id ...]

Every reel is a seamless loop of P frames at FPS. Procedural keys are sampled over one period
and the baked GLB clips get cycle modifiers, so each sequence wraps cleanly. Encode the PNG
sequences with ffmpeg afterwards (the HyperFrames step adds the overlay).
"""
import math
import os
import random
import sys
import time

import bpy

ARGS = sys.argv[sys.argv.index('--') + 1:]
OUT = os.path.abspath(ARGS[0])
ONLY = set(ARGS[1:])
MODELS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'ui', 'public', 'models')
FPS = 24
P = 96  # frames per loop: 4 s at 24 fps
WIDTH, HEIGHT = 960, 540
TAU = 2 * math.pi

GOLD = (0.96, 0.71, 0.26)
CYAN = (0.36, 0.88, 1.0)
GREEN = (0.18, 0.90, 0.62)
RED = (1.0, 0.30, 0.43)


def material(name, color, metal=0.0, rough=0.4, glow=None, strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Metallic'].default_value = metal
    bsdf.inputs['Roughness'].default_value = rough
    if glow:
        bsdf.inputs['Emission Color'].default_value = (*glow, 1.0)
    bsdf.inputs['Emission Strength'].default_value = strength
    return m


def emission(mat):
    return mat.node_tree.nodes['Principled BSDF'].inputs['Emission Strength']


def prim(kind, loc, scale, mat):
    if kind == 'cube':
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    elif kind == 'cyl':
        bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=1, location=loc, vertices=32)
    elif kind == 'sphere':
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=loc, segments=32, ring_count=16)
    elif kind == 'torus':
        bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.04, location=loc, major_segments=96)
    o = bpy.context.active_object
    o.scale = scale
    o.data.materials.append(mat)
    return o


def light(name, kind, loc, color, energy, spot_deg=40.0):
    d = bpy.data.lights.new(name, kind)
    d.color = color
    d.energy = energy
    if kind == 'SPOT':
        d.spot_size = math.radians(spot_deg)
        d.spot_blend = 0.5
    o = bpy.data.objects.new(name, d)
    bpy.context.collection.objects.link(o)
    o.location = loc
    return o


def loop(owner, attr, fn, index=-1, step=6):
    """Key attr over one loop. fn(phase) returns a tuple for a whole vector, or a scalar for
    component index (or the whole value when index < 0). Keys run frames 1..P+1; P+1 equals frame 1."""
    for f in range(1, P + 2, step):
        v = fn(((f - 1) % P) / P)
        if isinstance(v, tuple):
            setattr(owner, attr, v)
            owner.keyframe_insert(data_path=attr, frame=f)
        elif index >= 0:
            getattr(owner, attr)[index] = v
            owner.keyframe_insert(data_path=attr, index=index, frame=f)
        else:
            setattr(owner, attr, v)
            owner.keyframe_insert(data_path=attr, frame=f)


def wrap_baked_clips():
    """Loop every baked GLB clip: its curves repeat from their first key."""
    for action in bpy.data.actions:
        for layer in action.layers:
            for strip in layer.strips:
                for slot in action.slots:
                    cb = strip.channelbag(slot)
                    if cb:
                        for fc in cb.fcurves:
                            fc.modifiers.new('CYCLES')


def import_glb(name):
    before = set(o.name for o in bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(MODELS, f'{name}.glb'))
    wrap_baked_clips()
    return [o for o in bpy.data.objects if o.name not in before and o.parent is None]


def stage(accent):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x, sc.render.resolution_y = WIDTH, HEIGHT
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 1, P
    sc.view_settings.view_transform = 'Standard'
    sc.eevee.taa_render_samples = 16
    world = bpy.data.worlds.new('World')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.006, 0.006, 0.01, 1)
    sc.world = world
    prim('cube', (0, 0, -0.05), (30, 30, 0.1), material('Floor', (0.02, 0.02, 0.025), rough=0.5))

    pivot = bpy.data.objects.new('Pivot', None)
    bpy.context.collection.objects.link(pivot)
    pivot.location = (0, 0, 1.0)
    loop(pivot, 'rotation_euler', lambda ph: (0, 0, math.radians(4) * math.sin(TAU * ph)))
    cam_d = bpy.data.cameras.new('Cam')
    cam_d.lens = 50
    cam = bpy.data.objects.new('Cam', cam_d)
    bpy.context.collection.objects.link(cam)
    cam.parent = pivot
    cam.location = (0, -7.5, 0.6)
    cam.rotation_euler = (math.radians(84), 0, 0)
    sc.camera = cam

    key = light('Key', 'SPOT', (0, -2.5, 6), (1, 0.97, 0.92), 2600.0)
    key.rotation_euler = (math.radians(12), 0, 0)
    rim = light('Rim', 'SPOT', (3.5, 4.0, 4.5), accent, 1600.0, 36.0)
    rim.rotation_euler = (math.radians(-120), 0, math.radians(35))
    light('Fill', 'SUN', (0, 0, 0), (0.7, 0.8, 1.0), 0.6)


def coin():
    for r in import_glb('coin'):
        r.location.z += 1.0
    ring = prim('torus', (0, 0, 1.0), (1.4, 1.4, 1.4), material('Ring', GOLD, glow=GOLD, strength=2.5))
    loop(ring, 'rotation_euler', lambda ph: (math.radians(90), 0, TAU * ph))


def gatekeeper():
    for r in import_glb('shield'):
        r.location.z += 0.2
    red = material('Lamp', RED, glow=RED, strength=6.0)
    prim('sphere', (0, -0.35, 2.9), (0.09, 0.09, 0.09), red)
    loop(emission(red), 'default_value', lambda ph: 3.0 + 3.0 * math.sin(TAU * ph))
    for side in (-1, 1):
        gate = prim('cube', (side * 1.9, -0.55, 1.5), (0.22, 0.12, 2.8), material('Gate', (0.2, 0.22, 0.26), metal=0.9, rough=0.3))
        loop(gate, 'location', lambda ph, s=side: (s * (2.4 - 0.9 * (0.5 + 0.5 * math.sin(TAU * ph))), -0.55, 1.5))


def holders():
    for r in import_glb('whale'):
        r.location = (0, 0.2, 1.0)
    rng = random.Random(7)
    coin_mat = material('Stack', GOLD, metal=1.0, rough=0.25)
    for i in range(5):
        for j in range(5):
            x, y = -1.6 + i * 0.8, -2.2 + j * 0.25
            amp = rng.uniform(0.05, 0.5)
            phase = rng.uniform(0, TAU)
            height = lambda ph, a=amp, p=phase: 0.05 + a * (0.5 + 0.5 * math.sin(TAU * ph + p))
            stack = prim('cyl', (x, y, 0.1), (0.3, 0.3, 0.05), coin_mat)
            loop(stack, 'scale', lambda ph, h=height: (0.3, 0.3, h(ph)))
            loop(stack, 'location', lambda ph, h=height, xx=x, yy=y: (xx, yy, h(ph)))


def traders():
    rng = random.Random(3)
    for i in range(28):
        x = -3.4 + i * 0.25
        col = GREEN if rng.random() > 0.4 else RED
        mat = material(f'Tick{i}', col, glow=col, strength=3.0)
        k = rng.choice([1, 2, 3])
        phase = rng.uniform(0, TAU)
        level = lambda ph, kk=k, p=phase: 0.5 + 0.5 * math.sin(TAU * kk * ph + p)
        bar = prim('cube', (x, 0, 0.9), (0.09, 0.09, 0.4), mat)
        loop(bar, 'scale', lambda ph, lv=level: (0.09, 0.09, 0.2 + 0.9 * lv(ph)))
        loop(bar, 'location', lambda ph, lv=level, xx=x: (xx, 0, 0.2 + 0.45 * lv(ph)))
    prim('cube', (0, 0.05, 0.02), (4.0, 0.05, 0.02), material('Belt', CYAN, glow=CYAN, strength=1.5))


def kline():
    rng = random.Random(11)
    for i in range(14):
        x = -3.0 + i * 0.46
        col = GREEN if rng.random() > 0.45 else RED
        body_mat = material(f'Body{i}', col, glow=col, strength=1.2)
        wick_mat = material(f'Wick{i}', (0.6, 0.6, 0.65), metal=0.2, rough=0.5)
        h = rng.uniform(0.6, 1.6)
        amp = rng.uniform(0.2, 0.7)
        phase = rng.uniform(0, TAU)
        length = lambda ph, hh=h, a=amp, p=phase: hh + a * math.sin(TAU * ph + p)
        prim('cube', (x, 0, 1.1), (0.02, 0.02, 1.4), wick_mat)
        body = prim('cube', (x, 0, 1.1), (0.18, 0.04, h / 2), body_mat)
        loop(body, 'scale', lambda ph, ln=length: (0.18, 0.04, ln(ph) / 2))
        loop(body, 'location', lambda ph, ln=length, xx=x: (xx, 0, 0.6 + ln(ph) / 4))
    light('Chart', 'SPOT', (0, -4, 4), GOLD, 900.0, 50.0)


def smart_money():
    for r in import_glb('radar'):
        r.location.z += 0.2
    for i in range(6):
        mat = material(f'Pulse{i}', CYAN, glow=CYAN, strength=4.0)
        ring = prim('torus', (0, 0, 0.3), (0.7, 0.7, 0.7), mat)
        off = i / 6
        loop(ring, 'scale', lambda ph, o=off: (0.5 + 2.2 * ((ph + o) % 1.0),) * 3)
        loop(emission(mat), 'default_value', lambda ph, o=off: 6.0 * (1 - (ph + o) % 1.0) ** 2)


def kol():
    rng = random.Random(5)
    for i in range(9):
        x = -3.2 + i * 0.8
        glow = material(f'Lit{i}', GOLD, glow=GOLD, strength=0.0)
        prim('cyl', (x, 0, 0.6), (0.22, 0.22, 0.6), glow)
        prim('sphere', (x, 0, 1.5), (0.16, 0.16, 0.16), glow)
        p = rng.uniform(0, TAU)
        loop(emission(glow), 'default_value', lambda ph, pp=p: 5.0 * max(0.0, math.sin(TAU * ph + pp)) ** 3)
    spot = light('Warm', 'SPOT', (0, -3, 5), GOLD, 1400.0, 60.0)
    spot.rotation_euler = (math.radians(15), 0, 0)


def agent():
    core_mat = material('Core', CYAN, glow=CYAN, strength=6.0)
    prim('sphere', (0, 0, 1.2), (0.45, 0.45, 0.45), core_mat)
    loop(emission(core_mat), 'default_value', lambda ph: 4.0 + 3.0 * math.sin(TAU * ph))
    for i, (tilt, lean) in enumerate([(90, 0), (60, 30), (30, 60)]):
        size = 0.9 + 0.25 * i
        ring = prim('torus', (0, 0, 1.2), (size, size, size), material(f'Orbit{i}', CYAN, glow=CYAN, strength=2.0))
        loop(ring, 'rotation_euler', lambda ph, t=tilt, l=lean, k=i + 1: (math.radians(t), math.radians(l), TAU * k * ph))


def verdict():
    for r in import_glb('chest'):
        r.location = (0, 0, 0)
    beam_mat = material('Beam', GREEN, glow=GREEN, strength=2.0)
    prim('cyl', (0, 0, 2.8), (0.12, 0.12, 2.0), beam_mat)
    loop(emission(beam_mat), 'default_value', lambda ph: 1.0 + 1.5 * (0.5 + 0.5 * math.sin(TAU * ph)))
    inner = light('Inside', 'POINT', (0, 0.2, 0.8), GREEN, 600.0)
    loop(inner.data, 'energy', lambda ph: 300 + 400 * (0.5 + 0.5 * math.sin(TAU * ph)))


BUILDERS = {
    'token_info': (GOLD, coin),
    'security': (RED, gatekeeper),
    'holders': (CYAN, holders),
    'traders': (GREEN, traders),
    'kline': (GOLD, kline),
    'smart_money': (CYAN, smart_money),
    'kol': (GOLD, kol),
    'agent': (CYAN, agent),
    'verdict': (GREEN, verdict),
}


def render_reel(reel_id, accent, build):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    stage(accent)
    build()
    folder = os.path.join(OUT, reel_id)
    os.makedirs(folder, exist_ok=True)
    sc = bpy.context.scene
    sc.render.image_settings.file_format = 'PNG'
    sc.render.filepath = os.path.join(folder, 'f_')
    t = time.time()
    bpy.ops.render.render(animation=True)
    print(f'REEL {reel_id} frames={P} sec={round(time.time() - t, 1)}', flush=True)


for reel_id, (accent, build) in BUILDERS.items():
    if ONLY and reel_id not in ONLY:
        continue
    render_reel(reel_id, accent, build)
