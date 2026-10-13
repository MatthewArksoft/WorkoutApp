# Blender script: builds the isolated "DeskResetDemos" scene used by tools/rig.py.
# Imports the Quaternius Universal Base Character (CC0) from Assets/ and sets up camera, lights, floor and EEVEE.
# Safe to re-run: reuses existing datablocks. Never touches other scenes.
import bpy, math, os

ROOT = r"C:/Git Source Code/WorkoutApp"
GLTF = ROOT + "/Assets/Base Characters/Godot - UE/Superhero_Male_FullBody.gltf"

sc = bpy.data.scenes.get("DeskResetDemos") or bpy.data.scenes.new("DeskResetDemos")

# --- character ---
col = bpy.data.collections.get("DR_character")
if not col:
    col = bpy.data.collections.new("DR_character")
    sc.collection.children.link(col)
if not bpy.data.objects.get("Armature") or "SuperHero_Male" not in bpy.data.objects:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=GLTF)
    for o in [o for o in bpy.data.objects if o not in before]:
        for c in list(o.users_collection): c.objects.unlink(o)
        col.objects.link(o)
for n in ("Icosphere", "Eyebrows"):   # pack helper sphere; eyebrows aren't skinned to the rig
    if n in bpy.data.objects: bpy.data.objects[n].hide_render = True
arm = bpy.data.objects["Armature"]
arm.rotation_mode = 'XYZ'; arm.rotation_euler = (0, 0, math.radians(90))   # face +X

# --- floor ---
fl = bpy.data.objects.get("DR_floor")
if not fl:
    me = bpy.data.meshes.new("DR_floor")
    import bmesh
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=2.0); bm.to_mesh(me); bm.free()
    fl = bpy.data.objects.new("DR_floor", me); sc.collection.objects.link(fl)
fm = bpy.data.materials.get("DR_floor") or bpy.data.materials.new("DR_floor")
fm.use_nodes = True
b = fm.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.82, 0.84, 0.87, 1); b.inputs["Roughness"].default_value = 1.0
fl.data.materials.clear(); fl.data.materials.append(fm)
fl.scale = (20, 20, 0.01); fl.location = (0, 0, -0.01); fl.hide_render = False

# --- camera ---
cd = bpy.data.cameras.get("DR_cam") or bpy.data.cameras.new("DR_cam")
cd.type = 'ORTHO'; cd.clip_end = 100
cam = bpy.data.objects.get("DR_cam")
if not cam:
    cam = bpy.data.objects.new("DR_cam", cd); sc.collection.objects.link(cam)
sc.camera = cam

# --- world + lights ---
w = bpy.data.worlds.get("DR_world") or bpy.data.worlds.new("DR_world")
w.use_nodes = True
bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (1, 1, 1, 1); bg.inputs[1].default_value = 0.55
sc.world = w
def sun(name, energy, rot, angle):
    o = bpy.data.objects.get(name)
    if not o:
        o = bpy.data.objects.new(name, bpy.data.lights.new(name, 'SUN')); sc.collection.objects.link(o)
    o.data.energy = energy; o.data.angle = math.radians(angle)
    o.rotation_euler = [math.radians(a) for a in rot]
sun("DR_key", 2.2, (35, 0, -60), 25)
sun("DR_fill", 0.5, (60, 0, 150), 40)

# --- render ---
r = sc.render
engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
r.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in engines else 'BLENDER_EEVEE'
sc.eevee.taa_render_samples = 16
r.resolution_x, r.resolution_y, r.resolution_percentage = 480, 320, 100
r.film_transparent = False
r.image_settings.file_format = 'PNG'
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'

# --- characters: male (DR_character) and female (DR_character_f, hidden unless rig.set_character("f")) ---
def import_female():
    if "Armature_F" in bpy.data.objects: return
    col = bpy.data.collections.get("DR_character_f") or bpy.data.collections.new("DR_character_f")
    if col.name not in sc.collection.children: sc.collection.children.link(col)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=ROOT + "/Assets/Base Characters/Godot - UE/Superhero_Female_FullBody.gltf")
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        for c in list(o.users_collection): c.objects.unlink(o)
        col.objects.link(o)
    a = next(o for o in new if o.type == 'ARMATURE'); a.name = "Armature_F"
    next(o for o in new if o.type == 'MESH' and o.name.startswith("Superhero_Female")).name = "SuperHero_Female"
    a.rotation_mode = 'XYZ'; a.rotation_euler = (0, 0, math.radians(90))
    for o in new:
        if o.type == 'MESH' and o.name.startswith(("Icosphere", "Eyebrows")): o.hide_render = True   # eyebrows aren't skinned
    col.hide_render = col.hide_viewport = True

def mat(name, col, rough):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = col; b.inputs["Roughness"].default_value = rough
    return m

# Athletic kit painted in the skin shader from rest-pose position (Generated coords = undeformed mesh):
# hems are clean straight lines through the faces, and the skin mask (AOV) excludes everything covered.
# (name, colour, roughness, z from, z to, |x| from, |x| to) in rest-pose metres; later entries win.
CLOTH = {"shorts": ((0.030, 0.045, 0.085, 1), 0.75), "shoe": ((0.07, 0.08, 0.10, 1), 0.45),
         "sole": ((0.93, 0.93, 0.94, 1), 0.6), "sock": ((0.94, 0.94, 0.95, 1), 0.9)}
MALE_KIT = [("sock", 0.105, 0.175, 0, 9), ("shoe", -1, 0.105, 0, 9), ("sole", -1, 0.022, 0, 9), ("shorts", 0.695, 1.078, 0, 0.26)]      # top covers the texture's briefs band
FEMALE_KIT = [("sock", 0.10, 0.165, 0, 9), ("shoe", -1, 0.10, 0, 9), ("sole", -1, 0.02, 0, 9), ("shorts", 0.70, 1.06, 0, 0.26),
              ("shorts", 1.165, 1.37, 0, 0.145), ("shorts", 1.37, 1.47, 0.075, 0.11)]      # sports bra + straps

def kit_shader(body_name, kit):
    body = bpy.data.objects[body_name]; me = body.data
    for p_ in me.polygons: p_.material_index = 0
    m = me.materials[0]; nt = m.node_tree; N, L = nt.nodes, nt.links
    for n in [n for n in N if n.name.startswith("DR_k")]: N.remove(n)
    def node(t, name, **kw):
        n = N.new(t); n.name = "DR_k" + name
        for k, v in kw.items(): setattr(n, k, v)
        return n
    def math(op, a, b, name):
        n = node("ShaderNodeMath", name, operation=op)
        for i, v in enumerate((a, b)):
            if isinstance(v, (int, float)): n.inputs[i].default_value = v
            else: L.new(v, n.inputs[i])
        return n.outputs[0]
    me.use_auto_texspace = True
    loc, size = me.texspace_location, me.texspace_size
    tc = node("ShaderNodeTexCoord", "tc")
    sc_ = node("ShaderNodeVectorMath", "scale", operation='MULTIPLY_ADD')
    L.new(tc.outputs["Generated"], sc_.inputs[0]); sc_.inputs[1].default_value = tuple(2 * c for c in size)
    sc_.inputs[2].default_value = tuple(l - c for l, c in zip(loc, size))
    xyz = node("ShaderNodeSeparateXYZ", "xyz"); L.new(sc_.outputs[0], xyz.inputs[0])
    ax = math('ABSOLUTE', xyz.outputs["X"], 0, "ax"); z = xyz.outputs["Z"]
    bsdf = N["Principled BSDF"]
    col = N["DR_mul"].outputs[0]                                   # neutral skin (neutral_skin)
    sep = next((n for n in N if n.type == 'SEPARATE_COLOR'), None)  # roughness map channel
    rough = sep.outputs["Green"] if sep else None
    skin = None
    for i, (cloth, z0, z1, x0, x1) in enumerate(kit):
        mk = math('MULTIPLY', math('MULTIPLY', math('GREATER_THAN', z, z0, f"z0{i}"), math('LESS_THAN', z, z1, f"z1{i}"), f"mz{i}"),
                  math('MULTIPLY', math('GREATER_THAN', ax, x0 - 1e-4, f"x0{i}"), math('LESS_THAN', ax, x1, f"x1{i}"), f"mx{i}"), f"m{i}")
        c, r = CLOTH[cloth]
        mx = node("ShaderNodeMix", f"col{i}", data_type='RGBA'); L.new(mk, mx.inputs["Factor"])
        L.new(col, mx.inputs["A"]); mx.inputs["B"].default_value = c; col = mx.outputs["Result"]
        mr = node("ShaderNodeMix", f"rough{i}", data_type='FLOAT'); L.new(mk, mr.inputs["Factor"])
        if rough: L.new(rough, mr.inputs["A"])
        else: mr.inputs["A"].default_value = bsdf.inputs["Roughness"].default_value
        mr.inputs["B"].default_value = r; rough = mr.outputs["Result"]
        skin = math('SUBTRACT', 1.0, mk, f"s{i}") if skin is None else math('MULTIPLY', skin, math('SUBTRACT', 1.0, mk, f"s{i}"), f"sm{i}")
    L.new(col, bsdf.inputs["Base Color"]); L.new(rough, bsdf.inputs["Roughness"])
    L.new(skin, N["DR_aov"].inputs["Value"])

def dress(body_name, arm_name, hair_file):
    """Buzz-cut / buns hairstyle parented to the Head bone in the rest pose."""
    arm = bpy.data.objects[arm_name]; hname = "DR_hair" if arm_name == "Armature" else "DR_hair_f"
    if hname not in bpy.data.objects:
        for pb in arm.pose.bones: pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
        sc.view_layers[0].update()
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=ROOT + "/Assets/Hairstyles/Origin at 0/glTF (Godot)/" + hair_file)
        new = [o for o in bpy.data.objects if o not in before]
        col = arm.users_collection[0]
        for o in new:
            for c in list(o.users_collection): c.objects.unlink(o)
            col.objects.link(o)
        hair = next(o for o in new if o.type == 'MESH'); hair.name = hname
        sc.view_layers[0].update()
        M = arm.matrix_world @ hair.matrix_world
        hair.parent = arm; hair.parent_type = 'BONE'; hair.parent_bone = "Head"
        sc.view_layers[0].update(); hair.matrix_world = M
        for o in new:
            if o is not hair: bpy.data.objects.remove(o, do_unlink=True)
    hair = bpy.data.objects[hname]
    hair.data.materials.clear(); hair.data.materials.append(mat("DR_hair_mat", (0.045, 0.032, 0.024, 1), 0.65))

def neutral_skin(mat_name, albedo=0.9):
    """Skin keeps its texture detail but loses its hue: luminance x k, so the app can tint any skin tone.
    Also writes the 'skin' AOV (1 on skin) that becomes the tint mask."""
    import numpy as np
    m = bpy.data.materials[mat_name]; nt = m.node_tree; nodes = nt.nodes
    bsdf = nodes["Principled BSDF"]
    if "DR_bw" not in nodes:
        src = bsdf.inputs["Base Color"].links[0].from_socket
        bw = nodes.new("ShaderNodeRGBToBW"); bw.name = "DR_bw"
        mul = nodes.new("ShaderNodeMath"); mul.name = "DR_mul"; mul.operation = 'MULTIPLY'; mul.use_clamp = True
        nt.links.new(src, bw.inputs[0]); nt.links.new(bw.outputs[0], mul.inputs[0]); nt.links.new(mul.outputs[0], bsdf.inputs["Base Color"])
    img = next(n.image for n in nodes if n.type == 'TEX_IMAGE' and n.image and "Normal" not in n.image.name and "Roughness" not in n.image.name)
    px = np.array(img.pixels[:], dtype=np.float32).reshape(-1, 4)
    lum = px[:, 0] * 0.2126 + px[:, 1] * 0.7152 + px[:, 2] * 0.0722
    nodes["DR_mul"].inputs[1].default_value = albedo / float(np.percentile(lum[lum > 0.02], 50))
    aov = nodes.get("DR_aov") or nodes.new("ShaderNodeOutputAOV"); aov.name = "DR_aov"
    aov.aov_name = "skin"; aov.inputs["Value"].default_value = 1.0

def mask_pass():
    """Compositor: beauty to the normal output, the 'skin' AOV to a PNG per frame (rig.render_anim names it)."""
    vl = sc.view_layers[0]
    if "skin" not in [a.name for a in vl.aovs]:
        a = vl.aovs.add(); a.name = "skin"; a.type = 'VALUE'
    ng = bpy.data.node_groups.get("DR_comp") or bpy.data.node_groups.new("DR_comp", "CompositorNodeTree")
    ng.nodes.clear(); ng.interface.clear()
    ng.interface.new_socket("Image", in_out='OUTPUT', socket_type='NodeSocketColor')
    rl = ng.nodes.new("CompositorNodeRLayers"); rl.scene = sc; rl.layer = vl.name
    go = ng.nodes.new("NodeGroupOutput"); ng.links.new(rl.outputs["Image"], go.inputs[0])
    fo = ng.nodes.new("CompositorNodeOutputFile"); fo.name = "DR_mask"
    if hasattr(fo.format, "media_type"): fo.format.media_type = 'IMAGE'      # 5.x defaults to multilayer EXR
    fo.format.file_format = 'PNG'; fo.format.color_mode = 'BW'; fo.format.color_depth = '8'
    fo.file_output_items.new('FLOAT', "skin")
    ng.links.new(rl.outputs["skin"], fo.inputs["skin"])
    sc.compositing_node_group = ng
    sc.render.use_compositing = True
    return [s.name for s in rl.outputs]

import_female()
dress("SuperHero_Male", "Armature", "Hair_Buzzed.gltf")
dress("SuperHero_Female", "Armature_F", "Hair_Buns.gltf")
for _m in ("MI_Superhero_Male", "MI_Superhero_Female"): neutral_skin(_m)
kit_shader("SuperHero_Male", MALE_KIT); kit_shader("SuperHero_Female", FEMALE_KIT)
DRESS = {"comp": mask_pass()}
