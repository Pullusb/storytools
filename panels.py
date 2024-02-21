# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.types import Context, Panel, Menu
from .fn import get_addon_prefs


class STORYTOOLS_PT_storytools_ui(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Storytools" # Gpencil
    bl_label = "Storytools"

    def draw(self, context):
        
        """ # Old
        layout = self.layout
        ob = context.object
        col = layout.column()
        # settings = context.scene.storytools_settings
        # row = col.row()
        # if not settings.show_camera_panel:
        #     row.prop(settings, 'show_camera_panel', text='', icon='DISCLOSURE_TRI_RIGHT', emboss=False)
        #     row.label(text='Cameras')
        #     # col.prop(settings, 'show_camera_panel', icon='DISCLOSURE_TRI_RIGHT', emboss=False)
        # else:
        #     row.prop(settings, 'show_camera_panel', text='', icon='DISCLOSURE_TRI_DOWN', emboss=False)
        #     row.label(text='Cameras:')
        #     # col.prop(settings, 'show_camera_panel', icon='DISCLOSURE_TRI_DOWN', emboss=False)
        #     camera_layout(col, context)

        # if context.scene.camera:
        #     row = col.row(align=True)
        #     row.label(text='Passepartout')
        #     if context.scene.camera.name == 'draw_cam' and hasattr(context.scene, 'gptoolprops'):
        #         row.prop(context.scene.gptoolprops, 'drawcam_passepartout', text='', icon ='OBJECT_HIDDEN') 
        #     else:
        #         row.prop(context.scene.camera.data, 'show_passepartout', text='', icon ='OBJECT_HIDDEN')
        #     row.prop(context.scene.camera.data, 'passepartout_alpha', text='')

        # col.label(text='Drawings:') # Objects, Grease Pencils
        # object_layout(col, context)


        col.label(text='Layers:')
        ob = context.object
        if not ob or ob.type != 'GPENCIL':
            col.label(text=f'No Grease Pencil Active')
            return

        ## Layers:
        layers_layout(col, context)

        materials_layout(col, context)

        tool_layout(self, col, context)
        """


class STORYTOOLS_PT_camera_ui(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Storytools" # Gpencil
    bl_label = "Camera"
    bl_parent_id = "STORYTOOLS_PT_storytools_ui" # as_subpanel
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header_preset(self, context):
        layout = self.layout
        if context.scene.camera:
            row = layout.row(align=True)
            # row.label(text='Passepartout')
            if context.scene.camera.name == 'draw_cam' and hasattr(context.scene, 'gptoolprops'):
                row.prop(context.scene.gptoolprops, 'drawcam_passepartout', text='', icon ='OBJECT_HIDDEN') 
            else:
                row.prop(context.scene.camera.data, 'show_passepartout', text='', icon ='OBJECT_HIDDEN')
            row.prop(context.scene.camera.data, 'passepartout_alpha', text='')
        else:
            layout.label(text='No active camera')

    def draw(self, context):
        col = self.layout.column()
        camera_layout(col, context)

class STORYTOOLS_PT_drawings_ui(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Storytools" # Gpencil
    bl_label = "Drawings"
    bl_parent_id = "STORYTOOLS_PT_storytools_ui" # as_subpanel

    def draw(self, context):
        col = self.layout.column()
        object_layout(col, context)

class STORYTOOLS_PT_layers_ui(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Storytools" # Gpencil
    bl_label = "Layers"
    bl_parent_id = "STORYTOOLS_PT_storytools_ui" # as_subpanel

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'GPENCIL'

    def draw(self, context):
        col = self.layout.column()
        layers_layout(col, context)

class STORYTOOLS_PT_materials_ui(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Storytools" # Gpencil
    bl_label = "Materials"
    bl_parent_id = "STORYTOOLS_PT_storytools_ui" # as_subpanel

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'GPENCIL'

    def draw(self, context):
        col = self.layout.column()
        materials_layout(col, context)

class STORYTOOLS_PT_tool_ui(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Storytools" # Gpencil
    bl_label = "Tool"
    bl_parent_id = "STORYTOOLS_PT_storytools_ui" # as_subpanel

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'GPENCIL'

    def draw(self, context):
        col = self.layout.column()
        tool_layout(self, col, context)

class STORYTOOLS_MT_gp_objects_list_options(Menu):
    bl_label = "Options"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.storytools_settings
        layout.prop(settings, 'show_gp_users')
        layout.prop(settings, 'show_gp_parent')
        layout.prop(settings, 'show_gp_in_front')
        # layout.operator("...", icon="FILE_REFRESH", text="Refresh")

def camera_layout(layout, context):
    col = layout
    scn = context.scene    
    #col.label(text='Camera:')

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


def object_layout(layout, context):
    col = layout
    scn = context.scene    
    
    row = col.row()
    row.template_list("STORYTOOLS_UL_gp_objects_list", "",
        scn, "objects", scn.gp_object_props, "index", rows=4)

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
    
    col_lateral.menu("STORYTOOLS_MT_gp_objects_list_options", icon='DOWNARROW_HLT', text='')

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

def tool_layout(self, layout, context):
    ## -- Workspace setup
    show_workspace_switch = context.window.workspace.name != 'Storyboard'
    # show_storypencil_setup = len(context.window_manager.windows) == 1 and context.preferences.addons.get('storypencil')
    # if show_workspace_switch or show_storypencil_setup:        
    #     layout.separator()
    #     layout.label(text='Workspace:')

    #     if show_workspace_switch:
    #         layout.operator('storytools.set_storyboard_workspace', text='Storyboard Workspace', icon='WORKSPACE')

    #     if show_storypencil_setup: # Experimental Dual setup
    #         layout.operator('storytools.setup_storypencil', text='Setup Storypencil (dual window)', icon='WORKSPACE')
    if show_workspace_switch:
        layout.label(text='Workspace:')
        layout.operator('storytools.set_storyboard_workspace', text='Storyboard Workspace', icon='WORKSPACE')

    ## -- Check for grease pencil tools addon

    # if not hasattr(bpy.types, GP_PT_sidebarPanel):
    if not context.preferences.addons.get('greasepencil_tools') and not context.preferences.addons.get('greasepencil-addon'):
        layout.separator()
        layout.label(text='GP Tools addon is disabled')
        layout.operator('preferences.addon_enable', text='Enable Grease Pencil Tools').module = 'greasepencil_tools'
        # layout.operator('preferences.addon_enable',text='Enable Grease Pencil Tools').module='greasepencil-addon' # The Dev one
    else:
        ## Don't know how to auto-pin GP_tools panel, so call it's panel draw directly
        # layout.separator()
        layout.label(text='Tools:')
        bpy.types.GP_PT_sidebarPanel.draw(self, context) # (Use 'self.layout', Show at the end only)

class STORYTOOLS_MT_material_context_menu(bpy.types.Menu):
    # bl_idname = "STORYTOOLS_MT_material_context_menu"
    bl_label = "Storyboard Material Menu"

    def draw(self, context):
        layout = self.layout
        col=layout.column()
        col.operator('storytools.load_default_palette', text='Load Base Palette')
        # col.prop(bpy.context.scene.storytools_settings, 'material_sync', text='')

class STORYTOOLS_PT_brushes_ui(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Storytools" # Gpencil
    bl_label = "Brushes"
    bl_parent_id = "STORYTOOLS_PT_storytools_ui" # as_subpanel
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        # Check draw mode to hide panel when not in draw (or just display message ?)
        return context.object and context.object.type == 'GPENCIL'# and context.mode == 'PAINT_GPENCIL'

    def draw(self, context):
        layout = self.layout
        if not hasattr(bpy.types, "VIEW3D_PT_tools_grease_pencil_brush_select"):
            layout.label(text='could not found Brushes select class')
            return

        brush_cls = bpy.types.VIEW3D_PT_tools_grease_pencil_brush_select
        if not hasattr(brush_cls, "poll") or brush_cls.poll(context):
            brush_cls.draw(self, context)
        else:
            layout.label(text="Need a GPencil object in Draw mode", icon="INFO")

class STORYTOOLS_PT_colors_ui(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Storytools" # Gpencil
    bl_label = "Colors"
    bl_parent_id = "STORYTOOLS_PT_storytools_ui" # as_subpanel
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        # Check draw mode to hide panel when not in draw (or just display message ?)
        return context.object and context.object.type == 'GPENCIL'# and context.mode == 'PAINT_GPENCIL'

    def draw(self, context):
        layout = self.layout
        if not hasattr(bpy.types, "VIEW3D_PT_tools_grease_pencil_brush_mixcolor"):
            return
        
        mixcolor_cls = bpy.types.VIEW3D_PT_tools_grease_pencil_brush_mixcolor
        if not hasattr(mixcolor_cls, "poll") or mixcolor_cls.poll(context):
            mixcolor_cls.draw(self, context)
        else:
            layout.label(text="Can't display this panel here!", icon="ERROR")

class STORYTOOLS_PT_palette_ui(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Storytools" # Gpencil
    bl_label = "Palette"
    bl_parent_id = "STORYTOOLS_PT_storytools_ui" # as_subpanel
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        # Check draw mode to hide panel when not in draw (or just display message ?)
        return context.object and context.object.type == 'GPENCIL'# and context.mode == 'PAINT_GPENCIL'

    def draw(self, context):
        layout = self.layout
        if not hasattr(bpy.types, "VIEW3D_PT_tools_grease_pencil_brush_mix_palette"):
            return

        palette_cls = bpy.types.VIEW3D_PT_tools_grease_pencil_brush_mix_palette
        if not hasattr(palette_cls, "poll") or palette_cls.poll(context):
            palette_cls.draw(self, context)
        else:
            layout.label(text="Can't display this panel here!", icon="ERROR")

# class DummyPanel:
#     def __init__(self, layout):
#         self.layout = layout



# def palette_layout(layout, context):
#     dummy_panel = DummyPanel(layout)
#     if hasattr(bpy.types, "VIEW3D_PT_tools_grease_pencil_brush_mix_palette"):
#         if not hasattr(
#             bpy.types.VIEW3D_PT_tools_grease_pencil_brush_mix_palette, "poll"
#         ) or bpy.types.VIEW3D_PT_tools_grease_pencil_brush_mix_palette.poll(context):
#             bpy.types.VIEW3D_PT_tools_grease_pencil_brush_mix_palette.draw(
#                 dummy_panel, context
#             )
#         else:
#             layout.label(text="Can't display this panel here!", icon="ERROR")


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

panel_classes = (
    STORYTOOLS_MT_gp_objects_list_options,
    STORYTOOLS_PT_storytools_ui,
    STORYTOOLS_PT_camera_ui,
    STORYTOOLS_PT_drawings_ui,
    STORYTOOLS_PT_layers_ui,
    STORYTOOLS_PT_materials_ui,
    STORYTOOLS_PT_brushes_ui, # Reference native panel
    STORYTOOLS_PT_colors_ui, # Reference native panel
    STORYTOOLS_PT_palette_ui, # Reference native panel
    STORYTOOLS_PT_tool_ui,
)


def register(): 
    bpy.utils.register_class(STORYTOOLS_MT_material_context_menu)
    
    if get_addon_prefs().show_sidebar_ui:
        # Register only if needed
        for cls in panel_classes:
            bpy.utils.register_class(cls)    

    # bpy.types.GPENCIL_MT_material_context_menu.append(palette_manager_menu)

def unregister():
    # bpy.types.GPENCIL_MT_material_context_menu.remove(palette_manager_menu)

    if hasattr(bpy.types, 'STORYTOOLS_PT_storytools_ui'):
        # Unregister only if already there.
        for cls in reversed(panel_classes):
            bpy.utils.unregister_class(cls)    

    bpy.utils.unregister_class(STORYTOOLS_MT_material_context_menu)