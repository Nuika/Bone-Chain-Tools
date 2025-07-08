import bpy
from bpy.types import Operator

# ======================================================
# Bone Light Tools (Remove System)
# ======================================================

class BONELIGHT_OT_AddSystem(bpy.types.Operator):
    """Remove entire lighting setup"""
    bl_idname = "bonelight.add_system"
    bl_label = "Clear Light System"
    bl_options = {'REGISTER', 'UNDO'}


    
    def execute(self, context):
        # List of names to remove (collections and view layers)
        names_to_remove = ["Background", "Affector LOW", "Affector HIGH", "Additional"]
        
        # Remove collections
        for collection in list(bpy.data.collections):
            if collection.name in names_to_remove:
                # Recursively remove collection and its children
                self.remove_collection(collection)
        
        # Remove view layers
        for view_layer in list(context.scene.view_layers):
            if view_layer.name in names_to_remove:
                context.scene.view_layers.remove(view_layer)
                
        self.report({'INFO'}, "Cleared light system collections and view layers")
        return {'FINISHED'}
    
    def remove_collection(self, collection):
        # Recursively remove all objects in the collection and its children
        for child_collection in list(collection.children):
            self.remove_collection(child_collection)
        
        # Remove all objects from the collection
        for obj in list(collection.objects):
            bpy.data.objects.remove(obj)
        
        # Remove the collection itself
        bpy.data.collections.remove(collection)

# ======================================================
# Light Mode Toggling Functionality 
# ======================================================

class BONELIGHT_OT_ToggleNodeInput(Operator):
    """Switch quickly between custom and basic lighting"""
    bl_idname = "bonelight.toggle_node_input"
    bl_label = "Toggle Node Input"
    bl_options = {'REGISTER', 'UNDO'}
    

    render_node_name: bpy.props.StringProperty(default="Render Layers Clean")
    group_node_name: bpy.props.StringProperty(default="Super Composite")
    target_nodes: bpy.props.StringProperty(default="Composite Switch")

    def execute(self, context):
        # Force-enable compositor nodes if disabled
        if not context.scene.use_nodes:
            context.scene.use_nodes = True
            self.report({'INFO'}, "Enabled compositor nodes")
        node_tree = context.scene.node_tree

        # Validate nodes
        render_node = node_tree.nodes.get(self.render_node_name)
        group_node = node_tree.nodes.get(self.group_node_name)
        target_names = [name.strip() for name in self.target_nodes.split(",")]
        target_nodes = [node_tree.nodes.get(name) for name in target_names]

        required_nodes = [self.render_node_name, self.group_node_name, *self.target_nodes.split(",")]
        missing = [name for name in required_nodes if not node_tree.nodes.get(name)]
        
        if missing:
            self.report({'ERROR'}, f"Missing nodes: {', '.join(missing)}")
            return {'CANCELLED'}

        # Check current connected source
        current_source = None
        for link in node_tree.links:
            if link.to_node in target_nodes and link.to_socket.name == "Image":
                current_source = link.from_node
                break

        # Disconnect all targets
        for link in node_tree.links[:]:
            if link.to_node in target_nodes and link.to_socket.name == "Image":
                node_tree.links.remove(link)

        # Switch source
        new_source = group_node if current_source == render_node else render_node
        status = "Bone Lighting" if new_source == group_node else "Default"

        # Reconnect to all targets
        for target in target_nodes:
            node_tree.links.new(new_source.outputs["Image"], target.inputs["Image"])

        self.report({'INFO'}, f"Switched to {status}")
        return {'FINISHED'}

# ======================================================
# Low Affector Creation
# ======================================================

class BONELIGHT_OT_AddAffectorLow(bpy.types.Operator):
    """Adds a LOW affector, settings have to be configured in geo nodes"""
    bl_idname = "bonelight.add_low_affector"
    bl_label = "Add Affector LOW"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Create a new UV sphere
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, enter_editmode=False)
        sphere = context.active_object
        sphere.name = "Affector Basic"

        # Apply scale transform
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

        # Get or create the "Affector LOW" collection
        collection = bpy.data.collections.get("Affector LOW")
        if not collection:
            collection = bpy.data.collections.new("Affector LOW")
            context.scene.collection.children.link(collection)
        
        # Link sphere to collection and view layer
        if sphere.name not in collection.objects:
            if sphere.users_collection:  # Remove from existing collections
                for col in sphere.users_collection:
                    col.objects.unlink(sphere)
            collection.objects.link(sphere)

         # Add Geometry Nodes modifier (using existing node group)
        shadow_affector_group = bpy.data.node_groups.get("Shadow Affector")
        if shadow_affector_group:
            # Remove any existing modifiers of the same name
            for mod in sphere.modifiers:
                if mod.name == "Shadow Affector":
                    sphere.modifiers.remove(mod)
            
            # Add new modifier with the existing node group
            gn_mod = sphere.modifiers.new("Shadow Affector", 'NODES')
            gn_mod.node_group = shadow_affector_group
        else:
            self.report({'WARNING'}, "Geometry Node Group 'Shadow Affector' not found")

        # Assign material
        shadow_mat = bpy.data.materials.get("Shadow Normal")
        if shadow_mat:
            if not sphere.data.materials:
                sphere.data.materials.append(shadow_mat)
            else:
                sphere.data.materials[0] = shadow_mat
        else:
            self.report({'WARNING'}, "Material 'Shadow Normal' not found")

        # Rename with sequential number
        base_name = "Affector Basic"
        counter = 1
        while True:
            new_name = f"{base_name} {counter}"
            if new_name not in bpy.data.objects:
                sphere.name = new_name
                break
            counter += 1

        # Set scale to 0.13 and apply
        sphere.scale = (0.13, 0.13, 0.13)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

        self.report({'INFO'}, f"Added {sphere.name} to Affector LOW")
        return {'FINISHED'}

# ======================================================
# High Affector Creation
# ======================================================

class BONELIGHT_OT_AddAffectorHigh(bpy.types.Operator):
    """Adds a HIGH affector, settings have to be configured in geo nodes"""
    bl_idname = "bonelight.add_high_affector"
    bl_label = "Add Affector HIGH"
    bl_options = {'REGISTER', 'UNDO'}


    def execute(self, context):
        # Create a new UV sphere
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, enter_editmode=False)
        sphere = context.active_object
        sphere.name = "Affector Basic"

        # Apply scale transform
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

        # Get or create the "Affector LOW" collection
        collection = bpy.data.collections.get("Affector HIGH")
        if not collection:
            collection = bpy.data.collections.new("Affector HIGH")
            context.scene.collection.children.link(collection)
        
        # Link sphere to collection and view layer
        if sphere.name not in collection.objects:
            if sphere.users_collection:  # Remove from existing collections
                for col in sphere.users_collection:
                    col.objects.unlink(sphere)
            collection.objects.link(sphere)

         # Add Geometry Nodes modifier (using existing node group)
        shadow_affector_group = bpy.data.node_groups.get("Shadow Affector")
        if shadow_affector_group:
            # Remove any existing modifiers of the same name
            for mod in sphere.modifiers:
                if mod.name == "Shadow Affector":
                    sphere.modifiers.remove(mod)
            
            # Add new modifier with the existing node group
            gn_mod = sphere.modifiers.new("Shadow Affector", 'NODES')
            gn_mod.node_group = shadow_affector_group
        else:
            self.report({'WARNING'}, "Geometry Node Group 'Shadow Affector' not found")

        # Assign material
        shadow_mat = bpy.data.materials.get("Shadow Normal")
        if shadow_mat:
            if not sphere.data.materials:
                sphere.data.materials.append(shadow_mat)
            else:
                sphere.data.materials[0] = shadow_mat
        else:
            self.report({'WARNING'}, "Material 'Shadow Normal' not found")

        # Rename with sequential number
        base_name = "Affector Basic"
        counter = 1
        while True:
            new_name = f"{base_name} {counter}"
            if new_name not in bpy.data.objects:
                sphere.name = new_name
                break
            counter += 1

        # Set scale to 0.13 and apply
        sphere.scale = (0.13, 0.13, 0.13)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

        self.report({'INFO'}, f"Added {sphere.name} to Affector HIGH")
        return {'FINISHED'}
    
# ======================================================
# Registration
# ======================================================

classes = (
    BONELIGHT_OT_AddSystem,
    BONELIGHT_OT_ToggleNodeInput,
    BONELIGHT_OT_AddAffectorLow,
    BONELIGHT_OT_AddAffectorHigh,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)