"""Build the 3D relics for the scan arena as .glb files. Run through Blender in background mode:

    blender -b --factory-startup -P scripts/blender/build_quest_assets.py -- ui/public/models

Each relic carries its own baked animation so the browser only plays it.
"""
import math
import os
import sys

import bpy
import bmesh

OUT = os.path.abspath(sys.argv[sys.argv.index('--') + 1])
FPS = 30


def fresh_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps = FPS
    bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'


def material(name, color, metal=0.0, rough=0.4, glow=None, glow_strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Metallic'].default_value = metal
    bsdf.inputs['Roughness'].default_value = rough
    if glow:
        bsdf.inputs['Emission Color'].default_value = (*glow, 1.0)
        bsdf.inputs['Emission Strength'].default_value = glow_strength
    return m


def assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    return obj


def shade_smooth(obj):
    for poly in obj.data.polygons:
        poly.use_smooth = True


def empty(name, location=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(e)
    e.location = location
    return e


def link_child(child, parent):
    bpy.context.view_layer.update()  # matrix_world is stale until the depsgraph runs
    world = child.matrix_world.copy()
    child.parent = parent
    child.matrix_parent_inverse = parent.matrix_world.inverted()
    child.matrix_world = world


def spin(obj, axis, frames, turns, name, loop=True):
    """Bake a linear rotation about one axis. Looping clips end on the start pose."""
    idx = 'XYZ'.index(axis)
    end = frames
    obj.rotation_euler = (0, 0, 0)
    obj.keyframe_insert('rotation_euler', frame=1)
    obj.rotation_euler[idx] = turns * 2 * math.pi
    obj.keyframe_insert('rotation_euler', frame=end)
    obj.animation_data.action.name = name
    bpy.context.scene.frame_end = max(bpy.context.scene.frame_end, end)


def export(name):
    path = os.path.join(OUT, f'{name}.glb')
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', export_animations=True, export_apply=True)
    print('wrote', path, os.path.getsize(path), 'bytes')


def build_coin():
    fresh_scene()
    gold = material('Gold', (1.0, 0.72, 0.25), metal=1.0, rough=0.22, glow=(1.0, 0.6, 0.15), glow_strength=0.4)
    body = bpy.ops.mesh.primitive_cylinder_add(vertices=72, radius=1.0, depth=0.16)
    coin = assign(bpy.context.object, gold)
    shade_smooth(coin)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.86, minor_radius=0.07, major_segments=72, minor_segments=12)
    rim = assign(bpy.context.object, gold)
    rim.location = (0, 0, 0.08)
    shade_smooth(rim)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.86, minor_radius=0.07, major_segments=72, minor_segments=12)
    rim2 = assign(bpy.context.object, gold)
    rim2.location = (0, 0, -0.08)
    shade_smooth(rim2)
    star = bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.34)
    emblem = assign(bpy.context.object, material('Emblem', (0.95, 0.5, 0.1), metal=1.0, rough=0.3))
    emblem.location = (0, 0, 0.1)
    emblem.scale = (1, 1, 0.25)
    face = empty('CoinFace')  # turns the coin so its face looks along -Y, toward the viewer
    face.rotation_euler = (math.radians(-90), 0, 0)
    root = empty('Coin')
    for o in (coin, rim, rim2, emblem):
        link_child(o, root)
    root.parent = face  # plain parent: keep the face rotation rather than preserving world pose
    root.matrix_parent_inverse.identity()
    spin(root, 'Z', frames=90, turns=1, name='Flip')
    export('coin')


def build_shield():
    fresh_scene()
    steel = material('Steel', (0.42, 0.7, 0.9), metal=0.9, rough=0.28)
    outline = [(-1.0, 1.1), (1.0, 1.1), (1.0, 0.2), (0.55, -0.55), (0.0, -1.45), (-0.55, -0.55), (-1.0, 0.2)]
    mesh = bpy.data.meshes.new('ShieldMesh')
    mesh.from_pydata([(x, 0, y) for x, y in outline], [], [list(range(len(outline)))])
    mesh.update()
    shield = bpy.data.objects.new('Shield', mesh)
    bpy.context.collection.objects.link(shield)
    assign(shield, steel)
    bpy.context.view_layer.objects.active = shield
    shield.select_set(True)
    solid = shield.modifiers.new('Thick', 'SOLIDIFY')
    solid.thickness = 0.22
    bevel = shield.modifiers.new('Soft', 'BEVEL')
    bevel.width = 0.05
    bevel.segments = 3
    for mod in list(shield.modifiers):
        bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.36, minor_radius=0.06, major_segments=48, minor_segments=12)
    ring = assign(bpy.context.object, material('Lock', (0.6, 1.0, 0.8), metal=0.0, rough=0.3, glow=(0.2, 1.0, 0.6), glow_strength=1.5))
    ring.location = (0, -0.16, 0.1)
    ring.rotation_euler = (math.radians(90), 0, 0)
    export('shield')


def build_whale():
    fresh_scene()
    blue = material('Whale', (0.2, 0.42, 0.75), metal=0.1, rough=0.45)
    pale = material('Belly', (0.85, 0.92, 1.0), metal=0.0, rough=0.5)
    eye = material('Eye', (0.02, 0.02, 0.05), metal=0.0, rough=0.2)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1.0)
    body = assign(bpy.context.object, blue)
    body.scale = (1.5, 0.62, 0.62)
    shade_smooth(body)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1.0)
    belly = assign(bpy.context.object, pale)
    belly.scale = (1.2, 0.5, 0.36)
    belly.location = (0, 0, -0.22)
    shade_smooth(belly)
    parts = [body, belly]
    for side in (1, -1):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=10, radius=1.0)
        fluke = assign(bpy.context.object, blue)
        fluke.scale = (0.5, 0.06, 0.32)
        fluke.location = (-1.55, 0, 0)
        fluke.rotation_euler = (0, math.radians(side * 38), 0)
        shade_smooth(fluke)
        parts.append(fluke)
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.2, depth=0.5)
    fin = assign(bpy.context.object, blue)
    fin.location = (0.1, 0, 0.6)
    parts.append(fin)
    for side in (1, -1):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.09)
        e = assign(bpy.context.object, eye)
        e.location = (1.02, side * 0.36, 0.12)
        parts.append(e)
    root = empty('Whale')
    for o in parts:
        link_child(o, root)
    root.location = (0, 0, 0)
    root.keyframe_insert('location', frame=1)
    root.location.z = 0.22
    root.keyframe_insert('location', frame=FPS)
    root.location.z = 0
    root.keyframe_insert('location', frame=FPS * 2)
    root.rotation_euler = (0, 0, math.radians(-7))
    root.keyframe_insert('rotation_euler', frame=1)
    root.rotation_euler = (0, 0, math.radians(7))
    root.keyframe_insert('rotation_euler', frame=FPS)
    root.rotation_euler = (0, 0, math.radians(-7))
    root.keyframe_insert('rotation_euler', frame=FPS * 2)
    root.animation_data.action.name = 'Swim'
    bpy.context.scene.frame_end = FPS * 2
    export('whale')


def build_radar():
    fresh_scene()
    steel = material('Steel', (0.6, 0.66, 0.74), metal=0.8, rough=0.35)
    dish_mat = material('Dish', (0.78, 0.9, 1.0), metal=0.7, rough=0.25)
    glow = material('Beam', (0.36, 0.88, 1.0), glow=(0.36, 0.88, 1.0), glow_strength=3.0)
    bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=0.7, depth=0.18, location=(0, 0, 0.09))
    base = assign(bpy.context.object, steel)
    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.12, depth=1.6, location=(0, 0, 0.98))
    mast = assign(bpy.context.object, steel)
    pivot = empty('Sweep', location=(0, 0, 1.8))
    bpy.ops.mesh.primitive_uv_sphere_add(segments=40, ring_count=20, radius=1.0, location=(0, 0, 0))
    dish = assign(bpy.context.object, dish_mat)
    dish.scale = (0.95, 0.95, 0.22)
    dish.rotation_euler = (math.radians(-40), 0, 0)
    shade_smooth(dish)
    bpy.ops.mesh.primitive_cone_add(vertices=20, radius1=0.08, radius2=0.02, depth=0.8, location=(0, 0.5, 0.22))
    feed = assign(bpy.context.object, steel)
    feed.rotation_euler = (math.radians(-90), 0, 0)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.09, location=(0, 0.78, 0.34))
    lamp = assign(bpy.context.object, glow)
    for o in (dish, feed, lamp):
        link_child(o, pivot)
    spin(pivot, 'Z', frames=120, turns=1, name='Sweep')
    export('radar')


def build_chest():
    fresh_scene()
    wood = material('Oak', (0.42, 0.22, 0.09), metal=0.0, rough=0.7)
    gold = material('Gold', (1.0, 0.72, 0.25), metal=1.0, rough=0.25, glow=(1.0, 0.6, 0.15), glow_strength=0.3)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.8))
    base = assign(bpy.context.object, wood)
    base.scale = (1.2, 0.8, 0.8)
    hinge = empty('Lid', location=(0, 0.8, 1.6))
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 1.8))  # world position: sits on the base
    lid = assign(bpy.context.object, wood)
    lid.scale = (1.2, 0.8, 0.2)
    link_child(lid, hinge)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.8))
    band = assign(bpy.context.object, gold)
    band.scale = (0.22, 0.84, 0.82)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.8))
    band2 = assign(bpy.context.object, gold)
    band2.scale = (1.24, 0.84, 0.08)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=0.35, location=(0, 0, 1.5))
    loot = assign(bpy.context.object, material('Loot', (1.0, 0.9, 0.5), glow=(1.0, 0.85, 0.4), glow_strength=2.0))
    link_child(band, base)
    link_child(band2, base)
    link_child(loot, base)
    link_child(base, empty('Chest'))
    hinge.rotation_euler = (0, 0, 0)
    hinge.keyframe_insert('rotation_euler', frame=1)
    hinge.rotation_euler = (math.radians(-105), 0, 0)
    hinge.keyframe_insert('rotation_euler', frame=40)
    hinge.animation_data.action.name = 'Open'
    bpy.context.scene.frame_end = 40
    export('chest')


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    build_coin()
    build_shield()
    build_whale()
    build_radar()
    build_chest()
