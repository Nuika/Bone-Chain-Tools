bl_info = {
    "name": "Bone Chain Tools",
    "author": "Nuky",
    "version": (1, 1),
    "blender": (3, 6, 0),
    "description": "Tools for editing and creating bone chains",
    "category": "Rigging",
}

from . import bone_chain_ops, bone_light_ops, panels

def register():
    bone_chain_ops.register()
    bone_light_ops.register()
    panels.register()

def unregister():
    panels.unregister()
    bone_light_ops.unregister()
    bone_chain_ops.unregister()