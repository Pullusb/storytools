# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.props import (FloatProperty,
                        BoolProperty,
                        EnumProperty,
                        StringProperty,
                        IntProperty,
                        PointerProperty,
                        FloatVectorProperty)

from ..fn import get_addon_prefs, refresh_areas
# from .properties import STORYTOOLS_PG_tool_presets


class STORYTOOLS_OT_move_collection_item(bpy.types.Operator):
    bl_idname = "storytools.move_collection_item"
    bl_label = "Move Item"
    bl_description = "Move item in list up or down"
    bl_options = {'REGISTER', 'INTERNAL'}

    # direction : bpy.props.IntProperty(default=1)
    direction : bpy.props.EnumProperty(
        items=(
            ('UP', 'Move Up', 'Move up'),
            ('DOWN', 'Move down', 'Move down'),
        ),
        default='UP',
    )

    prop_name : bpy.props.StringProperty()
    items_name : bpy.props.StringProperty()

    def execute(self, context):
        pg = getattr(get_addon_prefs(), self.prop_name)
        uilist = getattr(pg, self.items_name)
        index = pg.index

        neighbor = index + (-1 if self.direction == 'UP' else 1)
        uilist.move(neighbor, index)
        list_length = len(uilist) - 1 # (index starts at 0)
        new_index = index + (-1 if self.direction == 'UP' else 1)
        list_index = max(0, min(new_index, list_length))

        setattr(pg, 'index', list_index)
        refresh_areas()
        return {'FINISHED'}
    
## Manage tools presets
class STORYTOOLS_OT_add_toolpreset(bpy.types.Operator):
    '''Add '''
    bl_idname = "storytools.add_toolpreset"
    bl_label = "Edit Source"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        tools = get_addon_prefs().tool_presets.tools
        tools.add()
        context.area.tag_redraw()
        return {'FINISHED'}

class STORYTOOLS_OT_remove_toolpreset(bpy.types.Operator):
    '''Remove storytools Tool preset'''
    bl_idname = "storytools.remove_toolpreset"
    bl_label = "Remove toolpreset"
    bl_options = {'REGISTER', 'INTERNAL'}

    # index : bpy.props.IntProperty()

    def execute(self, context):
        pg = get_addon_prefs().tool_presets
        self.report({'INFO'}, f'Removed {pg.tools[pg.index].name}')
        pg.tools.remove(pg.index)
        context.area.tag_redraw()
        return {'FINISHED'}

class STORYTOOLS_UL_toolpreset_list(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, active_property, index):

        self.use_filter_show = False # force closed search
        layout.label(text=f'{active_property}')
        layout.label(text=item.name)
        ## display icon if using blender icons with gizmos

        # layout.operator('storytools.edit_toolpreset', text='', icon='PRESET')

    # def draw_filter(self, context, layout):
    #     row = layout.row()
    #     subrow = row.row(align=True)
    #     subrow.prop(self, "filter_name", text="") # Only show items matching this name (use ‘*’ as wildcard)

    #     # reverse order
    #     icon = 'SORT_DESC' if self.use_filter_sort_reverse else 'SORT_ASC'
    #     subrow.prop(self, "use_filter_sort_reverse", text="", icon=icon) # built-in reverse

    # def filter_items(self, context, data, propname):
    #     collec = getattr(data, propname)
    #     helper_funcs = bpy.types.UI_UL_list

    #     flt_flags = []
    #     flt_neworder = []
    #     if self.filter_name:
    #         flt_flags = helper_funcs.filter_items_by_name(self.filter_name, self.bitflag_filter_item, collec, "name",
    #                                                       reverse=self.use_filter_sort_reverse)#self.use_filter_name_reverse)
    #     return flt_flags, flt_neworder

### --- REGISTER ---

classes = (
    ## UI list
    STORYTOOLS_OT_move_collection_item,
    STORYTOOLS_OT_add_toolpreset,
    STORYTOOLS_OT_remove_toolpreset,
    STORYTOOLS_UL_toolpreset_list,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
