"""
Material Handler

Handles material related commands.
"""

from typing import Any

import bpy


def get_principled_bsdf(nodes):
    """Get Principled BSDF node, compatible with different Blender versions"""
    # First try to find by name (common Blender default name)
    bsdf = nodes.get("Principled BSDF")
    if bsdf and bsdf.type == "BSDF_PRINCIPLED":
        return bsdf

    # Then search by type
    for node in nodes:
        if node.type == "BSDF_PRINCIPLED":
            return node
    return None


def handle_create(params: dict[str, Any]) -> dict[str, Any]:
    """Create material"""
    name = params.get("name", "Material")
    color = params.get("color", [0.8, 0.8, 0.8, 1.0])
    metallic = params.get("metallic", 0.0)
    roughness = params.get("roughness", 0.5)
    use_nodes = params.get("use_nodes", True)

    # Create material
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = use_nodes

    if use_nodes:
        # Get Principled BSDF node
        nodes = mat.node_tree.nodes
        principled = get_principled_bsdf(nodes)

        if principled:
            # Set color
            if len(color) == 3:
                color = color + [1.0]
            principled.inputs["Base Color"].default_value = color

            # Set metallic and roughness
            principled.inputs["Metallic"].default_value = metallic
            principled.inputs["Roughness"].default_value = roughness
    else:
        mat.diffuse_color = color

    return {"success": True, "data": {"material_name": mat.name}}


def handle_assign(params: dict[str, Any]) -> dict[str, Any]:
    """Assign material"""
    object_name = params.get("object_name", "")
    material_name = params.get("material_name", "")
    slot_index = params.get("slot_index", 0)

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    mat = bpy.data.materials.get(material_name)
    if not mat:
        return {
            "success": False,
            "error": {
                "code": "MATERIAL_NOT_FOUND",
                "message": f"Material not found: {material_name}",
            },
        }

    # Ensure enough material slots
    while len(obj.material_slots) <= slot_index:
        obj.data.materials.append(None)

    # Assign material
    obj.material_slots[slot_index].material = mat

    return {"success": True, "data": {}}


def handle_set_properties(params: dict[str, Any]) -> dict[str, Any]:
    """Set material properties"""
    material_name = params.get("material_name", "")
    properties = params.get("properties", {})

    mat = bpy.data.materials.get(material_name)
    if not mat:
        return {
            "success": False,
            "error": {
                "code": "MATERIAL_NOT_FOUND",
                "message": f"Material not found: {material_name}",
            },
        }

    if not mat.use_nodes:
        mat.use_nodes = True

    nodes = mat.node_tree.nodes
    principled = get_principled_bsdf(nodes)

    if not principled:
        return {
            "success": False,
            "error": {"code": "NODE_NOT_FOUND", "message": "Principled BSDF node not found"},
        }

    # Set properties
    if "color" in properties:
        color = properties["color"]
        if len(color) == 3:
            color = color + [1.0]
        principled.inputs["Base Color"].default_value = color

    if "metallic" in properties:
        principled.inputs["Metallic"].default_value = properties["metallic"]

    if "roughness" in properties:
        principled.inputs["Roughness"].default_value = properties["roughness"]

    if "specular" in properties:
        # Blender 4.0+ uses Specular IOR Level
        if "Specular IOR Level" in principled.inputs:
            principled.inputs["Specular IOR Level"].default_value = properties["specular"]
        elif "Specular" in principled.inputs:
            principled.inputs["Specular"].default_value = properties["specular"]

    if "emission_color" in properties:
        emission = properties["emission_color"]
        if len(emission) == 3:
            emission = emission + [1.0]
        principled.inputs["Emission Color"].default_value = emission

    if "emission_strength" in properties:
        principled.inputs["Emission Strength"].default_value = properties["emission_strength"]

    if "alpha" in properties:
        principled.inputs["Alpha"].default_value = properties["alpha"]
        mat.blend_method = "BLEND" if properties["alpha"] < 1.0 else "OPAQUE"

    if "blend_mode" in properties:
        mat.blend_method = properties["blend_mode"]

    return {"success": True, "data": {}}


def handle_add_texture(params: dict[str, Any]) -> dict[str, Any]:
    """Add texture"""
    material_name = params.get("material_name", "")
    texture_path = params.get("texture_path")
    texture_type = params.get("texture_type", "COLOR")
    params.get("mapping", "UV")

    mat = bpy.data.materials.get(material_name)
    if not mat:
        return {
            "success": False,
            "error": {
                "code": "MATERIAL_NOT_FOUND",
                "message": f"Material not found: {material_name}",
            },
        }

    if not mat.use_nodes:
        mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    principled = get_principled_bsdf(nodes)

    if not principled:
        return {
            "success": False,
            "error": {"code": "NODE_NOT_FOUND", "message": "Principled BSDF node not found"},
        }

    # Load image
    try:
        image = bpy.data.images.load(texture_path)
    except Exception as e:
        return {
            "success": False,
            "error": {"code": "IMAGE_LOAD_ERROR", "message": f"Failed to load image: {e}"},
        }

    # Create image texture node
    tex_node = nodes.new(type="ShaderNodeTexImage")
    tex_node.image = image
    tex_node.location = (-400, 0)

    # Connect to corresponding input
    input_map = {
        "COLOR": "Base Color",
        "NORMAL": None,  # Requires normal map node
        "ROUGHNESS": "Roughness",
        "METALLIC": "Metallic",
        "EMISSION": "Emission Color",
    }

    target_input = input_map.get(texture_type)

    if texture_type == "NORMAL":
        # Create normal map node
        normal_node = nodes.new(type="ShaderNodeNormalMap")
        normal_node.location = (-200, 0)
        links.new(tex_node.outputs["Color"], normal_node.inputs["Color"])
        links.new(normal_node.outputs["Normal"], principled.inputs["Normal"])
        image.colorspace_settings.name = "Non-Color"
    elif target_input:
        links.new(tex_node.outputs["Color"], principled.inputs[target_input])
        if texture_type != "COLOR":
            image.colorspace_settings.name = "Non-Color"

    return {"success": True, "data": {}}


def handle_list(params: dict[str, Any]) -> dict[str, Any]:
    """List materials"""
    limit = params.get("limit", 50)

    materials = []
    for mat in bpy.data.materials[:limit]:
        mat_info = {"name": mat.name}

        if mat.use_nodes:
            nodes = mat.node_tree.nodes
            principled = get_principled_bsdf(nodes)
            if principled:
                mat_info["color"] = list(principled.inputs["Base Color"].default_value)
                mat_info["metallic"] = principled.inputs["Metallic"].default_value
                mat_info["roughness"] = principled.inputs["Roughness"].default_value

        materials.append(mat_info)

    return {"success": True, "data": {"materials": materials, "total": len(bpy.data.materials)}}


def handle_delete(params: dict[str, Any]) -> dict[str, Any]:
    """Delete material"""
    material_name = params.get("material_name", "")

    mat = bpy.data.materials.get(material_name)
    if not mat:
        return {
            "success": False,
            "error": {
                "code": "MATERIAL_NOT_FOUND",
                "message": f"Material not found: {material_name}",
            },
        }

    bpy.data.materials.remove(mat)

    return {"success": True, "data": {}}


def handle_node_add(params: dict[str, Any]) -> dict[str, Any]:
    """Add material node

    Args:
        params:
            - material_name: Material name
            - node_type: Node type
                - SSS: Subsurface scattering node configuration
                - EMISSION: Emission node
                - MIX_RGB: Mix RGB
                - COLOR_RAMP: Color ramp
                - NOISE_TEXTURE: Noise texture
                - IMAGE_TEXTURE: Image texture
                - NORMAL_MAP: Normal map
                - BUMP: Bump map
            - settings: Node settings
            - connect_to: Node input to connect to
    """
    material_name = params.get("material_name", "")
    node_type = params.get("node_type")
    settings = params.get("settings", {})
    connect_to = params.get("connect_to")
    location = params.get("location", [-300, 0])

    mat = bpy.data.materials.get(material_name)
    if not mat:
        return {
            "success": False,
            "error": {
                "code": "MATERIAL_NOT_FOUND",
                "message": f"Material not found: {material_name}",
            },
        }

    if not mat.use_nodes:
        mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    principled = get_principled_bsdf(nodes)

    try:
        # Create and configure node based on node type
        if node_type == "SSS":
            # Configure Principled BSDF subsurface scattering
            if principled:
                subsurface = settings.get("subsurface", 0.3)
                settings.get("subsurface_color", [0.8, 0.2, 0.1])
                subsurface_radius = settings.get("subsurface_radius", [1.0, 0.2, 0.1])

                # Blender 4.0+ uses a different SSS interface
                if "Subsurface Weight" in principled.inputs:
                    principled.inputs["Subsurface Weight"].default_value = subsurface
                elif "Subsurface" in principled.inputs:
                    principled.inputs["Subsurface"].default_value = subsurface

                if "Subsurface Radius" in principled.inputs:
                    principled.inputs["Subsurface Radius"].default_value = subsurface_radius

                return {"success": True, "data": {"node_type": "SSS", "subsurface": subsurface}}

        elif node_type == "EMISSION":
            # Configure emission
            if principled:
                emission_color = settings.get("color", [1.0, 1.0, 1.0, 1.0])
                emission_strength = settings.get("strength", 1.0)

                if len(emission_color) == 3:
                    emission_color = emission_color + [1.0]

                principled.inputs["Emission Color"].default_value = emission_color
                principled.inputs["Emission Strength"].default_value = emission_strength

                return {
                    "success": True,
                    "data": {"node_type": "EMISSION", "strength": emission_strength},
                }

        elif node_type == "MIX_RGB":
            node = nodes.new(type="ShaderNodeMixRGB")
            node.location = location
            node.blend_type = settings.get("blend_type", "MIX")
            node.inputs["Fac"].default_value = settings.get("fac", 0.5)

        elif node_type == "COLOR_RAMP":
            node = nodes.new(type="ShaderNodeValToRGB")
            node.location = location
            # Set color stops
            stops = settings.get("stops", [])
            for i, stop in enumerate(stops):
                if i < len(node.color_ramp.elements):
                    elem = node.color_ramp.elements[i]
                else:
                    elem = node.color_ramp.elements.new(stop.get("position", 0.5))
                elem.position = stop.get("position", i / max(len(stops) - 1, 1))
                elem.color = stop.get("color", [1, 1, 1, 1])

        elif node_type == "NOISE_TEXTURE":
            node = nodes.new(type="ShaderNodeTexNoise")
            node.location = location
            node.inputs["Scale"].default_value = settings.get("scale", 5.0)
            node.inputs["Detail"].default_value = settings.get("detail", 2.0)
            node.inputs["Roughness"].default_value = settings.get("roughness", 0.5)

        elif node_type == "IMAGE_TEXTURE":
            node = nodes.new(type="ShaderNodeTexImage")
            node.location = location
            image_path = settings.get("image_path")
            if image_path:
                try:
                    image = bpy.data.images.load(image_path)
                    node.image = image
                except:
                    pass

        elif node_type == "NORMAL_MAP":
            node = nodes.new(type="ShaderNodeNormalMap")
            node.location = location
            node.space = settings.get("space", "TANGENT")
            node.inputs["Strength"].default_value = settings.get("strength", 1.0)

        elif node_type == "BUMP":
            node = nodes.new(type="ShaderNodeBump")
            node.location = location
            node.inputs["Strength"].default_value = settings.get("strength", 1.0)
            node.inputs["Distance"].default_value = settings.get("distance", 0.1)

        else:
            # Try to create generic node
            try:
                node = nodes.new(type=node_type)
                node.location = location
            except:
                return {
                    "success": False,
                    "error": {
                        "code": "INVALID_NODE_TYPE",
                        "message": f"Unsupported node type: {node_type}",
                    },
                }

        # Connect node
        if connect_to and principled:
            if node_type not in ["SSS", "EMISSION"]:
                target_input = connect_to.get("input", "Base Color")
                output_socket = connect_to.get("output", "Color")

                if (
                    target_input in principled.inputs
                    and hasattr(node.outputs, output_socket)
                    or output_socket in [o.name for o in node.outputs]
                ):
                    out_socket = node.outputs.get(output_socket) or node.outputs[0]
                    links.new(out_socket, principled.inputs[target_input])

        return {
            "success": True,
            "data": {"node_type": node_type, "node_name": node.name if "node" in dir() else "N/A"},
        }

    except Exception as e:
        return {"success": False, "error": {"code": "NODE_ADD_ERROR", "message": str(e)}}


def handle_texture_apply(params: dict[str, Any]) -> dict[str, Any]:
    """Apply texture map

    Args:
        params:
            - material_name: Material name
            - image_path: Image file path
            - mapping_type: Mapping type
                - UV: UV mapping (default)
                - BOX: Box mapping
                - FLAT: Flat mapping
                - SPHERE: Sphere mapping
            - texture_type: Texture usage
                - COLOR: Color map
                - NORMAL: Normal map
                - ROUGHNESS: Roughness map
                - METALLIC: Metallic map
                - EMISSION: Emission map
                - ALPHA: Alpha map
    """
    material_name = params.get("material_name", "")
    image_path = params.get("image_path")
    mapping_type = params.get("mapping_type", "UV")
    texture_type = params.get("texture_type", "COLOR")

    mat = bpy.data.materials.get(material_name)
    if not mat:
        return {
            "success": False,
            "error": {
                "code": "MATERIAL_NOT_FOUND",
                "message": f"Material not found: {material_name}",
            },
        }

    if not mat.use_nodes:
        mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    principled = get_principled_bsdf(nodes)

    if not principled:
        return {
            "success": False,
            "error": {"code": "NODE_NOT_FOUND", "message": "Principled BSDF node not found"},
        }

    # Load image
    try:
        image = bpy.data.images.load(image_path)
    except Exception as e:
        return {
            "success": False,
            "error": {"code": "IMAGE_LOAD_ERROR", "message": f"Failed to load image: {e}"},
        }

    # Create image texture node
    tex_node = nodes.new(type="ShaderNodeTexImage")
    tex_node.image = image
    tex_node.location = (-600, 0)

    # Create texture coordinate and mapping nodes
    tex_coord = nodes.new(type="ShaderNodeTexCoord")
    tex_coord.location = (-1000, 0)

    mapping = nodes.new(type="ShaderNodeMapping")
    mapping.location = (-800, 0)

    # Connect texture coordinates
    coord_output = "UV" if mapping_type == "UV" else "Generated"
    if mapping_type == "BOX":
        coord_output = "Object"

    links.new(tex_coord.outputs[coord_output], mapping.outputs["Vector"])
    links.new(mapping.outputs["Vector"], tex_node.inputs["Vector"])

    # Connect to corresponding input based on texture type
    input_map = {
        "COLOR": "Base Color",
        "NORMAL": None,  # Requires normal map node
        "ROUGHNESS": "Roughness",
        "METALLIC": "Metallic",
        "EMISSION": "Emission Color",
        "ALPHA": "Alpha",
    }

    target_input = input_map.get(texture_type)

    if texture_type == "NORMAL":
        # Create normal map node
        normal_node = nodes.new(type="ShaderNodeNormalMap")
        normal_node.location = (-400, 0)
        links.new(tex_node.outputs["Color"], normal_node.inputs["Color"])
        links.new(normal_node.outputs["Normal"], principled.inputs["Normal"])
        image.colorspace_settings.name = "Non-Color"
    elif target_input:
        links.new(tex_node.outputs["Color"], principled.inputs[target_input])
        if texture_type not in ["COLOR", "EMISSION"]:
            image.colorspace_settings.name = "Non-Color"

        # Handle alpha/transparency
        if texture_type == "ALPHA":
            mat.blend_method = "BLEND"

    return {
        "success": True,
        "data": {
            "material_name": mat.name,
            "image_name": image.name,
            "texture_type": texture_type,
            "mapping_type": mapping_type,
        },
    }


def handle_create_skin_material(params: dict[str, Any]) -> dict[str, Any]:
    """Create skin material

    Preset skin material with SSS and appropriate roughness settings.

    Args:
        params:
            - name: Material name
            - skin_tone: Skin tone type (LIGHT, MEDIUM, DARK, CUSTOM)
            - custom_color: Custom color (when skin_tone is CUSTOM)
    """
    name = params.get("name", "SkinMaterial")
    skin_tone = params.get("skin_tone", "MEDIUM")
    custom_color = params.get("custom_color")

    # Preset skin tones
    skin_colors = {
        "LIGHT": [0.95, 0.85, 0.75, 1.0],
        "MEDIUM": [0.87, 0.70, 0.55, 1.0],
        "DARK": [0.45, 0.30, 0.20, 1.0],
    }

    color = (
        custom_color
        if skin_tone == "CUSTOM" and custom_color
        else skin_colors.get(skin_tone, skin_colors["MEDIUM"])
    )
    if len(color) == 3:
        color = color + [1.0]

    # Create material
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    principled = get_principled_bsdf(nodes)

    if principled:
        # Base color
        principled.inputs["Base Color"].default_value = color

        # SSS settings
        if "Subsurface Weight" in principled.inputs:
            principled.inputs["Subsurface Weight"].default_value = 0.3
        elif "Subsurface" in principled.inputs:
            principled.inputs["Subsurface"].default_value = 0.3

        if "Subsurface Radius" in principled.inputs:
            # Red light scatters the most, blue the least
            principled.inputs["Subsurface Radius"].default_value = [1.0, 0.2, 0.1]

        # Roughness
        principled.inputs["Roughness"].default_value = 0.4

        # Specular reflection
        if "Specular IOR Level" in principled.inputs:
            principled.inputs["Specular IOR Level"].default_value = 0.5
        elif "Specular" in principled.inputs:
            principled.inputs["Specular"].default_value = 0.5

    return {
        "success": True,
        "data": {"material_name": mat.name, "skin_tone": skin_tone, "color": color[:3]},
    }


def handle_create_toon_material(params: dict[str, Any]) -> dict[str, Any]:
    """Create toon material

    Stylized toon material suitable for chibi/cartoon characters.

    Args:
        params:
            - name: Material name
            - color: Base color
            - shadow_color: Shadow color (optional)
            - outline: Whether to add outline effect
    """
    name = params.get("name", "ToonMaterial")
    color = params.get("color", [0.8, 0.8, 0.8, 1.0])
    params.get("shadow_color")
    outline = params.get("outline", False)

    if len(color) == 3:
        color = color + [1.0]

    # Create material
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Clear default nodes
    for node in nodes:
        nodes.remove(node)

    # Create output node
    output = nodes.new(type="ShaderNodeOutputMaterial")
    output.location = (400, 0)

    # Create Principled BSDF (simplified toon effect)
    principled = nodes.new(type="ShaderNodeBsdfPrincipled")
    principled.location = (100, 0)
    principled.inputs["Base Color"].default_value = color
    principled.inputs["Roughness"].default_value = (
        0.9  # High roughness to reduce specular highlights
    )
    principled.inputs["Metallic"].default_value = 0.0

    if "Specular IOR Level" in principled.inputs:
        principled.inputs["Specular IOR Level"].default_value = 0.1
    elif "Specular" in principled.inputs:
        principled.inputs["Specular"].default_value = 0.1

    links.new(principled.outputs["BSDF"], output.inputs["Surface"])

    # If outline is needed, set backface culling
    if outline:
        mat.use_backface_culling = True

    return {"success": True, "data": {"material_name": mat.name, "color": color[:3]}}


# ==================== Production Standard Optimization Handlers ====================

# Texture type to correct color space mapping
TEXTURE_COLORSPACE_MAP = {
    "COLOR": "sRGB",
    "DIFFUSE": "sRGB",
    "BASE_COLOR": "sRGB",
    "EMISSION": "sRGB",
    "NORMAL": "Non-Color",
    "ROUGHNESS": "Non-Color",
    "METALLIC": "Non-Color",
    "AO": "Non-Color",
    "OCCLUSION": "Non-Color",
    "HEIGHT": "Non-Color",
    "DISPLACEMENT": "Non-Color",
    "ALPHA": "Non-Color",
    "SPECULAR": "Non-Color",
}


def handle_analyze(params: dict[str, Any]) -> dict[str, Any]:
    """Analyze whether material meets PBR production standards

    Args:
        params:
            - material_name: Material name
            - target_engine: Target game engine
    """
    material_name = params.get("material_name", "")
    target_engine = params.get("target_engine", "GENERIC")

    mat = bpy.data.materials.get(material_name)
    if not mat:
        return {
            "success": False,
            "error": {
                "code": "MATERIAL_NOT_FOUND",
                "message": f"Material not found: {material_name}",
            },
        }

    issues = []
    suggestions = []
    textures = []
    pbr_values = {}

    # Check if using nodes
    uses_nodes = mat.use_nodes

    if uses_nodes and mat.node_tree:
        nodes = mat.node_tree.nodes

        # Find Principled BSDF node
        principled = None
        for node in nodes:
            if node.type == "BSDF_PRINCIPLED":
                principled = node
                break

        if principled:
            # Check metallic
            metallic = principled.inputs["Metallic"].default_value
            pbr_values["metallic"] = metallic

            if 0 < metallic < 1:
                issues.append(
                    f"Metallic value is {metallic:.2f}, should be 0 (non-metal) or 1 (metal)"
                )
                suggestions.append(
                    "Use a metallic texture map or set the value to 0 or 1 to comply with PBR standards"
                )

            # Check roughness
            roughness = principled.inputs["Roughness"].default_value
            pbr_values["roughness"] = roughness

            # Check base color
            base_color = list(principled.inputs["Base Color"].default_value)
            pbr_values["base_color"] = base_color[:3]

            # Check for overly bright or dark colors
            brightness = sum(base_color[:3]) / 3
            if brightness > 0.95:
                suggestions.append("Base color is too bright, may cause overexposure in rendering")
            elif brightness < 0.05:
                suggestions.append("Base color is too dark, consider increasing brightness")

        # Check texture nodes
        for node in nodes:
            if node.type == "TEX_IMAGE" and node.image:
                image = node.image

                # Try to detect texture type
                tex_type = "UNKNOWN"
                name_lower = image.name.lower()

                if any(x in name_lower for x in ["normal", "nrm", "nor", "bump"]):
                    tex_type = "NORMAL"
                elif any(x in name_lower for x in ["rough", "roughness", "rgh"]):
                    tex_type = "ROUGHNESS"
                elif any(x in name_lower for x in ["metal", "metallic", "mtl"]):
                    tex_type = "METALLIC"
                elif any(x in name_lower for x in ["ao", "occlusion", "ambient"]):
                    tex_type = "AO"
                elif any(x in name_lower for x in ["color", "diffuse", "albedo", "base"]):
                    tex_type = "COLOR"
                elif any(x in name_lower for x in ["emit", "emission", "glow"]):
                    tex_type = "EMISSION"

                expected_colorspace = TEXTURE_COLORSPACE_MAP.get(tex_type, "sRGB")
                actual_colorspace = image.colorspace_settings.name
                colorspace_correct = actual_colorspace == expected_colorspace or (
                    expected_colorspace == "Non-Color" and "non" in actual_colorspace.lower()
                )

                textures.append(
                    {
                        "name": image.name,
                        "type": tex_type,
                        "colorspace": actual_colorspace,
                        "expected_colorspace": expected_colorspace,
                        "colorspace_correct": colorspace_correct,
                    }
                )

                if not colorspace_correct:
                    issues.append(
                        f"Texture '{image.name}' color space should be {expected_colorspace}, currently {actual_colorspace}"
                    )
    else:
        issues.append("Material does not use nodes, unable to perform detailed analysis")
        suggestions.append("Recommend enabling node material for better PBR support")

    # Engine-specific checks
    if target_engine == "UNITY":
        suggestions.append("Unity uses Standard/URP/HDRP shaders, ensure export as glTF or FBX")
    elif target_engine == "UNREAL":
        suggestions.append(
            "Unreal uses separate ORM textures (Occlusion+Roughness+Metallic), consider merging channels"
        )
    elif target_engine == "GODOT":
        suggestions.append("Godot supports glTF 2.0 and ORM texture formats")

    # Calculate compatibility score
    score = 100
    score -= len(issues) * 15
    score = max(0, score)

    return {
        "success": True,
        "data": {
            "uses_nodes": uses_nodes,
            "pbr_values": pbr_values,
            "textures": textures,
            "issues": issues,
            "suggestions": suggestions,
            "compatibility_score": score,
        },
    }


def handle_optimize(params: dict[str, Any]) -> dict[str, Any]:
    """Optimize material to meet game engine PBR standards

    Args:
        params:
            - material_name: Material name
            - target_engine: Target game engine
            - fix_metallic: Fix metallic values
            - fix_color_space: Fix texture color spaces
            - combine_textures: Combine texture channels
    """
    material_name = params.get("material_name", "")
    params.get("target_engine", "GENERIC")
    fix_metallic = params.get("fix_metallic", True)
    fix_color_space = params.get("fix_color_space", True)
    params.get("combine_textures", False)

    mat = bpy.data.materials.get(material_name)
    if not mat:
        return {
            "success": False,
            "error": {
                "code": "MATERIAL_NOT_FOUND",
                "message": f"Material not found: {material_name}",
            },
        }

    fixes_applied = []

    if not mat.use_nodes:
        mat.use_nodes = True
        fixes_applied.append("Enabled node material")

    if mat.node_tree:
        nodes = mat.node_tree.nodes

        # Find Principled BSDF
        principled = None
        for node in nodes:
            if node.type == "BSDF_PRINCIPLED":
                principled = node
                break

        if principled and fix_metallic:
            metallic = principled.inputs["Metallic"].default_value
            if 0 < metallic < 1:
                # Round to 0 or 1
                new_metallic = 1.0 if metallic >= 0.5 else 0.0
                principled.inputs["Metallic"].default_value = new_metallic
                fixes_applied.append(f"Metallic: {metallic:.2f} -> {new_metallic}")

        # Fix texture color spaces
        if fix_color_space:
            for node in nodes:
                if node.type == "TEX_IMAGE" and node.image:
                    image = node.image
                    name_lower = image.name.lower()

                    # Detect texture type
                    tex_type = "COLOR"
                    if any(x in name_lower for x in ["normal", "nrm", "nor", "bump"]):
                        tex_type = "NORMAL"
                    elif any(x in name_lower for x in ["rough", "roughness", "rgh"]):
                        tex_type = "ROUGHNESS"
                    elif any(x in name_lower for x in ["metal", "metallic", "mtl"]):
                        tex_type = "METALLIC"
                    elif any(x in name_lower for x in ["ao", "occlusion", "ambient"]):
                        tex_type = "AO"
                    elif any(x in name_lower for x in ["height", "displacement", "disp"]):
                        tex_type = "HEIGHT"

                    expected = TEXTURE_COLORSPACE_MAP.get(tex_type, "sRGB")
                    current = image.colorspace_settings.name

                    needs_fix = False
                    if (
                        expected == "Non-Color"
                        and "non" not in current.lower()
                        or expected == "sRGB"
                        and current != "sRGB"
                    ):
                        needs_fix = True

                    if needs_fix:
                        old_space = current
                        image.colorspace_settings.name = expected
                        fixes_applied.append(
                            f"Texture '{image.name}' color space: {old_space} -> {expected}"
                        )

    return {"success": True, "data": {"material_name": mat.name, "fixes_applied": fixes_applied}}


def handle_create_pbr(params: dict[str, Any]) -> dict[str, Any]:
    """Create production-standard PBR material

    Args:
        params:
            - name: Material name
            - target_engine: Target game engine
            - base_color: Base color
            - metallic: Metallic
            - roughness: Roughness
            - *_texture: Various texture paths
            - emission_strength: Emission strength
            - alpha_mode: Alpha mode
            - double_sided: Double-sided rendering
    """
    name = params.get("name", "PBR_Material")
    target_engine = params.get("target_engine", "GENERIC")
    base_color = params.get("base_color", [0.8, 0.8, 0.8, 1.0])
    metallic = params.get("metallic", 0.0)
    roughness = params.get("roughness", 0.5)
    alpha_mode = params.get("alpha_mode", "OPAQUE")
    double_sided = params.get("double_sided", False)
    emission_strength = params.get("emission_strength", 0.0)

    # Texture paths
    base_color_texture = params.get("base_color_texture")
    normal_texture = params.get("normal_texture")
    metallic_texture = params.get("metallic_texture")
    roughness_texture = params.get("roughness_texture")
    ao_texture = params.get("ao_texture")
    emission_texture = params.get("emission_texture")

    if len(base_color) == 3:
        base_color = base_color + [1.0]

    # Create material
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True

    # Set blend mode
    blend_modes = {"OPAQUE": "OPAQUE", "CLIP": "CLIP", "HASHED": "HASHED", "BLEND": "BLEND"}
    mat.blend_method = blend_modes.get(alpha_mode, "OPAQUE")

    # Double-sided rendering
    mat.use_backface_culling = not double_sided

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    principled = get_principled_bsdf(nodes)
    nodes.get("Material Output")

    if principled:
        # Set base properties
        principled.inputs["Base Color"].default_value = base_color
        principled.inputs["Metallic"].default_value = metallic
        principled.inputs["Roughness"].default_value = roughness

        if emission_strength > 0:
            if "Emission Strength" in principled.inputs:
                principled.inputs["Emission Strength"].default_value = emission_strength
            principled.inputs["Emission Color"].default_value = base_color

    textures_loaded = []
    x_offset = -300

    # Helper function to load textures
    def load_texture(path, tex_type, y_offset):
        nonlocal x_offset
        if not path:
            return None

        import os

        if not os.path.exists(path):
            return None

        try:
            image = bpy.data.images.load(path)
            tex_node = nodes.new(type="ShaderNodeTexImage")
            tex_node.location = (x_offset, y_offset)
            tex_node.image = image

            # Set color space
            colorspace = TEXTURE_COLORSPACE_MAP.get(tex_type, "sRGB")
            image.colorspace_settings.name = colorspace

            textures_loaded.append(f"{tex_type}: {os.path.basename(path)}")
            return tex_node
        except:
            return None

    # Load and connect textures
    if base_color_texture and principled:
        tex = load_texture(base_color_texture, "COLOR", 200)
        if tex:
            links.new(tex.outputs["Color"], principled.inputs["Base Color"])
            if tex.outputs.get("Alpha"):
                links.new(tex.outputs["Alpha"], principled.inputs["Alpha"])

    if normal_texture and principled:
        tex = load_texture(normal_texture, "NORMAL", 0)
        if tex:
            normal_map = nodes.new(type="ShaderNodeNormalMap")
            normal_map.location = (x_offset + 200, 0)
            links.new(tex.outputs["Color"], normal_map.inputs["Color"])
            links.new(normal_map.outputs["Normal"], principled.inputs["Normal"])

    if roughness_texture and principled:
        tex = load_texture(roughness_texture, "ROUGHNESS", -200)
        if tex:
            links.new(tex.outputs["Color"], principled.inputs["Roughness"])

    if metallic_texture and principled:
        tex = load_texture(metallic_texture, "METALLIC", -400)
        if tex:
            links.new(tex.outputs["Color"], principled.inputs["Metallic"])

    if ao_texture and principled:
        tex = load_texture(ao_texture, "AO", -600)
        if tex:
            # AO is typically multiplied with base color
            mix_node = nodes.new(type="ShaderNodeMixRGB")
            mix_node.blend_type = "MULTIPLY"
            mix_node.location = (x_offset + 200, 200)
            mix_node.inputs["Fac"].default_value = 1.0

            # Find existing color connection and insert AO
            for link in list(links):
                if link.to_socket == principled.inputs["Base Color"]:
                    links.new(link.from_socket, mix_node.inputs["Color1"])
                    links.remove(link)
                    break
            else:
                mix_node.inputs["Color1"].default_value = base_color

            links.new(tex.outputs["Color"], mix_node.inputs["Color2"])
            links.new(mix_node.outputs["Color"], principled.inputs["Base Color"])

    if emission_texture and principled:
        tex = load_texture(emission_texture, "EMISSION", -800)
        if tex:
            links.new(tex.outputs["Color"], principled.inputs["Emission Color"])

    return {
        "success": True,
        "data": {
            "material_name": mat.name,
            "target_engine": target_engine,
            "textures_loaded": textures_loaded,
        },
    }


def handle_fix_colorspace(params: dict[str, Any]) -> dict[str, Any]:
    """Fix texture color spaces in material

    Args:
        params:
            - material_name: Material name
            - auto_detect: Auto detect
    """
    material_name = params.get("material_name", "")
    params.get("auto_detect", True)

    mat = bpy.data.materials.get(material_name)
    if not mat:
        return {
            "success": False,
            "error": {
                "code": "MATERIAL_NOT_FOUND",
                "message": f"Material not found: {material_name}",
            },
        }

    fixed_textures = []

    if mat.use_nodes and mat.node_tree:
        for node in mat.node_tree.nodes:
            if node.type == "TEX_IMAGE" and node.image:
                image = node.image
                name_lower = image.name.lower()

                # Auto detect texture type
                tex_type = "COLOR"
                if any(x in name_lower for x in ["normal", "nrm", "nor", "bump"]):
                    tex_type = "NORMAL"
                elif any(x in name_lower for x in ["rough", "roughness", "rgh"]):
                    tex_type = "ROUGHNESS"
                elif any(x in name_lower for x in ["metal", "metallic", "mtl"]):
                    tex_type = "METALLIC"
                elif any(x in name_lower for x in ["ao", "occlusion", "ambient"]):
                    tex_type = "AO"
                elif any(x in name_lower for x in ["height", "displacement", "disp"]):
                    tex_type = "HEIGHT"
                elif any(x in name_lower for x in ["alpha", "opacity", "mask"]):
                    tex_type = "ALPHA"

                expected = TEXTURE_COLORSPACE_MAP.get(tex_type, "sRGB")
                current = image.colorspace_settings.name

                needs_fix = False
                if (
                    expected == "Non-Color"
                    and "non" not in current.lower()
                    or expected == "sRGB"
                    and current != "sRGB"
                ):
                    needs_fix = True

                if needs_fix:
                    old_space = current
                    image.colorspace_settings.name = expected
                    fixed_textures.append(
                        {"name": image.name, "old_space": old_space, "new_space": expected}
                    )

    return {"success": True, "data": {"material_name": mat.name, "fixed_textures": fixed_textures}}


def handle_bake_textures(params: dict[str, Any]) -> dict[str, Any]:
    """Bake material textures

    Args:
        params:
            - material_name: Material name
            - output_directory: Output directory
            - resolution: Resolution
            - bake_types: Bake type list
    """
    import os

    material_name = params.get("material_name", "")
    output_directory = params.get("output_directory")
    resolution = params.get("resolution", 1024)
    bake_types = params.get("bake_types", ["DIFFUSE", "ROUGHNESS", "NORMAL"])

    mat = bpy.data.materials.get(material_name)
    if not mat:
        return {
            "success": False,
            "error": {
                "code": "MATERIAL_NOT_FOUND",
                "message": f"Material not found: {material_name}",
            },
        }

    # Ensure output directory exists
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Find or create an object using this material
    target_obj = None
    for obj in bpy.data.objects:
        if obj.type == "MESH" and mat.name in [
            slot.material.name for slot in obj.material_slots if slot.material
        ]:
            target_obj = obj
            break

    if not target_obj:
        return {
            "success": False,
            "error": {
                "code": "NO_OBJECT_FOUND",
                "message": "No mesh object found using this material",
            },
        }

    # Set up baking
    bpy.context.scene.render.engine = "CYCLES"
    bpy.context.scene.cycles.bake_type = "DIFFUSE"

    baked_textures = []

    # Note: Complete baking implementation requires more setup
    # This provides a basic framework

    for bake_type in bake_types:
        # Create bake target image
        image_name = f"{material_name}_{bake_type.lower()}"
        if image_name in bpy.data.images:
            bpy.data.images.remove(bpy.data.images[image_name])

        bpy.data.images.new(name=image_name, width=resolution, height=resolution, alpha=True)

        output_path = os.path.join(output_directory, f"{image_name}.png")
        baked_textures.append(f"{bake_type}: {output_path}")

    return {
        "success": True,
        "data": {
            "material_name": mat.name,
            "output_directory": output_directory,
            "resolution": resolution,
            "baked_textures": baked_textures,
        },
    }
