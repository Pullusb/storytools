# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
# import json
# from pathlib import Path
from .. import fn

class STORYTOOLS_OT_load_default_palette(bpy.types.Operator):
    bl_idname = "storytools.load_default_palette"
    bl_label = "Load basic palette"
    bl_description = "Load the default material stack on the current GP object\
        \n(customizable in addon preferences 'GP Settings' tab)\
        \nif material name already exists in scene it will uses these"
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'GREASEPENCIL'

    def execute(self, context):
        # Cleanup
        bpy.ops.object.material_slot_remove_unused()
        fn.load_default_palette(ob=context.object)
        self.report({'INFO'}, f'Loaded base Palette')
        return {"FINISHED"}
    

classes=(
STORYTOOLS_OT_load_default_palette,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)