# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import Operator, Panel, Menu
from .fn import get_addon_prefs
# from bl_ui.utils import PresetPanel

from . import fn
from .constants import STORYBOARD_TEMPLATE_BLEND, DUAL_STORYBOARD_TEMPLATE_BLEND

class STORYTOOLS_PT_storytools_ui(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Storytools" # Gpencil
    bl_label = "Storytools"

    def draw(self, context):
        return
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
        if not ob or ob.type != 'GREASEPENCIL':
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

    def draw_header_preset(self, context):
        layout = self.layout
        layout.prop(context.space_data.overlay, "use_gpencil_grid", text='', icon='MESH_GRID')

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
        return context.object and context.object.type == 'GREASEPENCIL'

    ## Add autolock value
    # def draw_header_preset(self, context):
    #     layout = self.layout
    #     icon = 'LOCKED' if context.object.data.use_autolock_layers else 'DECORATE_UNLOCKED'
    #     layout.prop(context.object.data, 'use_autolock_layers', text='', icon=icon)
    #     # layout.prop(context.object.data, 'use_autolock_layers')

    def draw(self, context):
        layers_layout(self.layout, context.grease_pencil)

class STORYTOOLS_PT_materials_ui(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Storytools" # Gpencil
    bl_label = "Materials"
    bl_parent_id = "STORYTOOLS_PT_storytools_ui" # as_subpanel

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'GREASEPENCIL'

    def draw(self, context):
        col = self.layout.column()
        materials_layout(col, context)

class STORYTOOLS_PT_tool_ui(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Storytools" # Gpencil
    bl_label = "Tool"
    bl_parent_id = "STORYTOOLS_PT_storytools_ui" # as_subpanel

    # def draw_header_preset(self, context):
    #     layout = self.layout
    #     layout.operator("storytools.open_addon_prefs", text='', icon='PREFERENCES')

    # @classmethod
    # def poll(cls, context):
    #     return context.object and context.object.type == 'GREASEPENCIL'

    def draw(self, context):
        col = self.layout.column()
        tool_layout(self, col, context)


class STORYTOOLS_PT_gp_objects_list_options(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI' # 'HEADER'
    bl_category = "View"
    bl_label = "Options"
    bl_options = {'INSTANCED'}
    # bl_ui_units_x = 12

    def draw(self, context):
        layout = self.layout
        settings = context.scene.storytools_settings
        # layout.prop(settings, 'show_scale_figure', text='Scale Helper') # Added in overlay
        row = layout.row()
        row.label(text='Drawing List Display Toggles')
        info = row.operator('storytools.info_note', text='', icon='QUESTION', emboss=False)
        info.title = 'Display Toggles Informations'
        info.text = 'Show/hide: Define what infos you want to see in list\
                \nAutomatic: icons appear only if there is enough sidebar space'

        col = layout.column(align=True)

        col.label(text='Visibility State')
        row=col.row(align=True)
        row.prop(settings, 'show_gp_visibility', text='Show GP Visibility', expand=True)

        col.separator()

        col.label(text='In Front State')
        row=col.row(align=True)
        row.prop(settings, 'show_gp_in_front', text='Show In Front State', expand=True)
        
        col.separator()

        col.label(text='Parent State')
        row=col.row(align=True)
        row.prop(settings, 'show_gp_parent', text='Show Parent State', expand=True)

        col.separator()

        col.label(text='Multiple Users State')
        row=col.row(align=True)
        row.prop(settings, 'show_gp_users', text='Show GP users', expand=True)


""" 
class STORYTOOLS_MT_focal_presets(Menu): 
    bl_label = 'Camera Focal Display Presets' 
    preset_subdir = 'camera/focal' 
    preset_operator = 'script.execute_preset' 
    draw = bpy.types.Menu.draw_preset

class STORYTOOLS_PT_focal_presets(PresetPanel, Panel):
    bl_label = 'Camera Focal Display Presets'
    preset_subdir = 'camera/focal'
    preset_operator = 'script.execute_preset'
    preset_add_operator = 'camera.focal_preset_add'
 """

class STORYTOOLS_PT_camera_settings(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Storytools" # Gpencil
    bl_label = 'Camera Settings'
    bl_options = {'INSTANCED'}

    @classmethod
    def poll(cls, context):
        return context.scene.camera

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        cam = context.scene.camera

        if cam.data.type == 'ORTHO':
            # col.label(text='Camera is Orthographic', icon='INFO')
            col.prop(cam.data, 'ortho_scale')
        else:
            # col.label(text='Lens:')
            if cam.data.lens_unit == 'FOV':
                col.prop(cam.data, "angle")
            else:
                col.prop(cam.data, "lens")
        
        col = layout.column(align=True)
        
        row = col.row()
        row.label(text='Focal Length Presets:')
        focal_list = (18, 21, 25, 28, 35, 40, 50, 85, 135, 200)
        for i, f in enumerate(focal_list):
            if i % 2 == 0:
                row = col.row(align=True)
            row.operator('storytools.set_focal', text=f'{f} mm').lens = f
        
        col.active = cam.data.type != 'ORTHO'

        col = layout.column()
        
        col.separator()
        col.label(text='Track To Constraint:')
        ## Track To Constraints
        col = layout.column(align=True)
        existing_constraints = [c for c in cam.constraints if c.type in ('TRACK_TO', 'DAMPED_TRACK', 'LOCKED_TRACK')]
        if not existing_constraints:
            col.operator('storytools.add_track_to_constraint', text='Add Track To Target')
            emptys = [o for o in context.selected_objects if o.type == 'EMPTY']
            if emptys:
                col.label(text=f'Selected empty "{emptys[0].name}"', icon='INFO')
                col.label(text=f'will be used as track target', icon='BLANK1')
                # col.label(text=f'Deselect all empties to create a new one', icon='INFO')
        else:
            for const in existing_constraints:
                box = col.box()
                colbox = box.column(align=True)
                colbox.prop(const, 'influence')
                colbox.prop(const, 'target')
                colbox.operator('storytools.make_active_and_select', text='Select Target', icon='RESTRICT_SELECT_OFF').name = const.target.name
                if const.target and const.target.type == 'EMPTY':
                    colbox.separator()
                    colbox.label(text='Target Display:')
                    colbox.prop(const.target, 'empty_display_type', text='')
                    colbox.prop(const.target, 'empty_display_size')

            col.separator()
            col.operator('storytools.add_track_to_constraint', text='Remove Track To constraints', icon='X').remove = True
        
        ## Cam delete
        col.separator()
        row = col.row()
        row.alert = True
        row.operator('storytools.delete_camera', text='Delete Camera', icon='X')

        col.separator()
        
        row = col.row()
        row.label(text="Settings Display Toggle:")
        info = row.operator('storytools.info_note', text='', icon='QUESTION', emboss=False)
        info.title = 'Display Toggles Informations'
        info.text = 'Show/hide: Define what infos you want to see in list\
                \nAutomatic: icons appear only if there is enough sidebar space'

        row = col.row()
        row.prop(context.scene.storytools_settings, "show_cam_settings", text='Show Settings In List', expand=True)


def camera_layout(layout, context):
    col = layout
    scn = context.scene    
    #col.label(text='Camera:')

    row = col.row()
    row.template_list("STORYTOOLS_UL_camera_list", "",
        scn, "objects", scn.st_camera_props, "index", rows=3)

    col_lateral = row.column(align=True)
    # col_lateral.operator('storytools.create_camera', icon='ADD', text='') # 'PLUS'
    
    col_lateral.operator('storytools.create_camera', icon='ADD', text='')
    ## Using native operator (need to be in object mode)
    # addcam = col_lateral.operator('object.add', icon='ADD', text='')
    # addcam.type='CAMERA'
    # addcam.align='VIEW'
    # addcam.location = context.space_data.region_3d.view_matrix.inverted().translation

    ## Lens options
    col_lateral.popover('STORYTOOLS_PT_camera_settings', text='', icon='DOWNARROW_HLT')
    
    ## ! can't call lens panel, (call context.camera in property)
    # col_lateral.operator('wm.call_panel', text='', icon='TOOL_SETTINGS').name = 'DATA_PT_lens'

    if hasattr(bpy.types, 'GP_OT_draw_cam_switch'):
        if context.scene.camera and context.scene.camera.name == 'draw_cam':
            col_lateral.operator('gp.draw_cam_switch', text='', icon='LOOP_BACK')
            col_lateral.operator('gp.reset_cam_rot', text='', icon='DRIVER_ROTATIONAL_DIFFERENCE')
        elif context.scene.camera:
            col_lateral.operator('gp.draw_cam_switch', text='', icon='CON_CAMERASOLVER').cam_mode = 'draw'

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
    
    ## GP Grid toggle (now in header)
    # col_lateral.prop(context.space_data.overlay, "use_gpencil_grid", text='', icon='MESH_GRID')
    
    ## Toobar toggle (now have it's own overlay)
    # if get_addon_prefs().active_toolbar:
    #     col_lateral.prop(context.scene.storytools_settings, "show_session_toolbar", text='', icon='STATUSBAR')
    
    # col_lateral.menu("STORYTOOLS_MT_gp_objects_list_options", icon='DOWNARROW_HLT', text='')
    col_lateral.popover(panel="STORYTOOLS_PT_gp_objects_list_options", text="", icon='DOWNARROW_HLT')


def layers_layout(layout, grease_pencil):
    layer = grease_pencil.layers.active
    is_layer_active = layer is not None
    is_group_active = grease_pencil.layer_groups.active is not None

    row = layout.row()
    row.template_grease_pencil_layer_tree()

    col = row.column()
    sub = col.column(align=True)
    sub.operator_context = 'EXEC_DEFAULT'
    sub.operator("grease_pencil.layer_add", icon='ADD', text="")
    sub.operator("grease_pencil.layer_group_add", icon='NEWFOLDER', text="")
    sub.separator()

    if is_layer_active:
        sub.operator("grease_pencil.layer_remove", icon='REMOVE', text="")
    if is_group_active:
        sub.operator("grease_pencil.layer_group_remove", icon='REMOVE', text="").keep_children = True

    sub.separator()

    sub.menu("GREASE_PENCIL_MT_grease_pencil_add_layer_extra", icon='DOWNARROW_HLT', text="")

    col.separator()

    sub = col.column(align=True)
    sub.operator("grease_pencil.layer_move", icon='TRIA_UP', text="").direction = 'UP'
    sub.operator("grease_pencil.layer_move", icon='TRIA_DOWN', text="").direction = 'DOWN'

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
        # sub.operator("grease_pencil.material_isolate", icon='RESTRICT_VIEW_ON', text="").affect_visibility = True
        # sub.operator("grease_pencil.material_isolate", icon='LOCKED', text="").affect_visibility = False
    
    ## Material sync mode
    col = layout.column()
    col.prop(bpy.context.scene.storytools_settings, 'material_sync', text='')

def tool_layout(self, layout, context):
    row = layout.row(align=True)
    row.operator('storytools.align_view_to_object', text='Align View To Object')
    row.operator('storytools.opposite_view', text='', icon='FORCE_MAGNETIC') # CON_ROTLIMIT

    ## Test to see if it's worth adding as gizmo
    # layout.operator('storytools.camera_shift', text='Camera Shift')
    
    ## Set origin to bottom : disabled for now...
    ## maybe we want the origin to move down in "local space" (on GP axis depending on drawing plane)
    # layout.operator('storytools.set_origin_bottom', text='Set Origin to Bottom')

    ## -- Check for grease pencil tools addon

    if bpy.app.version < (4,2,0) and (not context.preferences.addons.get('greasepencil_tools') and not context.preferences.addons.get('greasepencil-addon')):
        ## Propose to enable built-in
        layout.separator()
        layout.label(text='GP Tools addon is disabled')
        layout.operator('preferences.addon_enable', text='Enable Grease Pencil Tools').module = 'greasepencil_tools'
        # layout.operator('preferences.addon_enable',text='Enable Grease Pencil Tools').module='greasepencil-addon' # The Dev one
    else:
        if hasattr(bpy.types, 'GP_PT_sidebarPanel'):
            ## Don't know how to auto-pin GP_tools panel, so call it's panel draw directly
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
        return context.object and context.object.type == 'GREASEPENCIL'

    @staticmethod
    def paint_settings(context):
        if hasattr(bpy.types, "VIEW3D_PT_tools_grease_pencil_v3_brush_select"):
            return bpy.types.VIEW3D_PT_tools_grease_pencil_v3_brush_select.paint_settings(context)

    def draw(self, context):
        layout = self.layout
        if not hasattr(bpy.types, "VIEW3D_PT_tools_grease_pencil_v3_brush_select"):
            layout.label(text='Could not find Brushes select class')
            return

        brush_cls = bpy.types.VIEW3D_PT_tools_grease_pencil_v3_brush_select
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
        return context.object and context.object.type == 'GREASEPENCIL'# and context.mode == 'PAINT_GREASE_PENCIL'

    def draw(self, context):
        layout = self.layout
        if not hasattr(bpy.types, "VIEW3D_PT_tools_grease_pencil_v3_brush_mixcolor"):
            return
        
        mixcolor_cls = bpy.types.VIEW3D_PT_tools_grease_pencil_v3_brush_mixcolor
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
        return context.object and context.object.type == 'GREASEPENCIL'# and context.mode == 'PAINT_GREASE_PENCIL'

    def draw(self, context):
        layout = self.layout
        if not hasattr(bpy.types, "VIEW3D_PT_tools_grease_pencil_brush_mix_palette"):
            return

        palette_cls = bpy.types.VIEW3D_PT_tools_grease_pencil_brush_mix_palette
        if not hasattr(palette_cls, "poll") or palette_cls.poll(context):
            palette_cls.draw(self, context)
        else:
            layout.label(text="Can't display this panel here!", icon="ERROR")


## Sub-panel for camera exclusion settings in camera menu, operartors in "cam_exclude_filter.py"
class STORYTOOLS_PT_camera_exclusion_settings(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Storytools"
    bl_label = "Camera Exclusions"
    bl_parent_id = "STORYTOOLS_PT_camera_settings"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.camera

    def draw_header(self, context):
        cam = context.scene.camera
        layout = self.layout
        if cam and hasattr(cam, 'exclude_props') and cam.exclude_props:
            layout.prop(cam.exclude_props, "enabled", text="")

    ## Do not appear in popover menu
    # def draw_header_preset(self, context):
    #     layout = self.layout
    #     info = layout.operator('storytools.info_note', text='', icon='QUESTION', emboss=False)
    #     info.title = 'Visibility exclusions from camera'
    #     info.text = 'List object or collection you want to hide from this camera view\
    #         \nVisibility will be restored when going into another camera that does not exclude it'

    def draw(self, context):
        layout = self.layout
        cam = context.scene.camera

        ## Make sure the camera has the property group
        if not hasattr(cam, 'exclude_props') or not cam.exclude_props:
            layout.label(text="Missing exclusion properties", icon='ERROR')
            return
        
        ## Hide lists when disabled
        # if not cam.exclude_props.enabled:
        #     return

        # Objects section
        main_col = layout.column()
        main_col.label(text="Excluded Objects:")
        
        row = main_col.row()
        row.template_list("STORYTOOLS_UL_excluded_objects", "", 
                         cam.exclude_props, "excluded_objects", 
                         cam.exclude_props, "active_object_index", 
                         rows=3)
        
        col = row.column(align=True)
        col.operator("storytools.add_excluded_object_from_selection", text="", icon='ADD')
        col.operator("storytools.search_add_excluded_object", text="", icon='VIEW_ZOOM')
        op = col.operator("storytools.remove_excluded_object", text="", icon='REMOVE')
        op.index = cam.exclude_props.active_object_index
        
        # Collections section
        # main_col = layout.column()
        main_col.label(text="Excluded Collections:")
        
        row = main_col.row()
        row.template_list("STORYTOOLS_UL_excluded_collections", "", 
                         cam.exclude_props, "excluded_collections", 
                         cam.exclude_props, "active_collection_index", 
                         rows=3)
        
        col = row.column(align=True)
        col.operator("storytools.search_add_excluded_collection", text="", icon='VIEW_ZOOM')
        op = col.operator("storytools.remove_excluded_collection", text="", icon='REMOVE')
        op.index = cam.exclude_props.active_collection_index

        main_col.active = cam.exclude_props.enabled

class STORYTOOLS_OT_info_note(Operator):
    bl_idname = "storytools.info_note"
    bl_label = "Info Note"
    bl_description = "Info Note"
    bl_options = {"REGISTER", "INTERNAL"}

    text : bpy.props.StringProperty(default='', options={'SKIP_SAVE'})
    title : bpy.props.StringProperty(default='Help', options={'SKIP_SAVE'})
    icon : bpy.props.StringProperty(default='INFO', options={'SKIP_SAVE'})

    @classmethod
    def description(self, context, properties):
        return properties.text

    def execute(self, context):
        ## Split text in list of lines
        lines = self.text.split('\n')
        fn.show_message_box(_message=lines, _title=self.title, _icon=self.icon)
        return {"FINISHED"}

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
#     # {'EDIT_GREASE_PENCIL', 'PAINT_GREASE_PENCIL','SCULPT_GREASE_PENCIL','WEIGHT_GREASE_PENCIL', 'VERTEX_GPENCIL'}
#     layout.separator()
#     prefs = get_addon_prefs()
#     layout.operator("", text='do stuff from material submenu', icon='MATERIAL')

def additional_gp_overlay_options(self, context):
    layout = self.layout
    settings = context.scene.storytools_settings
    
    layout.separator()
    layout.label(text='Scale Figure')
    
    col = layout.column()
    col.active = settings.use_scale_figure
    row = col.row(align=False)
    row.prop(settings, 'use_scale_figure', text='')
    subrow = row.row(align=True)
    subrow.prop(settings, 'scale_figure_opacity', text='Opacity')
    subrow.prop(settings, 'use_scale_figure_xray', text='', icon='XRAY')
    subrow.operator('storytools.bake_scale_figure_as_layer', text='', icon='OUTLINER_DATA_GP_LAYER')
    col.prop(settings, 'scale_figure_color', text='')
    
    # col.use_property_split = True
    col.prop(settings, 'scale_figure_type', text='Figure')
    if settings.scale_figure_type == 'HEIGHT':
        subcol = col.column(align=True)
        subcol.prop(settings, 'scale_figure_height', text='Height')
        subcol.prop(settings, 'scale_figure_subdivision', text='Subdivision')


def storyboard_file_new(self, context):
    self.layout.separator()
    op = self.layout.operator('wm.read_homefile', text="Storyboard")
    op.filepath = str(STORYBOARD_TEMPLATE_BLEND)
    op.load_ui = True
    op = self.layout.operator('wm.read_homefile', text="Storyboard Dual Window")
    op.filepath = str(DUAL_STORYBOARD_TEMPLATE_BLEND)
    op.load_ui = True


#-# REGISTER

panel_classes = (
    # STORYTOOLS_MT_focal_presets,
    # STORYTOOLS_PT_focal_presets,
    STORYTOOLS_OT_info_note,
    STORYTOOLS_PT_camera_settings,
    STORYTOOLS_PT_camera_exclusion_settings,
    STORYTOOLS_PT_gp_objects_list_options,
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

    bpy.types.TOPBAR_MT_file_new.append(storyboard_file_new)
    bpy.types.VIEW3D_PT_overlay_grease_pencil_options.append(additional_gp_overlay_options)
    # bpy.types.GPENCIL_MT_material_context_menu.append(palette_manager_menu)

def unregister():
    # bpy.types.GPENCIL_MT_material_context_menu.remove(palette_manager_menu)

    if hasattr(bpy.types, 'STORYTOOLS_PT_storytools_ui'):
        # Unregister only if already there.
        for cls in reversed(panel_classes):
            bpy.utils.unregister_class(cls)    

    bpy.utils.unregister_class(STORYTOOLS_MT_material_context_menu)

    bpy.types.TOPBAR_MT_file_new.remove(storyboard_file_new)
    bpy.types.VIEW3D_PT_overlay_grease_pencil_options.remove(additional_gp_overlay_options)
