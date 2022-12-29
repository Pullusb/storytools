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
        
        # col.operator('storytools.align_with_view', icon='AXIS_FRONT')

        ## Objects
        # col.label(text='Object:')
        row = col.row()
        row.label(text='Object:')

        # col.operator('storytools.object_depth_move', icon='PLUS') # test poll
        row = col.row()
        row.operator('storytools.create_object', icon='PLUS') # 'ADD'
        row.prop(context.space_data.overlay, "use_gpencil_grid", text='', icon='MESH_GRID')

        if context.object:
            if context.object.parent:
                col.operator('storytools.attach_toggle', text='Detach From Camera', icon='UNLINKED')
            else:
                col.operator('storytools.attach_toggle', text='Attach To Camera', icon='LINKED')
        else:
            col.operator('storytools.attach_toggle', text='Attach To Camera', icon='LINKED')
        
        scn = context.scene        
        col.template_list("STORYTOOLS_UL_gp_objects_list", "",
            scn, "objects", scn.gp_object_props, "index", rows=6)
        ## :: listtype_name, list_id, dataptr, propname, active_dataptr, active_propname,
        ## item_dyntip_propname, rows, maxrows, type, columns, sort_reverse, sort_lock) 

        col.label(text='Layers:')

        ob = context.object
        if not ob or ob.type != 'GPENCIL':
            col.label(text=f'No Grease Pencil Active')
            return
        gpd = ob.data
        
        ## Layers:
        col.template_list("GPENCIL_UL_layer", "", gpd, "layers", gpd.layers, "active_index",
                        rows=3, sort_reverse=True, sort_lock=True)
        
        ## Material:
        col.label(text=f'Materials:')
        row = col.row()
        row.template_list("GPENCIL_UL_matslots", "", ob, "material_slots", ob, "active_material_index", rows=7)
    

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