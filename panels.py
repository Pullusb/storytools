# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.types import Panel
from .preferences import get_addon_prefs

class STORYTOOLS_PT_storytools_ui(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Storytools" # Gpencil
    bl_label = "Storytools"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        ob = context.object
        col.operator('storytools.load_default_palette', text='Load Base Palette')
        col.label(text='Storytool panel')
        
        col.label(text='Test buttons')
        col.operator('storytools.align_with_view')
        col.operator('storytools.create_object')

        ob = context.object
        if not ob:
            return
        if ob.type == 'GPENCIL':
            gpd = ob.data

            # 
            #col.template_list("STORYTOOLS_UL_gp_objects_list", "", ob.data, "layers", ob, "active_material_index", rows=6)

            ## Plain Layer list
            col.template_list("GPENCIL_UL_layer", "", gpd, "layers", gpd.layers, "active_index",
                            rows=3, sort_reverse=True, sort_lock=True)
            ## Add plain material slot list
            # col.label(text=ob.name)
            col.label(text=f'Materials:')
            row = col.row()
            row.template_list("GPENCIL_UL_matslots", "", ob, "material_slots", ob, "active_material_index", rows=7)

        # row = col.row()
        # row.operator('catname.opsname', text='Turbo Ops', icon='SNAP_ON')


# ## function to append in a menu
# def palette_manager_menu(self, context):
#     """Palette menu to append in existing menu"""
#     # GPENCIL_MT_material_context_menu
#     layout = self.layout
#     # {'EDIT_GPENCIL', 'PAINT_GPENCIL','SCULPT_GPENCIL','WEIGHT_GPENCIL', 'VERTEX_GPENCIL'}
#     layout.separator()
#     prefs = get_addon_prefs()
#     layout.operator("", text='do stuff from material submenu', icon='MATERIAL')

#-# REGISTER

classes=(
STORYTOOLS_PT_storytools_ui,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)
    # bpy.types.GPENCIL_MT_material_context_menu.append(palette_manager_menu)

def unregister():
    # bpy.types.GPENCIL_MT_material_context_menu.remove(palette_manager_menu)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)