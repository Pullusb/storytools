# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
# import json
# from pathlib import Path
from .preferences import get_addon_prefs
from . import fn

class STORYTOOLS_OT_load_default_palette(bpy.types.Operator):
    bl_idname = "storytools.load_default_palette"
    bl_label = "Load basic palette"
    bl_description = "Load a material palette on the current GP object\nif material name already exists in scene it will uses these"
    bl_options = {"REGISTER", "INTERNAL"}

    # path_to_pal : bpy.props.StringProperty(name="paht to palette", description="path to the palette", default="")
    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'GPENCIL'

    def execute(self, context):
        # Cleanup
        bpy.ops.object.material_slot_remove_unused()
        
        # line_mat = bpy.data.materials.get('line')

        ## replace
        #Rename default solid stroke if still there
        line = context.object.data.materials.get('Black')
        if line:
            line.name = 'line'
        if not line:
            line = context.object.data.materials.get('Solid Stroke')
            if line:
                line.name = 'line'

        # load json
        # pfp = Path(bpy.path.abspath(get_addon_prefs().palette_path))
        
        """
        pfp = Path(__file__).parent / 'palettes'
        print('pfp: ', pfp)
        
        if not pfp.exists():
            self.report({'ERROR'}, f'Palette path not found')
            return {"CANCELLED"}

        base = pfp / 'base.json'
        if not base.exists():
            self.report({'ERROR'}, f'base.json palette not found in {pfp.as_posix()}')
            return {"CANCELLED"}
        """

        ## maybe move up all addition so it fit order ?
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