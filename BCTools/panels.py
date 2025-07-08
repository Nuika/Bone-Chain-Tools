import bpy
from bpy.types import Panel

class VIEW3D_PT_Bone_Hair_Tools(Panel):
    bl_label = "Bone Chain Tools"
    bl_category = "Bone Chain Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_order = 0
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        # Bone Build Tools
        box = layout.box()
        box.label(text="Bone Build Tools")
        col = box.column(align=True)
        col.operator("bonechain.create", text="Build Hair Rig", icon="NOCURVE")
        col.operator("boneskirt.create", text="Build Skirt Rig", icon="SPHERECURVE")
        col.operator("boneconnect.create", text="Connect Chain", icon="LIBRARY_DATA_DIRECT")

        # Bone Edit Tools
        box = layout.box()
        box.label(text="Bone Edit Tools")
        col = box.column(align=True)
        col.operator("boneroll.create", text="Align Roll", icon="SNAP_MIDPOINT")
        col.operator("bonefix.create", text="Fix Constraints", icon="TOOL_SETTINGS")
        col.operator("align.create", text="Align Bones", icon="CURVE_PATH")
        col.operator("bonename.create", text="Name Chain", icon="OUTLINER_OB_FONT")
        col.operator("switch.create", text="Switch Chain Direction", icon="FILE_REFRESH")
        
        # Animation Edit Tools
        box = layout.box()
        box.label(text="Animation Tools")
        col = box.column(align=True)
        col.operator("autokeyset.create", text="Auto Keying Set", icon="KEY_HLT")
        col.operator("keyall.create", text="Key All", icon="KEYINGSET")

class VIEW3D_PT_Light_Tools(Panel):
    bl_idname = "VIEW3D_PT_Light_Tools"
    bl_label = "Bone Light Tools"
    bl_category = "Bone Chain Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_order = 1
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.label(text="Light Tools")
        col = box.column(align=True)
        col.operator("bonelight.toggle_node_input", text="Switch Light Mode", icon="AREA_SWAP")
        col.operator("bonelight.add_low_affector", text="Add Affector LOW", icon="IPO_SINE")
        col.operator("bonelight.add_high_affector", text="Add Affector HIGH", icon="IPO_QUAD")

        
        box = layout.box()
        box.label(text="Light Setup")
        col = box.column(align=True)
        col.alert = True  # Makes the button red
        col.operator("bonelight.add_system", icon='TRASH')  # Optional: Add trash icon

classes = (VIEW3D_PT_Bone_Hair_Tools, VIEW3D_PT_Light_Tools)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)