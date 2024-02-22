# SPDX-License-Identifier: GPL-2.0-or-later

# Gizmo doc

import bpy
from bpy.types import (
    Operator,
    GizmoGroup,
    Gizmo
    )

from mathutils import Matrix, Vector
from .fn import get_addon_prefs
from . import fn


# class CAMERA_GGT_lock_gizmo(Gizmo):
#     bl_idname = "CAMERA_GGT_lock_gizmo"
#     bl_target_properties = (
#         {"id": "lock_camera", "type": 'BOOLEAN'},
#     )

#     def draw(self, context):
#         self.draw_icon('LOCK_VIEW_ON', color=(0.7, 0.7, 0.7))

#     def draw_select(self, context, select_id):
#         self.draw_icon('LOCK_VIEW_ON', color=(1.0, 1.0, 1.0))

#     def invoke(self, context, event):
#         context.space_data.lock_camera = not context.space_data.lock_camera
#         return {'FINISHED'}

## prop tester
# gz.use_draw_scale = True # already True
# for att in ['group',
#             'matrix_offset',
#             'use_draw_value',
#             'use_grab_cursor',
#             'use_tooltip',
#             'line_width']:
#     print(att, getattr(gz, att))

# alpha
# alpha_highlight
# bl_idname
# color
# color_highlight
# group
# hide
# hide_keymap
# hide_select
# is_highlight
# is_modal
# line_width
# matrix_basis
# matrix_offset
# matrix_space
# matrix_world
# properties
# rna_type
# scale_basis
# select
# select_bias
# use_draw_hover
# use_draw_modal
# use_draw_offset_scale
# use_draw_scale
# use_draw_value
# use_event_handle_all
# use_grab_cursor
# use_operator_tool_properties
# use_select_background
# use_tooltip

def set_gizmo_settings(gz, icon,
        color=(0.0, 0.0, 0.0),
        color_highlight=(0.5, 0.5, 0.5),
        alpha=0.7,
        alpha_highlight=0.7, # 0.1
        show_drag=False,
        draw_options={'BACKDROP', 'OUTLINE'},
        scale_basis=24): # scale_basis default: 14
    gz.icon = icon
    # default 0.0
    gz.color = color
    # default 0.5
    gz.color_highlight = color_highlight
    gz.alpha = alpha
    gz.alpha_highlight = alpha_highlight
    gz.show_drag = show_drag
    gz.draw_options = draw_options
    gz.scale_basis = scale_basis
    gz.use_draw_offset_scale = True
    # gz.line_width = 1.0 # no affect on 2D gizmo ?

class STORYTOOLS_GGT_toolbar(GizmoGroup):
    # bl_idname = "STORYTOOLS_GGT_toolbar"
    bl_label = "Story Tool Bar"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'PERSISTENT', 'SCALE'} # SHOW_MODAL_ALL ? 

    @classmethod
    def poll(cls, context):
        ## To only show in camera
        # return context.space_data.region_3d.view_perspective == 'CAMERA'
        return True

    def setup(self, context):
        ## --- Object

        self.object_gizmos = []
        
        ## Object Pan
        self.gz_ob_pan = self.gizmos.new("GIZMO_GT_button_2d")
        set_gizmo_settings(self.gz_ob_pan, 'VIEW_PAN', show_drag=True)
        props = self.gz_ob_pan.target_set_operator("storytools.object_pan") 
        self.object_gizmos.append(self.gz_ob_pan)
        
        ## Object Depth
        self.gz_ob_depth = self.gizmos.new("GIZMO_GT_button_2d")
        set_gizmo_settings(self.gz_ob_depth, 'EMPTY_SINGLE_ARROW', show_drag=True) # 
        props = self.gz_ob_depth.target_set_operator("storytools.object_depth_move")
        self.object_gizmos.append(self.gz_ob_depth)

        ## Object Scale
        self.gz_ob_scale = self.gizmos.new("GIZMO_GT_button_2d")
        set_gizmo_settings(self.gz_ob_scale, 'FULLSCREEN_ENTER', show_drag=True)
        props = self.gz_ob_scale.target_set_operator("storytools.object_scale")
        self.object_gizmos.append(self.gz_ob_scale)

        ## Object Align to view
        self.gz_ob_align_to_view = self.gizmos.new("GIZMO_GT_button_2d")
        set_gizmo_settings(self.gz_ob_align_to_view, 'AXIS_FRONT')
        props = self.gz_ob_align_to_view.target_set_operator("storytools.align_with_view")
        self.object_gizmos.append(self.gz_ob_align_to_view)
        
        ## Object key transform
        self.gz_key_ob = self.gizmos.new("GIZMO_GT_button_2d")
        set_gizmo_settings(self.gz_key_ob, 'DECORATE_KEYFRAME')
        props = self.gz_key_ob.target_set_operator("storytools.object_key_transform")
        self.object_gizmos.append(self.gz_key_ob)


        ## --- Camera
        
        self.camera_gizmos = []
        
        ## Camera Pan
        self.gz_cam_pan = self.gizmos.new("GIZMO_GT_button_2d")
        set_gizmo_settings(self.gz_cam_pan, 'VIEW_PAN', show_drag=True) # ARROW_LEFTRIGHT
        props = self.gz_cam_pan.target_set_operator("storytools.camera_pan")
        self.camera_gizmos.append(self.gz_cam_pan)
        
        ## Camera Depth
        self.gz_cam_depth = self.gizmos.new("GIZMO_GT_button_2d")
        set_gizmo_settings(self.gz_cam_depth, 'EMPTY_SINGLE_ARROW', show_drag=True)
        props = self.gz_cam_depth.target_set_operator("storytools.camera_depth")
        self.camera_gizmos.append(self.gz_cam_depth)

        # ## Camera Rotation
        # self.gz_cam_rot = self.gizmos.new("GIZMO_GT_button_2d")
        # set_gizmo_settings(self.gz_cam_rot, 'DRIVER_ROTATIONAL_DIFFERENCE', show_drag=True)
        # props = self.gz_cam_rot.target_set_operator("storytools.camera_rotate")
        # self.camera_gizmos.append(self.gz_cam_rot)

        ## Camera lock
        self.gz_lock_cam = self.gizmos.new("GIZMO_GT_button_2d")
        set_gizmo_settings(self.gz_lock_cam, 'OUTLINER_OB_CAMERA')
        props = self.gz_lock_cam.target_set_operator("storytools.camera_lock_toggle")
        self.camera_gizmos.append(self.gz_lock_cam)

        ## Camera key position
        self.gz_key_cam = self.gizmos.new("GIZMO_GT_button_2d")
        set_gizmo_settings(self.gz_key_cam, 'DECORATE_KEYFRAME')
        props = self.gz_key_cam.target_set_operator("storytools.camera_key_transform")
        self.camera_gizmos.append(self.gz_key_cam)


    def draw_prepare(self, context):
        prefs = get_addon_prefs()
        settings = context.scene.storytools_settings
        # icon_size = prefs.toolbar_icon_bounds
        icon_size = 0
        gap_size = prefs.toolbar_gap_size
        backdrop_size = prefs.toolbar_backdrop_size
        
        section_separator = 20
        px_scale = context.preferences.system.ui_scale

        for gz in self.gizmos:
            gz.hide = not settings.show_session_toolbar
        if not settings.show_session_toolbar:
            return
        
        region = context.region
        count = len(self.gizmos)

        ## Old method
        # icon_size = 34
        # gap_size = 28
        # self.bar_width = (count * (self.icon_size * px_scale)) + (count - 1) * (self.gap_size * px_scale) + section_separator
        # vertical_pos = self.icon_size + 2 * px_scale
        # left_pos = region.width / 2 - self.bar_width / 2 - self.icon_size / 2
        # next_pos = self.icon_size * px_scale + self.gap_size * px_scale

        ## With icon size pref parameter
        # self.bar_width = (count * (icon_size * px_scale)) + (count - 1) * (gap_size * px_scale) + section_separator
        # vertical_pos = prefs.toolbar_margin * px_scale
        # left_pos = region.width / 2 - self.bar_width / 2 - icon_size / 2
        # next_pos = icon_size * px_scale + gap_size * px_scale
        

        ## Using only direct offset
        self.bar_width = (count - 1) * (gap_size * px_scale) + section_separator * px_scale
        vertical_pos = prefs.toolbar_margin * px_scale        
        left_pos = region.width / 2 - self.bar_width / 2
        next_pos = gap_size * px_scale

        # ## Orangy
        # obj_color = (0.6, 0.3, 0.2)
        # obj_color_hl = (0.7, 0.4, 0.3)
        # ## Blue
        # cam_color = (0.2, 0.2, 0.6)
        # cam_color_hl = (0.3, 0.3, 0.8)

        # ## grey_light
        # obj_color = (0.3, 0.3, 0.3)
        # obj_color_hl = (0.4, 0.4, 0.4)
        # ## Grey_dark
        # cam_color = (0.1, 0.1, 0.1)
        # cam_color_hl = (0.3, 0.3, 0.3)

        ## Prefs Object gizmo color
        obj_color = prefs.object_gz_color
        obj_color_hl = [i + 0.1 for i in obj_color]
        ## Prefs Camera gizmo color
        cam_color = prefs.camera_gz_color
        cam_color_hl = [i + 0.1 for i in cam_color]

        separator_flag = False

        for i, gz in enumerate(self.gizmos):
            # if gz == self.gz_toggle_bar:
            #     continue
            gz.scale_basis = backdrop_size
            if gz in self.object_gizmos:
                gz.color = obj_color
                gz.color_highlight = obj_color_hl

            if gz in self.camera_gizmos:
                if separator_flag == False:
                    # Add separator
                    separator_flag = True
                    left_pos += section_separator

                gz.color = cam_color
                gz.color_highlight = cam_color_hl
    
            ## Matrix world is readonly
            gz.matrix_basis = Matrix.Translation((left_pos + (i * next_pos), vertical_pos * px_scale, 0))
            
            # matrix_offset seem to affect only backdrop
            # gz.matrix_offset = fn.compose_matrix(Vector((0,0,0)), Matrix().to_quaternion(), Vector((2,2,2)))
            
            # gz.scale_basis = 40 # same as tweaking matrix_basis scale
            
            ## changing matrix size does same thing as gz.scale_basis
            # gz.matrix_basis = fn.compose_matrix(
            #     Vector((left_pos + (i * next_pos), vertical_pos, 0)),
            #     Matrix().to_quaternion(), # Matrix.Rotation(0, 4, 'X'),
            #     Vector((1,1,1))
            # )

            # gz.matrix_basis = Matrix.Scale((1, 1, 1)) # takes at least 2 arguments (1 given)

        ## ! Not working : self.gz_lock_cam.icon = 'LOCKVIEW_ON' if context.space_data.lock_camera else 'LOCKVIEW_OFF'
        
        ## Show color when out of cam view ? : context.space_data.region_3d.view_perspective != 'CAMERA'
        self.gz_lock_cam.color = (0.5, 0.1, 0.1) if context.space_data.lock_camera else cam_color
        self.gz_lock_cam.color_highlight = (0.7, 0.2, 0.2) if context.space_data.lock_camera else cam_color_hl
            

    # def refresh(self, context):
    #     self.gz_lock_cam.icon = 'LOCKVIEW_ON' if context.space_data.lock_camera else 'LOCKVIEW_OFF'
    #     context.area.tag_redraw()


## Toolbar switcher

toggler_shape_verts = (
    (100, 100), (200, 100), (200, 200),
    (100, 100), (100, 200), (200, 200),
                )

toggler_shape_verts_select = (
    (100, 100), (200, 100), (150, 150),
                )

## Full WIP
class VIEW3D_GT_toggler_shape_widget(Gizmo):
    bl_idname = "VIEW3D_GT_toggler_shape_widget"
    # bl_target_properties = (
    #     {"id": "offset", "type": 'FLOAT', "array_length": 1},
    # )

    __slots__ = (
        "custom_shape",
        "custom_shape_select",
        # "init_mouse_y",
        # "init_value",
    )

    # def _update_offset_matrix(self):
    #     # offset behind the light
    #     self.matrix_offset.col[3][2] = self.target_get_value("offset") / -10.0

    def draw(self, context):
        # self._update_offset_matrix()
        self.draw_custom_shape(self.custom_shape)

    def draw_select(self, context, select_id):
        self.draw_custom_shape(self.custom_shape_select, select_id=select_id)

    ## WARN: select_id is probably not what I think it is...
    def test_select(self, context, select_id):
        # print('select_id: ', select_id)
        px_scale = context.preferences.system.ui_scale

        s_min = 100 * px_scale 
        s_max = 200 * px_scale
        select = 1 if s_min < select_id[0] < s_max and s_min < select_id[1]*px_scale < s_max else -1
        # print('select: ', select)
        # self.draw_custom_shape(self.custom_shape, select_id=select_id)
        return select

    def setup(self):
        if not hasattr(self, "custom_shape"):
            self.custom_shape = self.new_custom_shape('TRIS', toggler_shape_verts)
        if not hasattr(self, "custom_shape_select"):
            self.custom_shape_select = self.new_custom_shape('TRIS', toggler_shape_verts_select)

        # set_gizmo_settings(self, 'ADD', scale_basis=10, alpha=0.6)

    def invoke(self, context, event):
        # self.init_mouse_y = event.mouse_y
        # self.init_value = self.target_get_value("offset")
        settings = context.scene.storytools_settings
        settings.show_session_toolbar = not settings.show_session_toolbar
        return {'RUNNING_MODAL'}

    # def exit(self, context, cancel):
    #     pass
    #     # context.area.header_text_set(None)
    #     # if cancel:
    #     #     self.target_set_value("offset", self.init_value)

    def modal(self, context, event, tweak):
        ## TODO: Use modal to resize margin !

        # delta = (event.mouse_y - self.init_mouse_y) / 10.0
        # if 'SNAP' in tweak:
        #     delta = round(delta)
        # if 'PRECISE' in tweak:
        #     delta /= 10.0
        # value = self.init_value - delta
        # self.target_set_value("offset", value)
        # context.area.header_text_set("My Gizmo: %.4f" % value)
        return {'RUNNING_MODAL'}


class STORYTOOLS_GGT_toolbar_switch(GizmoGroup):
    # bl_idname = "STORYTOOLS_GGT_toolbar"
    bl_label = "Story Tool Bar Switch"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'PERSISTENT', 'SCALE'} # SHOW_MODAL_ALL ? 
    # bl_options = {'3D', 'PERSISTENT'}

    @classmethod
    def poll(cls, context):
        return True

    def setup(self, context):
        ## --- Toggle button
        """
        self.gz_toggle_bar = self.gizmos.new("VIEW3D_GT_toggler_shape_widget")
        self.gz_toggle_bar.color = (0.0, 0.0, 0.0)
        self.gz_toggle_bar.color_highlight = (0.5, 0.5, 0.9)
        self.gz_toggle_bar.alpha = 0.7
        self.gz_toggle_bar.alpha_highlight = 0.7
        self.gz_toggle_bar.scale_basis = 1
        # self.gz_toggle_bar.show_drag = False # not exists
        # self.gz_toggle_bar.icon = # not exists
        # self.gz_toggle_bar.draw_options = {'BACKDROP', 'OUTLINE'} # not exists
        """


        ## Simple Single button_2d
        self.gz_toggle_bar = self.gizmos.new("GIZMO_GT_button_2d")
        set_gizmo_settings(self.gz_toggle_bar, 'ADD', scale_basis=10, alpha=0.6) # PLUS
        props = self.gz_toggle_bar.target_set_operator("storytools.toggle_bottom_bar")

    def draw_prepare(self, context):
        prefs = get_addon_prefs()
        settings = context.scene.storytools_settings
        px_scale = context.preferences.system.ui_scale

        # show toggle:
        # self.gz_toggle_bar.matrix_basis = Matrix.Translation((100, 6 * px_scale, 0))
        self.gz_toggle_bar.matrix_basis = Matrix.Translation((400, 6 * px_scale, 0))

    # def refresh(self, context):
    #     pass



class STORYTOOLS_OT_toggle_bottom_bar(bpy.types.Operator):
    bl_idname = "storytools.toggle_bottom_bar"
    bl_label = 'Toggle Bottom Bar'
    bl_description = "Toggle Storytools Bar"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        settings = context.scene.storytools_settings
        settings.show_session_toolbar = not settings.show_session_toolbar
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        return {"FINISHED"}

classes=(
    # VIEW3D_GT_toggler_shape_widget,
    STORYTOOLS_OT_toggle_bottom_bar,
    STORYTOOLS_GGT_toolbar_switch,
    STORYTOOLS_GGT_toolbar,
)

def register():
    if not get_addon_prefs().active_toolbar:
        return
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    if not get_addon_prefs().active_toolbar:
        return
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)