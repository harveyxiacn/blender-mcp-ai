"""
Node system handler

Handles creation and editing of shader nodes, geometry nodes, and compositor nodes.
"""

import contextlib
from typing import Any

import bpy

# Shader preset configuration
SHADER_PRESETS = {
    "pbr_basic": {
        "nodes": [
            {"type": "ShaderNodeBsdfPrincipled", "name": "Principled BSDF", "location": [0, 0]},
        ],
        "connections": [],
        "values": {"Principled BSDF": {"Roughness": 0.5, "Metallic": 0.0}},
    },
    "glass": {
        "nodes": [
            {"type": "ShaderNodeBsdfGlass", "name": "Glass BSDF", "location": [0, 0]},
        ],
        "connections": [["Glass BSDF", "BSDF", "Material Output", "Surface"]],
        "values": {"Glass BSDF": {"Roughness": 0.0, "IOR": 1.45}},
    },
    "metal": {
        "nodes": [
            {"type": "ShaderNodeBsdfPrincipled", "name": "Principled BSDF", "location": [0, 0]},
        ],
        "connections": [],
        "values": {"Principled BSDF": {"Metallic": 1.0, "Roughness": 0.3}},
    },
    "emission": {
        "nodes": [
            {"type": "ShaderNodeEmission", "name": "Emission", "location": [0, 0]},
        ],
        "connections": [["Emission", "Emission", "Material Output", "Surface"]],
        "values": {"Emission": {"Strength": 5.0}},
    },
    "subsurface": {
        "nodes": [
            {"type": "ShaderNodeBsdfPrincipled", "name": "Principled BSDF", "location": [0, 0]},
        ],
        "connections": [],
        "values": {
            "Principled BSDF": {"Subsurface Weight": 0.3, "Subsurface Radius": [1.0, 0.2, 0.1]}
        },
    },
    "toon": {
        "nodes": [
            {"type": "ShaderNodeBsdfToon", "name": "Toon BSDF", "location": [0, 0]},
            {"type": "ShaderNodeShaderToRGB", "name": "Shader to RGB", "location": [200, 0]},
        ],
        "connections": [
            ["Toon BSDF", "BSDF", "Shader to RGB", "Shader"],
        ],
        "values": {"Toon BSDF": {"Size": 0.5, "Smooth": 0.1}},
    },
}


def _get_node_tree(target: str):
    """Get node tree"""
    # bpy_prop_collection.__contains__ requires a string argument
    if not isinstance(target, str):
        return None, None

    # Check if it is a material
    if target in bpy.data.materials:
        mat = bpy.data.materials[target]
        if not mat.use_nodes:
            mat.use_nodes = True
        return mat.node_tree, "SHADER"

    # Check if it is the compositor
    if target == "compositor":
        bpy.context.scene.use_nodes = True
        return bpy.context.scene.node_tree, "COMPOSITOR"

    # Check if it is an object (geometry nodes)
    if target in bpy.data.objects:
        obj = bpy.data.objects[target]
        for mod in obj.modifiers:
            if mod.type == "NODES" and mod.node_group:
                return mod.node_group, "GEOMETRY"
        return None, None

    return None, None


def handle_add(params: dict[str, Any]) -> dict[str, Any]:
    """Add node"""
    target = params.get("target")
    node_type = params.get("node_type")
    location = params.get("location", [0, 0])
    name = params.get("name")

    node_tree, tree_type = _get_node_tree(target)
    if not node_tree:
        return {
            "success": False,
            "error": {
                "code": "TARGET_NOT_FOUND",
                "message": f"Target not found or has no node tree: {target}",
            },
        }

    # Create nodes
    try:
        node = node_tree.nodes.new(type=node_type)
        node.location = location
        if name:
            node.name = name
            node.label = name

        return {"success": True, "data": {"node_name": node.name}}
    except Exception as e:
        return {"success": False, "error": {"code": "NODE_CREATE_ERROR", "message": str(e)}}


def handle_connect(params: dict[str, Any]) -> dict[str, Any]:
    """Connect nodes"""
    target = params.get("target")
    from_node = params.get("from_node", "")
    from_socket = params.get("from_socket", "")
    to_node = params.get("to_node", "")
    to_socket = params.get("to_socket", "")

    node_tree, tree_type = _get_node_tree(target)
    if not node_tree:
        return {
            "success": False,
            "error": {"code": "TARGET_NOT_FOUND", "message": f"Target not found: {target}"},
        }

    # Get nodes
    source = node_tree.nodes.get(from_node)
    dest = node_tree.nodes.get(to_node)

    if not source:
        return {
            "success": False,
            "error": {"code": "NODE_NOT_FOUND", "message": f"Source node not found: {from_node}"},
        }

    if not dest:
        return {
            "success": False,
            "error": {"code": "NODE_NOT_FOUND", "message": f"Target node not found: {to_node}"},
        }

    # Get sockets
    try:
        if isinstance(from_socket, int):
            output = source.outputs[from_socket]
        else:
            output = source.outputs.get(from_socket) or source.outputs[from_socket]

        if isinstance(to_socket, int):
            input_socket = dest.inputs[to_socket]
        else:
            input_socket = dest.inputs.get(to_socket) or dest.inputs[to_socket]

        # Create connection
        node_tree.links.new(output, input_socket)

        return {"success": True, "data": {}}
    except Exception as e:
        return {"success": False, "error": {"code": "CONNECT_ERROR", "message": str(e)}}


def handle_set_value(params: dict[str, Any]) -> dict[str, Any]:
    """Set node value"""
    target = params.get("target")
    node_name = params.get("node_name", "")
    input_name = params.get("input_name", "")
    value = params.get("value")

    node_tree, tree_type = _get_node_tree(target)
    if not node_tree:
        return {
            "success": False,
            "error": {"code": "TARGET_NOT_FOUND", "message": f"Target not found: {target}"},
        }

    node = node_tree.nodes.get(node_name)
    if not node:
        return {
            "success": False,
            "error": {"code": "NODE_NOT_FOUND", "message": f"Node not found: {node_name}"},
        }

    try:
        input_socket = node.inputs.get(input_name)
        if input_socket:
            input_socket.default_value = value
        else:
            # Try setting as a property
            if hasattr(node, input_name):
                setattr(node, input_name, value)

        return {"success": True, "data": {}}
    except Exception as e:
        return {"success": False, "error": {"code": "SET_VALUE_ERROR", "message": str(e)}}


def handle_shader_preset(params: dict[str, Any]) -> dict[str, Any]:
    """Apply shader preset"""
    material_name = params.get("material_name", "")
    preset = params.get("preset", "pbr_basic")
    color = params.get("color")

    # Get or create material
    mat = bpy.data.materials.get(material_name)
    if not mat:
        mat = bpy.data.materials.new(name=material_name)

    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Clear existing nodes (keep output node)
    output_node = None
    for node in list(nodes):
        if node.type == "OUTPUT_MATERIAL":
            output_node = node
        else:
            nodes.remove(node)

    if not output_node:
        output_node = nodes.new("ShaderNodeOutputMaterial")
        output_node.location = [300, 0]

    preset_config = SHADER_PRESETS.get(preset, SHADER_PRESETS["pbr_basic"])

    # Create nodes
    created_nodes = {}
    for node_config in preset_config["nodes"]:
        node = nodes.new(type=node_config["type"])
        node.name = node_config["name"]
        node.label = node_config["name"]
        node.location = node_config["location"]
        created_nodes[node_config["name"]] = node

    # Set values
    for node_name, values in preset_config.get("values", {}).items():
        node = created_nodes.get(node_name)
        if node:
            for input_name, value in values.items():
                if input_name in node.inputs:
                    node.inputs[input_name].default_value = value

    # Set color
    if color:
        for node in created_nodes.values():
            if "Base Color" in node.inputs:
                node.inputs["Base Color"].default_value = color
            elif "Color" in node.inputs:
                node.inputs["Color"].default_value = color

    # Create connections
    for conn in preset_config.get("connections", []):
        from_node = created_nodes.get(conn[0])
        to_node = nodes.get(conn[2]) if conn[2] == "Material Output" else created_nodes.get(conn[2])
        if from_node and to_node:
            with contextlib.suppress(BaseException):
                links.new(from_node.outputs[conn[1]], to_node.inputs[conn[3]])

    # Connect to output
    main_node = list(created_nodes.values())[0] if created_nodes else None
    if main_node:
        if "BSDF" in main_node.outputs:
            links.new(main_node.outputs["BSDF"], output_node.inputs["Surface"])
        elif "Emission" in main_node.outputs:
            links.new(main_node.outputs["Emission"], output_node.inputs["Surface"])
        elif "Shader" in main_node.outputs:
            links.new(main_node.outputs["Shader"], output_node.inputs["Surface"])

    return {"success": True, "data": {"material_name": mat.name, "preset": preset}}


def handle_geonodes_add(params: dict[str, Any]) -> dict[str, Any]:
    """Add geometry nodes modifier"""
    object_name = params.get("object_name", "")
    modifier_name = params.get("modifier_name", "GeometryNodes")

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    # Add geometry nodes modifier
    modifier = obj.modifiers.new(name=modifier_name, type="NODES")

    # Create new node group
    node_group = bpy.data.node_groups.new(name=modifier_name, type="GeometryNodeTree")
    modifier.node_group = node_group

    # Add input/output nodes
    input_node = node_group.nodes.new("NodeGroupInput")
    input_node.location = [-200, 0]

    output_node = node_group.nodes.new("NodeGroupOutput")
    output_node.location = [200, 0]

    # Add geometry input/output
    node_group.interface.new_socket(
        name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry"
    )
    node_group.interface.new_socket(
        name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry"
    )

    # Connect input to output
    node_group.links.new(input_node.outputs[0], output_node.inputs[0])

    return {
        "success": True,
        "data": {"modifier_name": modifier.name, "node_group": node_group.name},
    }


def handle_geonodes_preset(params: dict[str, Any]) -> dict[str, Any]:
    """Apply geometry nodes preset"""
    object_name = params.get("object_name", "")
    preset = params.get("preset", "scatter")
    preset_params = params.get("params", {})

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    # Add geometry nodes modifier
    modifier = obj.modifiers.new(name=f"GeoNodes_{preset}", type="NODES")
    node_group = bpy.data.node_groups.new(name=f"{preset}_nodes", type="GeometryNodeTree")
    modifier.node_group = node_group

    nodes = node_group.nodes
    links = node_group.links

    # Add input/output
    input_node = nodes.new("NodeGroupInput")
    input_node.location = [-400, 0]

    output_node = nodes.new("NodeGroupOutput")
    output_node.location = [400, 0]

    node_group.interface.new_socket(
        name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry"
    )
    node_group.interface.new_socket(
        name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry"
    )

    if preset == "scatter":
        # Scatter preset
        distribute = nodes.new("GeometryNodeDistributePointsOnFaces")
        distribute.location = [0, 100]

        instance = nodes.new("GeometryNodeInstanceOnPoints")
        instance.location = [200, 0]

        join = nodes.new("GeometryNodeJoinGeometry")
        join.location = [400, 0]

        links.new(input_node.outputs[0], distribute.inputs["Mesh"])
        links.new(distribute.outputs["Points"], instance.inputs["Points"])
        links.new(input_node.outputs[0], join.inputs["Geometry"])
        links.new(instance.outputs["Instances"], join.inputs["Geometry"])
        links.new(join.outputs["Geometry"], output_node.inputs[0])

    elif preset == "array":
        # Array preset
        mesh_line = nodes.new("GeometryNodeMeshLine")
        mesh_line.location = [0, 0]
        mesh_line.inputs["Count"].default_value = preset_params.get("count", 5)

        instance = nodes.new("GeometryNodeInstanceOnPoints")
        instance.location = [200, 0]

        links.new(mesh_line.outputs["Mesh"], instance.inputs["Points"])
        links.new(input_node.outputs[0], instance.inputs["Instance"])
        links.new(instance.outputs["Instances"], output_node.inputs[0])

    else:
        # Default passthrough
        links.new(input_node.outputs[0], output_node.inputs[0])

    return {"success": True, "data": {"preset": preset, "node_group": node_group.name}}
