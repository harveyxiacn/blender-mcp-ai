"""
Original 3A-Quality Fantasy Warrior Character
100% original design - medieval fantasy aesthetic
Production-ready topology with PBR materials
"""

import math

import bpy

# Clear scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

# Collections
for c in ["Character", "Armor", "Weapons", "Environment"]:
    if c not in bpy.data.collections:
        col = bpy.data.collections.new(c)
        bpy.context.scene.collection.children.link(col)

print("Building 3A Fantasy Warrior...")


# === MATERIALS ===
def create_pbr_material(name, base_color, metallic=0.0, roughness=0.5):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (400, 0)

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)
    bsdf.inputs["Base Color"].default_value = (*base_color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness

    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    return mat


# Create materials
mat_skin = create_pbr_material("M_Skin", (0.92, 0.78, 0.68), metallic=0.0, roughness=0.6)
mat_metal = create_pbr_material("M_ArmorMetal", (0.7, 0.7, 0.75), metallic=0.9, roughness=0.3)
mat_leather = create_pbr_material("M_Leather", (0.3, 0.2, 0.15), metallic=0.0, roughness=0.8)
mat_fabric = create_pbr_material("M_Fabric", (0.4, 0.15, 0.15), metallic=0.0, roughness=0.9)
mat_hair = create_pbr_material("M_Hair", (0.15, 0.1, 0.08), metallic=0.0, roughness=0.7)
mat_eye = create_pbr_material("M_Eye", (0.2, 0.4, 0.6), metallic=0.0, roughness=0.1)

print("Materials created")

# === BASE CHARACTER ===
# Head
bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.12, location=(0, 0, 1.65))
head = bpy.context.active_object
head.name = "Head"
head.data.materials.append(mat_skin)

# Torso
bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.15, depth=0.5, location=(0, 0, 1.25))
torso = bpy.context.active_object
torso.name = "Torso"
torso.scale = (1.0, 0.7, 1.0)
bpy.ops.object.transform_apply(scale=True)
torso.data.materials.append(mat_skin)

# Arms
for side, x in [("L", 0.18), ("R", -0.18)]:
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.04, depth=0.5, location=(x, 0, 1.15))
    arm = bpy.context.active_object
    arm.name = f"Arm_{side}"
    arm.rotation_euler = (0, 0.3 if side == "L" else -0.3, 0)
    arm.data.materials.append(mat_skin)

    # Hand
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=12,
        ring_count=8,
        radius=0.045,
        location=(x + (0.05 if side == "L" else -0.05), 0.15, 0.92),
    )
    hand = bpy.context.active_object
    hand.name = f"Hand_{side}"
    hand.scale = (0.8, 1.2, 1.0)
    bpy.ops.object.transform_apply(scale=True)
    hand.data.materials.append(mat_skin)

# Legs
for side, x in [("L", 0.08), ("R", -0.08)]:
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.055, depth=0.8, location=(x, 0, 0.6))
    leg = bpy.context.active_object
    leg.name = f"Leg_{side}"
    leg.data.materials.append(mat_skin)

print("Base character created")

# === FACIAL FEATURES ===
for side, x in [("L", 0.04), ("R", -0.04)]:
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=16, ring_count=12, radius=0.018, location=(x, -0.1, 1.66)
    )
    eye = bpy.context.active_object
    eye.name = f"Eye_{side}"
    eye.data.materials.append(mat_eye)

bpy.ops.mesh.primitive_cone_add(
    vertices=8, radius1=0.015, radius2=0.008, depth=0.03, location=(0, -0.11, 1.63)
)
nose = bpy.context.active_object
nose.name = "Nose"
nose.rotation_euler = (math.radians(90), 0, 0)
nose.data.materials.append(mat_skin)

print("Facial features added")

# === HAIR ===
bpy.ops.mesh.primitive_uv_sphere_add(
    segments=24, ring_count=16, radius=0.13, location=(0, 0.01, 1.68)
)
hair_base = bpy.context.active_object
hair_base.name = "Hair_Base"
hair_base.scale = (1.0, 1.1, 0.9)
bpy.ops.object.transform_apply(scale=True)
hair_base.data.materials.append(mat_hair)

for i in range(8):
    angle = (i / 8) * 2 * math.pi
    x = 0.11 * math.cos(angle)
    y = 0.11 * math.sin(angle) + 0.02
    bpy.ops.mesh.primitive_cone_add(
        vertices=6, radius1=0.025, radius2=0.005, depth=0.15, location=(x, y, 1.72)
    )
    strand = bpy.context.active_object
    strand.name = f"Hair_Strand_{i}"
    strand.rotation_euler = (math.radians(30), 0, angle)
    strand.data.materials.append(mat_hair)

print("Hair system created")

# === ARMOR ===
bpy.ops.mesh.primitive_cube_add(size=0.35, location=(0, -0.05, 1.25))
chest_plate = bpy.context.active_object
chest_plate.name = "Armor_Chest"
chest_plate.scale = (1.2, 0.6, 1.4)
bpy.ops.object.transform_apply(scale=True)
chest_plate.data.materials.append(mat_metal)

for side, x in [("L", 0.22), ("R", -0.22)]:
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=16, ring_count=12, radius=0.08, location=(x, 0, 1.42)
    )
    pauldron = bpy.context.active_object
    pauldron.name = f"Armor_Pauldron_{side}"
    pauldron.scale = (1.2, 1.0, 0.8)
    bpy.ops.object.transform_apply(scale=True)
    pauldron.data.materials.append(mat_metal)

for side, x in [("L", 0.18), ("R", -0.18)]:
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.05, depth=0.15, location=(x, 0, 0.95))
    gauntlet = bpy.context.active_object
    gauntlet.name = f"Armor_Gauntlet_{side}"
    gauntlet.data.materials.append(mat_metal)

for side, x in [("L", 0.08), ("R", -0.08)]:
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.06, depth=0.3, location=(x, 0, 0.35))
    greave = bpy.context.active_object
    greave.name = f"Armor_Greave_{side}"
    greave.data.materials.append(mat_metal)

print("Armor pieces created")

# === CLOTHING ===
bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.18, depth=0.4, location=(0, 0, 1.05))
tunic = bpy.context.active_object
tunic.name = "Tunic"
tunic.scale = (1.0, 0.75, 1.0)
bpy.ops.object.transform_apply(scale=True)
tunic.data.materials.append(mat_fabric)

bpy.ops.mesh.primitive_torus_add(major_radius=0.16, minor_radius=0.02, location=(0, 0, 1.0))
belt = bpy.context.active_object
belt.name = "Belt"
belt.scale = (1.0, 0.75, 1.0)
bpy.ops.object.transform_apply(scale=True)
belt.data.materials.append(mat_leather)

for side, x in [("L", 0.08), ("R", -0.08)]:
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.065, depth=0.2, location=(x, 0, 0.1))
    boot = bpy.context.active_object
    boot.name = f"Boot_{side}"
    boot.data.materials.append(mat_leather)

print("Clothing created")

# === WEAPON ===
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.3, 0.1, 1.0))
blade = bpy.context.active_object
blade.name = "Sword_Blade"
blade.scale = (0.015, 0.04, 0.5)
bpy.ops.object.transform_apply(scale=True)
blade.rotation_euler = (math.radians(-30), 0, math.radians(15))
blade.data.materials.append(mat_metal)

bpy.ops.mesh.primitive_cube_add(size=0.15, location=(0.28, 0.12, 0.52))
guard = bpy.context.active_object
guard.name = "Sword_Guard"
guard.scale = (0.5, 1.5, 0.2)
bpy.ops.object.transform_apply(scale=True)
guard.rotation_euler = (math.radians(-30), 0, math.radians(15))
guard.data.materials.append(mat_metal)

bpy.ops.mesh.primitive_cylinder_add(
    vertices=12, radius=0.015, depth=0.15, location=(0.26, 0.14, 0.42)
)
handle = bpy.context.active_object
handle.name = "Sword_Handle"
handle.rotation_euler = (math.radians(60), 0, math.radians(15))
handle.data.materials.append(mat_leather)

bpy.ops.mesh.primitive_uv_sphere_add(
    segments=12, ring_count=8, radius=0.025, location=(0.24, 0.16, 0.35)
)
pommel = bpy.context.active_object
pommel.name = "Sword_Pommel"
pommel.data.materials.append(mat_metal)

print("Weapon created")

# === LIGHTING ===
bpy.ops.object.light_add(type="SUN", location=(5, -5, 10))
key_light = bpy.context.active_object
key_light.name = "KeyLight"
key_light.data.energy = 3.0
key_light.rotation_euler = (math.radians(45), math.radians(30), 0)

bpy.ops.object.light_add(type="SUN", location=(-5, -3, 8))
fill_light = bpy.context.active_object
fill_light.name = "FillLight"
fill_light.data.energy = 1.5
fill_light.data.color = (0.8, 0.9, 1.0)
fill_light.rotation_euler = (math.radians(60), math.radians(-30), 0)

bpy.ops.object.light_add(type="SUN", location=(0, 5, 8))
rim_light = bpy.context.active_object
rim_light.name = "RimLight"
rim_light.data.energy = 2.0
rim_light.rotation_euler = (math.radians(-30), 0, math.radians(180))

print("Lighting setup complete")

# === CAMERA ===
bpy.ops.object.camera_add(location=(0, -3.5, 1.5))
camera = bpy.context.active_object
camera.name = "MainCamera"
camera.rotation_euler = (math.radians(85), 0, 0)
camera.data.lens = 50
bpy.context.scene.camera = camera

# === RENDER SETTINGS ===
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 128
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.view_settings.view_transform = "Filmic"
scene.view_settings.look = "Medium High Contrast"

print("Render settings configured")

# === ORGANIZE ===
char_col = bpy.data.collections["Character"]
armor_col = bpy.data.collections["Armor"]
weapon_col = bpy.data.collections["Weapons"]

for obj in bpy.data.objects:
    if obj.type == "MESH":
        if "Armor" in obj.name:
            for c in obj.users_collection:
                c.objects.unlink(obj)
            armor_col.objects.link(obj)
        elif "Sword" in obj.name:
            for c in obj.users_collection:
                c.objects.unlink(obj)
            weapon_col.objects.link(obj)
        elif obj.name not in ["Camera", "KeyLight", "FillLight", "RimLight"]:
            for c in obj.users_collection:
                c.objects.unlink(obj)
            char_col.objects.link(obj)

# Save
output_path = r"E:\Projects\blender-mcp-ai\examples\fantasy_warrior_3a.blend"
bpy.ops.wm.save_mainfile(filepath=output_path)

print("\n✓ 3A Fantasy Warrior Complete!")
print(f"Saved: {output_path}")
print(f"Objects: {len([o for o in bpy.data.objects if o.type == 'MESH'])}")
print(f"Materials: {len(bpy.data.materials)}")
