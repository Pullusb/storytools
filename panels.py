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
        ob = context.object
        col = layout.column()
        
        camera_layout(col, context)

        object_layout(col, context)

        col.label(text='Layers:')

        ob = context.object
        if not ob or ob.type != 'GPENCIL':
            col.label(text=f'No Grease Pencil Active')
            return

        ## Layers:
        layers_layout(col, context)

        materials_layout(col, context)


        ## -- Workspace setup
        show_workspace_switch = context.window.workspace.name != 'Storyboard'
        # show_storypencil_setup = len(context.window_manager.windows) == 1 and context.preferences.addons.get('storypencil')
        # if show_workspace_switch or show_storypencil_setup:        
        #     col.separator()
        #     col.label(text='Workspace:')

        #     if show_workspace_switch:
        #         col.operator('storytools.set_storyboard_workspace', text='Storyboard Workspace', icon='WORKSPACE')

        #     if show_storypencil_setup: # Experimental Dual setup
        #         col.operator('storytools.setup_storypencil', text='Setup Storypencil (dual window)', icon='WORKSPACE')
        if show_workspace_switch:
            col.label(text='Workspace:')
            col.operator('storytools.set_storyboard_workspace', text='Storyboard Workspace', icon='WORKSPACE')

        ## -- Check for grease pencil tools addon

        # if not hasattr(bpy.types, GP_PT_sidebarPanel):
        if not context.preferences.addons.get('greasepencil_tools') and not context.preferences.addons.get('greasepencil-addon'):
            col.separator()
            col.label(text='GP Tools addon is disabled')
            col.operator('preferences.addon_enable',text='Enable Grease Pencil Tools').module='greasepencil_tools'
            # col.operator('preferences.addon_enable',text='Enable Grease Pencil Tools').module='greasepencil-addon' # The Dev one
        else:
            ## Don't know how to auto-pin GP_tools panel, so call it's panel draw directly
            # layout.separator()
            layout.label(text='Tools:')
            bpy.types.GP_PT_sidebarPanel.draw(self, context) # (Use 'self.layout', Show at the end only)


def object_layout(layout, context):
    col = layout
    scn = context.scene    
    col.label(text='Object:')
    
    row = col.row()
    row.template_list("STORYTOOLS_UL_gp_objects_list", "",
        scn, "objects", scn.gp_object_props, "index", rows=3)

    col_lateral = row.column(align=True)
    col_lateral.operator('storytools.create_object', icon='ADD', text='') # 'PLUS'

    ## Parent toggle
    if context.object:
        if context.object.parent:
            col_lateral.operator('storytools.attach_toggle', text='', icon='UNLINKED') # Detach From Camera
        else:
            col_lateral.operator('storytools.attach_toggle', text='', icon='LINKED') # Attach To Camera
    else:
        col_lateral.operator('storytools.attach_toggle', text='', icon='LINKED') # Attach To Camera
    
    col_lateral.prop(context.space_data.overlay, "use_gpencil_grid", text='', icon='MESH_GRID')
    if get_addon_prefs().active_toolbar:
        col_lateral.prop(context.scene.storytools_settings, "show_session_toolbar", text='', icon='STATUSBAR')

def layers_layout(col, context):
    gpd = context.object.data
    row=col.row()
    row.template_list("GPENCIL_UL_layer", "", gpd, "layers", gpd.layers, "active_index",
                    rows=4, sort_reverse=True, sort_lock=True)
    layer_side(row, context)


def layer_side(layout, context):
    gpd = context.object.data
    gpl = gpd.layers.active

    col = layout.column()
    sub = col.column(align=True)
    sub.operator("gpencil.layer_add", icon='ADD', text="")
    sub.operator("gpencil.layer_remove", icon='REMOVE', text="")
    # sub.separator()

    if gpl:
        sub.menu("GPENCIL_MT_layer_context_menu", icon='DOWNARROW_HLT', text="")

        if len(gpd.layers) > 1:
            # col.separator()

            sub = col.column(align=True)
            sub.operator("gpencil.layer_move", icon='TRIA_UP', text="").type = 'UP'
            sub.operator("gpencil.layer_move", icon='TRIA_DOWN', text="").type = 'DOWN'

            # col.separator()

            # sub = col.column(align=True)
            # sub.operator("gpencil.layer_isolate", icon='RESTRICT_VIEW_ON', text="").affect_visibility = True
            # sub.operator("gpencil.layer_isolate", icon='LOCKED', text="").affect_visibility = False

class STORYTOOLS_MT_material_context_menu(bpy.types.Menu):
    # bl_idname = "STORYTOOLS_MT_material_context_menu"
    bl_label = "Storyboard Material Menu"

    def draw(self, context):
        layout = self.layout
        col=layout.column()
        col.operator('storytools.load_default_palette', text='Load Base Palette')
        # col.prop(bpy.context.scene.storytools_settings, 'material_sync', text='')

def materials_layout(layout, context):
    layout = layout

    ob = context.object
    ## Material:
    layout.label(text=f'Materials:')
    
    row = layout.row()
    row.template_list("GPENCIL_UL_matslots", "", ob, "material_slots", ob, "active_material_index", rows=7)
    
    col = row.column(align=True)
    col.menu("STORYTOOLS_MT_material_context_menu", icon='COLOR', text="")
    
    ## Palette load
    # if not ob.data.materials or not ob.data.materials.get('line'):
    #     col.operator('storytools.load_default_palette', text='Load Base Palette')
    
    # col.operator('storytools.load_default_palette', text='Load Base Palette')

    ## Default side buttons

    col.separator()

    is_sortable = len(ob.material_slots) > 1

    col.operator("object.material_slot_add", icon='ADD', text="")
    col.operator("object.material_slot_remove", icon='REMOVE', text="")

    col.separator()

    col.menu("GPENCIL_MT_material_context_menu", icon='DOWNARROW_HLT', text="")

    if is_sortable:
        col.separator()

        col.operator("object.material_slot_move", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("object.material_slot_move", icon='TRIA_DOWN', text="").direction = 'DOWN'

        # col.separator()

        # sub = col.column(align=True)
        # sub.operator("gpencil.material_isolate", icon='RESTRICT_VIEW_ON', text="").affect_visibility = True
        # sub.operator("gpencil.material_isolate", icon='LOCKED', text="").affect_visibility = False
    
    ## Material sync mode
    col = layout.column()
    col.prop(bpy.context.scene.storytools_settings, 'material_sync', text='')



def camera_layout(layout, context):
    col = layout
    scn = context.scene    
    col.label(text='Camera:')
    
    if context.scene.camera:
        row = layout.row(align=True)# .split(factor=0.5)
        row.label(text='Passepartout')
        if context.scene.camera.name == 'draw_cam' and hasattr(context.scene, 'gptoolprops'):
            row.prop(context.scene.gptoolprops, 'drawcam_passepartout', text='', icon ='OBJECT_HIDDEN') 
        else:
            row.prop(context.scene.camera.data, 'show_passepartout', text='', icon ='OBJECT_HIDDEN')
        row.prop(context.scene.camera.data, 'passepartout_alpha', text='')
        # subrow = row.row()
        # subrow.prop(context.scene.camera.data, 'passepartout_alpha', text='')
        # subrow.active = context.scene.camera.data.show_passepartout

    row = col.row()
    row.template_list("STORYTOOLS_UL_camera_list", "",
        scn, "objects", scn.st_camera_props, "index", rows=3)

    col_lateral = row.column(align=True)
    # col_lateral.operator('storytools.create_camera', icon='ADD', text='') # 'PLUS'
    
    ## Using native ops (Do not pass active) TODO: create a dedicated operator (With invoke settings)
    addcam = col_lateral.operator('object.add', icon='ADD', text='')
    addcam.type='CAMERA'
    addcam.align='VIEW'
    addcam.location = context.space_data.region_3d.view_matrix.inverted().translation


    col_lateral.prop(context.scene.storytools_settings, "show_focal", text='', icon='CONE')
    
    if hasattr(bpy.types, 'GP_OT_draw_cam_switch'):
        if context.scene.camera and context.scene.camera.name == 'draw_cam':
            col_lateral.operator('gp.draw_cam_switch', text='', icon='LOOP_BACK')
            col_lateral.operator('gp.reset_cam_rot', text='', icon='DRIVER_ROTATIONAL_DIFFERENCE')
        elif context.scene.camera:
            col_lateral.operator('gp.draw_cam_switch', text='', icon='CON_CAMERASOLVER').cam_mode = 'draw'
    
    ## ! can't call lens panel, (call context.camera in property)
    # col_lateral.operator('wm.call_panel', text='', icon='TOOL_SETTINGS').name = 'DATA_PT_lens'

    ## Parent toggle
    # if context.object:
    #     if context.object.parent:
    #         col_lateral.operator('storytools.attach_toggle', text='', icon='UNLINKED') # Detach From Camera
    #     else:
    #         col_lateral.operator('storytools.attach_toggle', text='', icon='LINKED') # Attach To Camera
    # else:
    #     col_lateral.operator('storytools.attach_toggle', text='', icon='LINKED') # Attach To Camera

'''
## Old object layout
def object_layout(layout, context):
    col = layout
    # col.operator('storytools.align_with_view', icon='AXIS_FRONT')

    row = col.row()
    row.label(text='Object:')

    # col.operator('storytools.object_depth_move', icon='PLUS') # test poll
    row = col.row()
    row.operator('storytools.create_object', icon='PLUS') # 'ADD'
    row.prop(context.space_data.overlay, "use_gpencil_grid", text='', icon='MESH_GRID')

    ## Parent toggle
    if context.object:
        if context.object.parent:
            col.operator('storytools.attach_toggle', text='Detach From Camera', icon='UNLINKED')
        else:
            col.operator('storytools.attach_toggle', text='Attach To Camera', icon='LINKED')
    else:
        col.operator('storytools.attach_toggle', text='Attach To Camera', icon='LINKED')
    
    scn = context.scene        
    col.template_list("STORYTOOLS_UL_gp_objects_list", "",
        scn, "objects", scn.gp_object_props, "index", rows=3)
    ## :: listtype_name, list_id, dataptr, propname, active_dataptr, active_propname,
    ## item_dyntip_propname, rows, maxrows, type, columns, sort_reverse, sort_lock)
'''


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
    STORYTOOLS_MT_material_context_menu,
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