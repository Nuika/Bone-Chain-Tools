import bpy
import bmesh
import mathutils
from mathutils import Vector
import math

## ------------------ BONE CHAIN TOOLS -------------------------------------------------------- 
# funny   

#Selected has to be mesh, switch to edit mode, 
#Function should figure out how many face sets it has, im talking about pieces of linked geomtry
#print it out
#ignore the current name of function and class

def calculate_island_bounds(island_verts):
    """ Calculate the bounds of an island. """
    min_coord = [float('inf')] * 3
    max_coord = [float('-inf')] * 3
    for vert in island_verts:
        for i in range(3):
            min_coord[i] = min(min_coord[i], vert.co[i])
            max_coord[i] = max(max_coord[i], vert.co[i])
    return min_coord, max_coord

def calculate_center_point(min_coord, max_coord):
    """ Calculate the center point of the bounds. """
    return [(min_coord[i] + max_coord[i]) / 2 for i in range(3)]

def calculate_scale(min_coord, max_coord):
    """ Calculate the scale (X, Y values) based on the bounds. """
    return [max_coord[i] - min_coord[i] for i in range(2)]

def calculate_general_scale(min_coord, max_coord):
    """ Calculate a single value representing the general scale. """
    scale = calculate_scale(min_coord, max_coord)
    return (scale[0]**2 + scale[1]**2)**0.5

def create_bone_chain(context, root_bone_size):
    obj = context.active_object
        
    if not obj or obj.type != 'MESH':
        raise ValueError("The selected object is not a mesh.")
    
    if any(axis_scale != 1 for axis_scale in obj.scale):
        raise ValueError("The mesh scale must be 1. Current scale is: " + str(obj.scale))   
        
    mesh_origin = obj.location.copy()
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    
    # MESH VERTEX DATA PART
    
    for vert in bm.verts:
        vert.tag = False

    islands = []
    for vert in bm.verts:
        if not vert.tag:
            island_verts = []
            verts_to_check = [vert]
            while verts_to_check:
                current_vert = verts_to_check.pop()
                current_vert.tag = True
                island_verts.append(current_vert)
                for edge in current_vert.link_edges:
                    linked_vert = edge.other_vert(current_vert)
                    if not linked_vert.tag:
                        verts_to_check.append(linked_vert)
            islands.append(island_verts)


    # Gather and print the required information for each island
    island_info = []
    for index, island in enumerate(islands):
        min_coord, max_coord = calculate_island_bounds(island)
        center = calculate_center_point(min_coord, max_coord)
        scale = calculate_scale(min_coord, max_coord)
        general_scale = calculate_general_scale(min_coord, max_coord)
        bounds = [min_coord[2], max_coord[2]]  # Top and bottom Z-coordinates

        island_info.append({
            "center": center,
            "bounds": bounds,
            "scale": scale,
            "general_scale": general_scale
        })
        print(f"Island {index + 1}: Center {center}, Bounds {bounds}, Scale {scale}, General Scale {general_scale}")
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # ARMATURE PART
    
    # Create an armature
    bpy.ops.object.armature_add()
    armature = bpy.context.object
    armature.name = 'HairRigArmature'
    
    # Set the armature's location to the mesh origin
    armature.location = mesh_origin

    # Keep the mesh selected
    obj.select_set(True)

    # Set the armature as the active object for editing
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='EDIT')
    
    bones = armature.data.edit_bones
    # Remove the default bone
    bones.remove(bones.active)
    
    # Create the ROOT bone
    root_bone = bones.new('ROOT')
    root_bone.head = (0, 0, 0)
    root_bone.tail = (0, 0, root_bone_size)
    
    #place bone on each islands center 
  
    for index, island_data in enumerate(island_info):
        center = island_data["center"]
        bone_name = f'IslandBone_{index}'
        bone = bones.new(bone_name)
        bone.head = center
        bone.tail = (center[0], center[1], center[2] + root_bone_size)  # Setting tail above the head
  
  
  
  
  
    bpy.ops.object.mode_set(mode='OBJECT')
 
 
 # INTERFACE CLASS
 
class BONECHAIN_OT_Create(bpy.types.Operator):
     
    bl_idname = "bonechain.create"
    bl_label = "Create Bone Chain"
    bl_options = {"REGISTER", "UNDO"}
    
    root_bone_size: bpy.props.FloatProperty(
        name="Root Bone Size",
        default=1,
        description="Length of the root bone",
        min=0.1,
        max=5.0
    )
        
    def execute(self, context):
        try:
            create_bone_chain(context, root_bone_size = self.root_bone_size)
        except ValueError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        return {'FINISHED'}
        
## ------------------ SKIRT TOOLS --------------------------------------------------------

def create_skirt_chain(context, rad, chain_length, root_bone_size, num_chains, chain_angle, flare_angle, auto_rotation_step, curve_angle, edit_size):
    
    if not context.selected_objects:
        raise ValueError("No objects selected.")
    obj = context.active_object
        
    if not obj or obj.type != 'MESH':
        raise ValueError("The selected object is not a mesh.")
    
    # Save the mesh's origin point
    mesh_origin = obj.location.copy()
    
    flare_radians = math.radians(flare_angle)
    chains_dict = {}
    
   # Using the bounding box to find top and bottom Z-coordinates
    bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    top_point = max(bbox_corners, key=lambda c: c.z)
    bottom_point = min(bbox_corners, key=lambda c: c.z)

    # Calculate top and bottom centers
    top_center = Vector((top_point.x, top_point.y, top_point.z))
    bottom_center = Vector((bottom_point.x, bottom_point.y, bottom_point.z))

    # Create an armature
    bpy.ops.object.armature_add()
    armature = bpy.context.object
    armature.name = 'SkirtRigArmature'
    armature.location = mesh_origin
    
    # Keep the mesh selected
    obj.select_set(True)
    
    # Set the armature as the active object for editing
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='EDIT')

    bones = armature.data.edit_bones
    # Remove the default bone
    if "Bone" in bones:
        bones.remove(bones["Bone"])

    # Create the ROOT bone
    root_bone = bones.new('ROOT')
    root_bone.head = (0, 0, 0)
    root_bone.tail = (0, 0, root_bone_size)

    # Calculate the total length for the bone chain
    total_chain_length = (top_center.z - bottom_center.z) * edit_size
    # chain lenght variable ---------------V
    bone_length = total_chain_length / chain_length

    # Positioning and rotation of chains
    radius = rad  # Radius for positioning the chains in a circle
    if auto_rotation_step == True:
        rotation_step = math.radians(360 / num_chains)   
    else:
        rotation_step = math.radians(chain_angle)

    for chain_id in range(num_chains):
        angle = rotation_step * chain_id
        chain_start = Vector((math.cos(angle) * rad, math.sin(angle) * rad, top_center.z))
        bone_roll = -angle

        # Generate the chain letter (a, b, c, etc.) based on chain_id
        chain_letter = chr(97 + chain_id)  # ASCII 'a' is 97

        prev_bone = root_bone
        
        
        for i in range(chain_length):
            bone_name = f'skirt.{chain_letter}.{i:03d}'
            bone = bones.new(bone_name)
            bone.parent = prev_bone
            bone.use_connect = (i != 0)

            bone.head = chain_start if i == 0 else prev_bone.tail
            bone.tail = bone.head + Vector((0, 0, -bone_length))

            # Rotate bone around its Y-axis
            bone.roll = bone_roll

            prev_bone = bone

    bpy.ops.object.mode_set(mode='OBJECT')
    
    bpy.ops.object.mode_set(mode='POSE')

    flare_radians = math.radians(flare_angle)
    curve_radians = math.radians(curve_angle)

    for chain_id in range(num_chains):
        chain_letter = chr(97 + chain_id)
        cumulative_curve = 0  # Initialize the cumulative curve rotation

        for bone_id in range(chain_length):
            bone_name = f'skirt.{chain_letter}.{bone_id:03d}'
            bone = armature.pose.bones.get(bone_name)

            if bone:
                bone.rotation_mode = 'XYZ'
                
                if bone_id == 0:
                    # Apply flare angle only to the first bone in each chain
                    bone.rotation_euler[2] = -flare_radians
                else:
                    # Apply additional curve angle to subsequent bones
                    cumulative_curve += curve_radians
                    bone.rotation_euler[2] = -cumulative_curve
    
            bpy.context.view_layer.update()

    # Apply the pose as the rest pose
    bpy.ops.pose.armature_apply()

    # Switch back to object mode after rotations
    bpy.ops.object.mode_set(mode='OBJECT')
    
class BONESKIRT_OT_Create(bpy.types.Operator):
    """Create a circular bone array resembling a skirt"""
    bl_idname = "boneskirt.create"
    bl_label = "Create Bone Chain"
    bl_options = {"REGISTER", "UNDO"}
    
    chain_radius: bpy.props.FloatProperty(
        name="Skirt Radius",
        default=1,
        description="The radius of the chain}",
    )
    
    chain_angle: bpy.props.FloatProperty(
        name="Skirt Angle",
        default=45,
        description="The angle of the chain}",
    )
    
    flare_angle: bpy.props.FloatProperty(
        name="Flare Angle",
        default=0.0,
        description="Angle to flare the chains outward",
        min=-90.0,
        max=90.0  # Max flare of 90 degrees
    )
     
    curve_angle: bpy.props.FloatProperty(
        name="Curve Angle",
        default=0.0,
        description="Angle to curve the chains",
        min=-90.0,
        max=90.0  # Max flare of 90 degrees
    )
    
    chain_length: bpy.props.IntProperty(
        name="Chain Length",
        default=4,
        description="Number of bones in each chain",
        min=1,
        max=20
    )
    
    num_chains: bpy.props.IntProperty(
        name="Number Of Chains",
        default=8,
        description="Number of bone chains",
        min=1,
        max=20
    )
    
    root_bone_size: bpy.props.FloatProperty(
        name="Root Bone Size",
        default=0.5,
        description="Length of the root bone",
    )
    
    edit_size: bpy.props.FloatProperty(
        name="Skirt Size",
        default=1,
        description="Length of the skirt",
    ) 
    
    auto_rotation_step: bpy.props.BoolProperty(
        name="Auto Rotation Step",
        description="Automatically calculate the rotation step",
        default=True
    )
    
    def draw(self, context):
        layout = self.layout
        
        layout.label(text = "Skirt Properties", icon="MODIFIER_DATA")
    
        layout.prop(self, "chain_radius")
        layout.prop(self, "num_chains")
        layout.prop(self, "chain_length")
        
        layout.separator(factor=2)
        layout.label(text = "Skirt Rotation", icon="GIZMO")
        box = layout.box()
        row = box.row()
        row.prop(self, "auto_rotation_step")
        if self.auto_rotation_step == False:
            row.prop(self, "chain_angle")
        layout.prop(self, "flare_angle")
        layout.prop(self, "curve_angle")
        
        layout.separator(factor=2)
        layout.label(text = "Skirt Size", icon="BONE_DATA")
        layout.prop(self, "root_bone_size")
        layout.prop(self, "edit_size")
        
    def execute(self, context):
        try:
            create_skirt_chain(context, rad=self.chain_radius, chain_length=self.chain_length, root_bone_size=self.root_bone_size, num_chains=self.num_chains, chain_angle=self.chain_angle, flare_angle=self.flare_angle, auto_rotation_step=self.auto_rotation_step, curve_angle=self.curve_angle, edit_size = self.edit_size)
        except ValueError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        return {'FINISHED'}
    
### ------------------ BONE ROLL TOOLS AND PANEL --------------------------------------------------------   

def bone_roll_align():
     # Ensure Blender is in Edit Mode
    if bpy.context.object.mode != 'EDIT':
        return  # Exit if not in Edit Mode

    obj = bpy.context.object
    if obj.type == 'ARMATURE' and obj.data.edit_bones.active:
        active_bone = obj.data.edit_bones.active
        active_roll = active_bone.roll

        for bone in obj.data.edit_bones:
            if bone.select and bone != active_bone:
                bone.roll = active_roll

class BONEROLL_OT_Create(bpy.types.Operator):
    bl_idname = "boneroll.create"
    bl_label = "Align Bone roll"
    bl_options = {"REGISTER", "UNDO"}    
    
    
    def execute(self, context):
        bone_roll_align()
        return {'FINISHED'}
    ### ------------------ BONE FIX TOOLS AND PANEL --------------------------------------------------------   

def bone_fix(context):
    # Check if any objects are selected
    if not context.selected_objects:
        raise ValueError("No objects selected.")
    
    # Ensure the active object is an armature and it is in Pose Mode
    obj = context.active_object
    if not obj or obj.type != 'ARMATURE' or context.mode != 'POSE':
        raise ValueError("Active object must be an Armature in Pose Mode.")
    
    # Check if any pose bones are selected
    if not context.selected_pose_bones:
        raise ValueError("No pose bones selected.")

    # Iterate through selected pose bones and adjust constraints
    for b in context.selected_pose_bones:
        for c in b.constraints:
            if c.type == "STRETCH_TO":
                c.rest_length = 0

class BONEFIX_OT_Create(bpy.types.Operator):
    """Fixes all stretch to constraints on selected bones"""
    bl_idname = "bonefix.create"
    bl_label = "Fixes all stretch constraints"
    bl_options = {"REGISTER", "UNDO"}    
    
    def execute(self, context):
        try:
            bone_fix(context)
        except ValueError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        return {'FINISHED'}

### ------------------ BONE NAME TOOLS AND PANEL --------------------------------------------------------   

def bone_chain_name(context, chain_name, reverse, custom_letter, da_letter, skip_letter):
    obj = context.active_object
    # Check if an armature is selected and it's in edit mode or pose mode
    if not obj or obj.type != 'ARMATURE' or (context.mode != 'EDIT_ARMATURE' and context.mode != 'POSE'):
        raise ValueError("No armature selected or not in edit or pose mode.")
    
    armature = obj.data
    selected_bones = [bone for bone in armature.edit_bones if bone.select]

    if not selected_bones:
        raise ValueError("No bones selected.")

    # Function to get the next available letter
    def get_next_letter(existing_names, base_name):  
        letters = 'abcdefghijklmnopqrstuvwxyz'
        for letter in letters:
            test_name = f"{base_name}.{letter}.000"
            if test_name not in existing_names:
                return letter
        return 'a'  # Default to 'a' if all are taken

    # Gather existing names to avoid duplicates
    existing_names = {bone.name for bone in armature.edit_bones}

    # Determine the starting letter
    if custom_letter == True:
        letter = da_letter
    else:
        letter = get_next_letter(existing_names, chain_name)

    num_bones = len(selected_bones)
    bone_indices = range(num_bones) if not reverse else reversed(range(num_bones))

    # Rename selected bones
    for i, bone_index in enumerate(bone_indices):
        bone = selected_bones[bone_index]
        if skip_letter == True:
            bone.name = f"{chain_name}.{i:03d}"
        else:
            bone.name = f"{chain_name}.{letter}.{i:03d}"

class BONENAME_OT_Create(bpy.types.Operator):
    """Name a selected bone chain in format [name.a.000]"""
    bl_idname = "bonename.create"
    bl_label = "Bone Chain Naming"
    bl_options = {"REGISTER", "UNDO"}    
    
     
    chain_name: bpy.props.StringProperty(
        name="Name",
        default="Hair",
        description="Name of chain",
    )
    
    reverse: bpy.props.BoolProperty(
        name="Reverse Name Order",
        default=False,
        description="Order of chain",
    )
    
    custom_letter: bpy.props.BoolProperty(
        name="Custom Letter",
        default=False,
        description="Custom Letter",
    )
    
    skip_letter: bpy.props.BoolProperty(
        name="Skip Letter",
        default=False,
        description="Skip Letter",
    )
    
    da_letter: bpy.props.StringProperty(
        name="Letter",
        default="x",
        description="Custom Letter",
    )
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "chain_name")
        
        layout.separator(factor=2)
        box = layout.box()
        row = box.row()
        row.prop(self, "reverse")
        row = box.row()
        row.prop(self, "skip_letter")
        row = box.row()
        if self.skip_letter == False:
            row.prop(self, "custom_letter")
            if self.custom_letter == True:
                row.prop(self, "da_letter") 
          
       
                
        
    def execute(self, context):
        try:
            bone_chain_name(context, chain_name=self.chain_name, reverse=self.reverse, custom_letter = self.custom_letter, da_letter = self.da_letter, skip_letter = self.skip_letter)
        except ValueError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        return {'FINISHED'}
    
### ------------------ BONE CONNECT TOOLS AND PANEL --------------------------------------------------------   

def bone_chain_connect(context, num_bones):
    obj = context.active_object
    # Check if an armature is selected and it's in edit mode
    if not obj or obj.type != 'ARMATURE' or context.mode != 'EDIT_ARMATURE':
        raise ValueError("No armature selected or not in edit mode.")
    
    bpy.ops.object.mode_set(mode='EDIT')
    armature = bpy.context.object
    edit_bones = armature.data.edit_bones

    selected_bones = [bone for bone in edit_bones if bone.select]
    
    if not 1 <= len(selected_bones) <= 2:
        raise ValueError("One or two bones must be selected")

    start_bone = selected_bones[0]
    start_pos = start_bone.tail

    if len(selected_bones) == 2:
        end_pos = selected_bones[1].head
    else:
        cursor_global_pos = mathutils.Vector(bpy.context.scene.cursor.location)
        cursor_local_pos = armature.matrix_world.inverted() @ cursor_global_pos
        end_pos = cursor_local_pos

    direction = end_pos - start_pos
    segment_length = direction.length / num_bones

    new_bones = []
    for i in range(num_bones):
        new_bone = edit_bones.new(f"ChainBone_{i:03d}")
        new_bone.head = start_pos + direction.normalized() * segment_length * i
        new_bone.tail = new_bone.head + direction.normalized() * segment_length
        new_bones.append(new_bone)

    new_bones[0].parent = start_bone
    new_bones[0].use_connect = True
    for i in range(1, len(new_bones)):
        new_bones[i].parent = new_bones[i - 1]
        new_bones[i].use_connect = True
    if len(selected_bones) == 2:
        selected_bones[1].parent = new_bones[-1]
        selected_bones[1].use_connect = True

class BONECONNECT_OT_Create(bpy.types.Operator):
    """Connect two bones, or a single bone and the 3D cursor with a bone chain"""
    bl_idname = "boneconnect.create"
    bl_label = "Connect Chain"
    bl_options = {"REGISTER", "UNDO"}    
    
    num_bones: bpy.props.IntProperty(
        name="Number Of Bones",
        default=3,
        description="Number of bones in chain",
        min=1,
        max=20
    )
    
    def execute(self, context):
        try:
            bone_chain_connect(context, num_bones = self.num_bones)
        except ValueError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        return {'FINISHED'}    
    
### ------------------ ROLL ALIGN TOOLS AND PANEL --------------------------------------------------------   

def bone_roll_align(context):
    obj = context.active_object
    # Check if an armature is selected and it's in edit mode
    if not obj or obj.type != 'ARMATURE' or context.mode != 'EDIT_ARMATURE':
        raise ValueError("No armature selected or not in edit mode.")
        
     # Ensure Blender is in Edit Mode
    if bpy.context.object.mode != 'EDIT':
        return  # Exit if not in Edit Mode

    obj = bpy.context.object
    if obj.type == 'ARMATURE' and obj.data.edit_bones.active:
        active_bone = obj.data.edit_bones.active
        active_roll = active_bone.roll

        for bone in obj.data.edit_bones:
            if bone.select and bone != active_bone:
                bone.roll = active_roll

class BONEROLL_OT_Create(bpy.types.Operator):
    """Align roll of inactive bones to active bone"""
    bl_idname = "boneroll.create"
    bl_label = "Align Bone roll"
    bl_options = {"REGISTER", "UNDO"}    
    
    
    def execute(self, context):
        try:
            bone_roll_align(context)
        except ValueError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        return {'FINISHED'}     
           
### ------------------ AUTO WEIGHT TOOLS AND PANEL --------------------------------------------------------   

#Automatically recalculates weight for selected bones
def re_weight():
    pass

class BONEWEIGHT_OT_Create(bpy.types.Operator):
    bl_idname = "reweight.create"
    bl_label = "Auto Weight"
    bl_options = {"REGISTER", "UNDO"}    
    
    
    def execute(self, context):
        re_weight()
        return {'FINISHED'}     

### ------------------ DIRECTION TOOLS AND PANEL --------------------------------------------------------   

def switch_chain(context):
    
    obj = context.active_object
    # Check if an armature is selected and it's in edit mode
    if not obj or obj.type != 'ARMATURE' or context.mode != 'EDIT_ARMATURE':
        raise ValueError("No armature selected or not in edit mode.")
        
    armature = context.active_object
    if not armature or armature.type != 'ARMATURE':
        print("No armature selected.")
        return

    bpy.ops.object.mode_set(mode='EDIT')

    bones = armature.data.edit_bones
    selected_bones = [bone for bone in bones if bone.select]
    if not selected_bones:
        print("No bones selected.")
        return
    
    # Identify the first bone in the chain
    first_bone = None
    for bone in selected_bones:
        if not bone.parent or bone.parent not in selected_bones:
            first_bone = bone
            break

    # Identify the last bone in the chain
    last_bone = None
    for bone in selected_bones:
        if not any(child in selected_bones for child in bone.children):
            last_bone = bone
            break

    if not first_bone or not last_bone:
        print("Could not determine the first or last bone in the chain.")
        return

    # Store the parent of the first bone
    first_bone_parent = first_bone.parent
    
    # Switch the direction of the selected bone chain
    bpy.ops.armature.switch_direction()

    # Re-parent the new last bone (previously the first bone) to the stored parent
    new_last_bone = bones[last_bone.name]  # Refresh the reference
    new_last_bone.parent = first_bone_parent
    new_last_bone.use_connect = False 
    
class SWITCHCHAIN_OT_Create(bpy.types.Operator):
    """Switch the direction of the selected bone chain and adjust parent"""
    bl_idname = "switch.create"
    bl_label = "Switch Chain Direction"
    bl_options = {"REGISTER", "UNDO"}    
    
    
    def execute(self, context):
        try:
            switch_chain(context)
        except ValueError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        return {'FINISHED'}     
           
### ------------------ AUTO ALIGN TOOLS AND PANEL --------------------------------------------------------   

#Automatically aligns selected bones
def re_align(context):
    obj = context.active_object
    # Check if an armature is selected and it's in edit mode
    if not obj or obj.type != 'ARMATURE' or context.mode != 'EDIT_ARMATURE':
        raise ValueError("No armature selected or not in edit mode.")
        
    for eb in context.selected_editable_bones:
        parent = eb        
        v = (eb.tail - eb.head).normalized()

        while len(parent.children):
            bone = parent.children[0]
            bone.head = parent.tail
            bone.tail = parent.tail + bone.length * v
            parent = bone

class BONEALIGN_OT_Create(bpy.types.Operator):
    """Align the bones based on the rotation of the first bone in the chain"""
    bl_idname = "align.create"
    bl_label = "Auto Align"
    bl_options = {"REGISTER", "UNDO"}    
    
    
    def execute(self, context):
        try:
            re_align(context)
        except ValueError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        return {'FINISHED'}     
        
### ------------------ KEY ALl TOOLS AND PANEL --------------------------------------------------------   

def has_keyframe(action, bone_name, frame):
    for fcurve in action.fcurves:
        if bone_name in fcurve.data_path:
            for keyframe_point in fcurve.keyframe_points:
                if int(keyframe_point.co.x) == frame:
                    return True
    return False

def mark_keyframe_as_breakdown(action, bone_name, frame):
    for fcurve in action.fcurves:
        if bone_name in fcurve.data_path:
            for keyframe_point in fcurve.keyframe_points:
                if int(keyframe_point.co.x) == frame:
                    keyframe_point.type = 'BREAKDOWN'

def key_all(context, use_custom, use_range, range_start, range_end, should_skip, skip_frame):
    obj = context.active_object

    # Ensure armature is selected, we are in pose mode, and there are selected bones
    if not obj or obj.type != 'ARMATURE' or context.mode != 'POSE' or not context.selected_pose_bones:
        raise ValueError("An armature must be selected, in pose mode, with selected bones.")

    action = obj.animation_data.action if obj.animation_data else None
    if not action:
        raise ValueError("No action found for the armature.")

    frame_start = range_start if use_range else bpy.context.scene.frame_start
    frame_end = range_end if use_range else bpy.context.scene.frame_end

    for frame in range(frame_start, frame_end + 1):
        if should_skip and frame % skip_frame != 0:
            continue

        bpy.context.scene.frame_set(frame)

        for bone in context.selected_pose_bones:
            bone_name = f'pose.bones["{bone.name}"]'
            key_needed = not has_keyframe(action, bone_name, frame)

            if key_needed:
                bpy.ops.pose.transforms_clear()
                bone.keyframe_insert(data_path="location", frame=frame, group=bone.name)
                bone.keyframe_insert(data_path="scale", frame=frame, group=bone.name)
                bone.keyframe_insert(data_path="rotation_euler", frame=frame, group=bone.name)
                bone.keyframe_insert(data_path="rotation_quaternion", frame=frame, group=bone.name)
                mark_keyframe_as_breakdown(action, bone_name, frame)

            # Keying custom properties if needed
            if use_custom:
                for prop in bone.keys():
                    if key_needed:
                        bone.keyframe_insert(data_path=f'["{prop}"]', frame=frame, group=bone.name)
                        mark_keyframe_as_breakdown(action, bone_name, frame)

class KEYALL_OT_Create(bpy.types.Operator):
    """Keys bones on all frames and resets thier transforms if there is no keyframe, useful for tweakers"""
    bl_idname = "keyall.create"
    bl_label = "Auto Key All Non Keyed"
    bl_options = {"REGISTER", "UNDO"}    

    use_custom: bpy.props.BoolProperty(
        name="Key Custom Properties",
        default=False,
        description="Key Custom Properties",
        )
        
    use_range: bpy.props.BoolProperty(
        name="Use Key Range",
        default=False,
        description="Key Only In Defined Range",
        )
    
    range_start: bpy.props.IntProperty(
        name="Start", 
        default=1,
        description="Range Beginning",
        )
        
    range_end: bpy.props.IntProperty(
        name="End",
        default=250,
        description="Range End",
        )
        
    should_skip: bpy.props.BoolProperty(
        name="Custom Skip",
        default=True,
        description="Creates a gap between frames",
        )

    skip_frame: bpy.props.IntProperty(
        name="Skip Frames",
        default=2,
        max = 10,
        min = 0,
        description="How many frames to gap between frames",
        )
    
    def draw(self, context):
        layout = self.layout
        
        layout.label(text = "Auto Key Settings", icon="MODIFIER_DATA")
    
        layout.prop(self, "use_custom")
        
        layout.separator(factor=2)
        layout.label(text = "Custom Range Settings", icon="ARROW_LEFTRIGHT")
        box = layout.box()
        row = box.row()
        row.prop(self, "use_range")
        if self.use_range == True:
            row = box.row()
            row.prop(self, "range_start")
            row.prop(self, "range_end")
        row = box.row()
        row.prop(self, "should_skip")   
        if self.should_skip == True:
            row = box.row()
            row.prop(self, "skip_frame")
    
    def execute(self, context):
        try:
            key_all(context, use_custom = self.use_custom, use_range = self.use_range, range_start = self.range_start, range_end = self.range_end, should_skip = self.should_skip, skip_frame = self.skip_frame)
        except ValueError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        return {'FINISHED'}    
          
### ------------------ AUTO KEY SET AND PANEL --------------------------------------------------------   

#Automatically creates keying set for armature based on names
def auto_key_set(context):
    obj = context.active_object
    if not obj or obj.type != 'ARMATURE':
        raise ValueError("No armature selected")
    
    
   # Ensure an armature is selected and in pose mode
    if bpy.context.active_object and bpy.context.active_object.type == 'ARMATURE':
        armature = bpy.context.active_object
        if bpy.context.mode != 'POSE':
            bpy.ops.object.posemode_toggle()

        # Create a new action named "00-keying"
        action = bpy.data.actions.new("00-keying")
        
        # Ensure armature has animation data and assign the action
        if not armature.animation_data:
            armature.animation_data_create()
        armature.animation_data.action = action

        # Iterate through visible bones
        for bone in armature.pose.bones:
            if bone.bone.hide:  # Skip hidden bones
                continue

            bone_name = bone.name.upper()
            # Key location and rotation for IK, POLE, CAM bones
            if any(sub in bone_name for sub in ["IK", "POLE", "CAM"]):
                bone.keyframe_insert(data_path="location", frame=0)
                if bone.rotation_mode == 'QUATERNION':
                    bone.keyframe_insert(data_path="rotation_quaternion", frame=0)
                else:
                    bone.keyframe_insert(data_path="rotation_euler", frame=0)
            # Key custom properties for VIS and PROP bones
            elif any(sub in bone_name for sub in ["VIS", "PROP"]):
                for prop in [p for p in bone.keys() if p not in bone.bl_rna.properties]:
                    bone.keyframe_insert(data_path=f'["{prop}"]', frame=0)
            # For other bones, key location, rotation, and scale
            else:
                bone.keyframe_insert(data_path="location", frame=0)
                bone.keyframe_insert(data_path="scale", frame=0)
                if bone.rotation_mode == 'QUATERNION':
                    bone.keyframe_insert(data_path="rotation_quaternion", frame=0)
                else:
                    bone.keyframe_insert(data_path="rotation_euler", frame=0)

class AUTOKEYSET_OT_Create(bpy.types.Operator):
    """Creates a simple keying set action"""
    bl_idname = "autokeyset.create"
    bl_label = "Auto Keying Set"
    bl_options = {"REGISTER", "UNDO"}    
    
    
    def execute(self, context):
        try:
            auto_key_set(context)
        except ValueError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        return {'FINISHED'}       
    
# ======================================================
# Registration
# ======================================================

classes = (
    BONECHAIN_OT_Create,
    BONESKIRT_OT_Create,
    BONEROLL_OT_Create,
    BONENAME_OT_Create,
    BONECONNECT_OT_Create,
    BONEFIX_OT_Create,
    BONEALIGN_OT_Create,
    SWITCHCHAIN_OT_Create,
    KEYALL_OT_Create,
    AUTOKEYSET_OT_Create
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
