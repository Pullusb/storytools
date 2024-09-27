# SPDX-License-Identifier: GPL-3.0-or-later

# Gizmo doc

import bpy
from bpy.types import (
    Operator,
    GizmoGroup,
    Gizmo
    )

from mathutils import Matrix, Vector
from gpu_extras.batch import batch_for_shader
from .fn import get_addon_prefs
from . import fn



## TESTS create a custom draw for 2d button
# r = 5
# button_shape_lines = [
#     (r, -r), (r, r), (-r, r),
#     (r, -r), (-r, r), (-r, -r),
# ]

# class VIEW3D_GT_button_widget(Gizmo):
#     bl_idname = "VIEW3D_GT_button_widget"

#     __slots__ = (
#         "button_shape",
#     )

#     def draw(self, context):
#         # self.color =  (0.2392, 0.2392, 0.2392) # non-gamma-corrected:(0.0466, 0.0466, 0.0466)
#         # self.color_highlight = (0.27, 0.27, 0.27)
#         self.draw_custom_shape(self.button_shape)

#     # def test_select(self, context, select_id):
#     #     pass

#     def test_select(self, context, select_id):
#             px_scale = context.preferences.system.ui_scale
#             x_min = self.matrix_basis.to_translation().x + (r * px_scale)
#             x_max = self.matrix_basis.to_translation().x + (r * px_scale)
#             y_min = self.matrix_basis.to_translation().y + (r * px_scale)
#             y_max = self.matrix_basis.to_translation().y + (r * px_scale)
#             select = 1 if x_min < select_id[0] < x_max and y_min < select_id[1] < y_max else -1

#             return select

#     def setup(self):
#         if not hasattr(self, "button_shape"):
#             self.button_shape = self.new_custom_shape('TRIS', button_shape_lines)

#     def invoke(self, context, event):
#         return {'RUNNING_MODAL'}

#     def exit(self, context, cancel):
#         pass

#     def modal(self, context, event, tweak):
#         return {'RUNNING_MODAL'}

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
        # return True
        return not fn.is_minimap_viewport(context)

    def setup(self, context):
        ## --- Object

        self.object_gizmos = []

        ## Object Pan
        self.gz_ob_pan = self.gizmos.new("GIZMO_GT_button_2d")
        # self.gz_ob_pan = self.gizmos.new("VIEW3D_GT_button_widget")
        fn.set_gizmo_settings(self.gz_ob_pan, 'VIEW_PAN', show_drag=True)
        self.gz_ob_pan.target_set_operator("storytools.object_pan")
        self.object_gizmos.append(self.gz_ob_pan)
        
        ## Object Depth
        self.gz_ob_depth = self.gizmos.new("GIZMO_GT_button_2d")
        fn.set_gizmo_settings(self.gz_ob_depth, 'EMPTY_SINGLE_ARROW', show_drag=True) # 
        self.gz_ob_depth.target_set_operator("storytools.object_depth_move")
        self.object_gizmos.append(self.gz_ob_depth)

        ## Object Rotation
        self.gz_ob_rotate = self.gizmos.new("GIZMO_GT_button_2d")
        fn.set_gizmo_settings(self.gz_ob_rotate, 'FILE_REFRESH', show_drag=True) # DRIVER_ROTATIONAL_DIFFERENCE
        self.gz_ob_rotate.target_set_operator("storytools.object_rotate")
        self.object_gizmos.append(self.gz_ob_rotate)
        
        ## Object Scale
        self.gz_ob_scale = self.gizmos.new("GIZMO_GT_button_2d")
        fn.set_gizmo_settings(self.gz_ob_scale, 'FULLSCREEN_ENTER', show_drag=True)
        self.gz_ob_scale.target_set_operator("storytools.object_scale")
        self.object_gizmos.append(self.gz_ob_scale)

        ## Object Align to view
        self.gz_ob_align_to_view = self.gizmos.new("GIZMO_GT_button_2d")
        fn.set_gizmo_settings(self.gz_ob_align_to_view, 'AXIS_FRONT')
        self.gz_ob_align_to_view.target_set_operator("storytools.align_with_view")
        self.object_gizmos.append(self.gz_ob_align_to_view)
        
        ## Object key transform
        self.gz_key_ob = self.gizmos.new("GIZMO_GT_button_2d")
        fn.set_gizmo_settings(self.gz_key_ob, 'DECORATE_KEYFRAME')
        self.gz_key_ob.target_set_operator("storytools.object_key_transform")
        self.object_gizmos.append(self.gz_key_ob)

        ## --- Grease Pencil
        self.gpencil_gizmos = []

        ## GP add new empty frame
        self.gz_gp_new_frame = self.gizmos.new("GIZMO_GT_button_2d")
        fn.set_gizmo_settings(self.gz_gp_new_frame, 'DECORATE_ANIMATE')
        self.gz_gp_new_frame.target_set_operator("storytools.new_frame")
        self.gpencil_gizmos.append(self.gz_gp_new_frame)
        
        ## GP add new duplicated frame
        self.gz_gp_new_additive_frame = self.gizmos.new("GIZMO_GT_button_2d")
        fn.set_gizmo_settings(self.gz_gp_new_additive_frame, 'SHAPEKEY_DATA')
        op = self.gz_gp_new_additive_frame.target_set_operator("storytools.new_frame")
        op.duplicate = True
        self.gpencil_gizmos.append(self.gz_gp_new_additive_frame)

        ## --- Camera

        self.camera_gizmos = []
        
        ## Camera Pan
        self.gz_cam_pan = self.gizmos.new("GIZMO_GT_button_2d")
        fn.set_gizmo_settings(self.gz_cam_pan, 'VIEW_PAN', show_drag=True) # ARROW_LEFTRIGHT
        self.gz_cam_pan.target_set_operator("storytools.camera_pan")
        self.camera_gizmos.append(self.gz_cam_pan)
        
        ## Camera Depth
        self.gz_cam_depth = self.gizmos.new("GIZMO_GT_button_2d")
        fn.set_gizmo_settings(self.gz_cam_depth, 'EMPTY_SINGLE_ARROW', show_drag=True)
        self.gz_cam_depth.target_set_operator("storytools.camera_depth")
        self.camera_gizmos.append(self.gz_cam_depth)

        ## Camera Rotation
        self.gz_cam_rot = self.gizmos.new("GIZMO_GT_button_2d")
        fn.set_gizmo_settings(self.gz_cam_rot, 'FILE_REFRESH', show_drag=True)
        op = self.gz_cam_rot.target_set_operator("storytools.object_rotate")
        op.camera = True
        self.camera_gizmos.append(self.gz_cam_rot)

        ## Camera lock
        self.gz_lock_cam = self.gizmos.new("GIZMO_GT_button_2d")
        fn.set_gizmo_settings(self.gz_lock_cam, 'OUTLINER_OB_CAMERA')
        self.gz_lock_cam.target_set_operator("storytools.lock_camera_to_view_toggle")
        self.camera_gizmos.append(self.gz_lock_cam)

        ## Camera key position
        self.gz_key_cam = self.gizmos.new("GIZMO_GT_button_2d")
        fn.set_gizmo_settings(self.gz_key_cam, 'DECORATE_KEYFRAME')
        self.gz_key_cam.target_set_operator("storytools.camera_key_transform")
        self.camera_gizmos.append(self.gz_key_cam)

        
        ## --- Interaction
        
        self.interact_gizmos = []
        
        ## Lock view
        self.gz_lock_view = self.gizmos.new("GIZMO_GT_button_2d")
        fn.set_gizmo_settings(self.gz_lock_view, 'LOCKVIEW_ON')
        self.gz_lock_view.target_set_operator("storytools.lock_view")
        self.interact_gizmos.append(self.gz_lock_view)

        
        ## Draw
        self.gz_draw = self.gizmos.new("GIZMO_GT_button_2d")
        fn.set_gizmo_settings(self.gz_draw, 'GREASEPENCIL')
        self.gz_draw.target_set_operator("storytools.object_draw")
        self.interact_gizmos.append(self.gz_draw)


    def draw_prepare(self, context):
        prefs = get_addon_prefs()
        settings = context.scene.storytools_settings
        gap_size = prefs.toolbar_gap_size
        backdrop_size = prefs.toolbar_backdrop_size
        
        section_separator = int(gap_size / 2) # Fixed at 20 ?
        px_scale = context.preferences.system.ui_scale

        for gz in self.gizmos:
            gz.hide = not settings.show_session_toolbar
        if not settings.show_session_toolbar:
            return
        
        region = context.region
        count = len(self.gizmos)
        sidebar_width = next((r.width for r in context.area.regions if r.type == 'UI'), 0)

        ## Using only direct offset
        self.bar_width = (count - 1) * (gap_size * px_scale) + (section_separator * 2) * px_scale

        vertical_pos = prefs.toolbar_margin * px_scale + fn.get_header_margin(context, overlap=False)
        left_pos = region.width / 2 - self.bar_width / 2

        ## Responsive width adjustment
        visible_region = region.width - sidebar_width
        ## Sidebar push control bar to the left
        overlap = (left_pos + self.bar_width + section_separator) - visible_region
        if overlap > 0:
            left_pos -= overlap
        
        ## Compress if left side is reached
        if left_pos < section_separator:
            out_size = abs(left_pos - section_separator)
            reduction_factor = visible_region / (visible_region + out_size)
            
            left_pos = section_separator # Reset left side
            # Reduce gap_size and section separator, clamped amount (factor of available space)
            # First reduce button size
            backdrop_size = max(backdrop_size * reduction_factor, 14)
            # then gap size
            gap_size = max(gap_size * reduction_factor, backdrop_size * 2)
            section_separator = max(section_separator * reduction_factor, gap_size / 2)

        next_pos = gap_size * px_scale

        ## Prefs Object gizmo color
        obj_color = prefs.object_gz_color
        obj_color_hl = [i + 0.1 for i in obj_color]
        
        ## Prefs Camera gizmo color
        cam_color = prefs.camera_gz_color
        cam_color_hl = [i + 0.1 for i in cam_color]


        for i, gz in enumerate(self.gizmos):
            gz.scale_basis = backdrop_size
            if gz in self.object_gizmos:
                gz.color = obj_color
                gz.color_highlight = obj_color_hl

            if gz in self.gpencil_gizmos:
                if gz == self.gpencil_gizmos[0]:
                    left_pos += section_separator
                gz.color = obj_color
                gz.color_highlight = obj_color_hl
                gz.hide = not context.object or context.object.type != 'GPENCIL'

            if gz in self.camera_gizmos:
                # if separator_flag == 0:
                if gz == self.camera_gizmos[0]:
                    # Add separator
                    left_pos += section_separator
                gz.color = cam_color
                gz.color_highlight = cam_color_hl
            
            if gz in self.interact_gizmos:
                if gz == self.interact_gizmos[0]:
                    # Add separator
                    left_pos += section_separator
                gz.color = obj_color
                gz.color_highlight = obj_color_hl

            ## Matrix world is readonly
            gz.matrix_basis = Matrix.Translation((left_pos + (i * next_pos), vertical_pos, 0))
        
        ## Show color when out of cam view ? : context.space_data.region_3d.view_perspective != 'CAMERA'
        self.gz_lock_cam.color = (0.5, 0.1, 0.1) if context.space_data.lock_camera else cam_color
        self.gz_lock_cam.color_highlight = (0.7, 0.2, 0.2) if context.space_data.lock_camera else cam_color_hl

        rgb_active = prefs.active_gz_color # (0.1, 0.1, 0.4)
        rgb_active_higlight = (rgb_active[0] + 0.1, rgb_active[1] + 0.1, rgb_active[2] + 0.1)
        r3d = context.space_data.region_3d
        self.gz_lock_view.color = rgb_active if r3d.lock_rotation else obj_color
        self.gz_lock_view.color_highlight = rgb_active_higlight if r3d.lock_rotation else obj_color_hl
        
        is_in_draw = context.mode == 'PAINT_GPENCIL'
        self.gz_draw.color = rgb_active if is_in_draw else obj_color
        self.gz_draw.color_highlight = rgb_active_higlight if is_in_draw else obj_color_hl
            

    # def refresh(self, context):
    #     self.gz_lock_cam.icon = 'LOCKVIEW_ON' if context.space_data.lock_camera else 'LOCKVIEW_OFF'
    #     context.area.tag_redraw()


## Toolbar switcher

## Long bar
# x_l = -300
# x_r = 300
# y_d = -4
# y_u = 4

# x_l = -8
# x_r = 8
x_l = -10
x_r = 10
y_d = -6
y_u = 6

toggler_shape_verts = (
    (x_l, y_d), (x_r, y_d), (x_r, y_u),
    (x_l, y_d), (x_r, y_u), (x_l, y_u),
                )

up_arrow_verts = [
    (4, -1), (0, 3), (0, 2),
    (-4, -2), (0, 2), (-4, -1),
    (4, -1), (0, 2), (4, -2),
    (0, 2), (0, 3), (-4, -1),
]

vertical_flip_mat = fn.get_scale_matrix((1, -1, 1))


class VIEW3D_GT_toggler_shape_widget(Gizmo):
    bl_idname = "VIEW3D_GT_toggler_shape_widget"
    # bl_target_properties = (
    #     {"id": "offset", "type": 'FLOAT', "array_length": 1},
    # )

    __slots__ = (
        "custom_shape",
        "arrow_shape",
        "arrow_batch",
        "init_mouse_x",
        "init_mouse_y",
        "mx",
        "my",
        "replace",
        "init_margin",
        # "init_value",
    )

    # def _update_offset_matrix(self):
    #     # offset behind the light
    #     self.matrix_offset.col[3][2] = self.target_get_value("offset") / -10.0

    def draw(self, context):
        # self._update_offset_matrix()
        self.color =  (0.2392, 0.2392, 0.2392) # non-gamma-corrected:(0.0466, 0.0466, 0.0466)
        self.color_highlight = (0.27, 0.27, 0.27)
        self.draw_custom_shape(self.custom_shape)
        
        self.color_highlight = self.color = (0.5568, 0.5568, 0.5568) # non-gamma-corrected:(0.2705, 0.2705, 0.2705)
        self.draw_custom_shape(self.arrow_shape)

    # def draw_select(self, context, select_id):
    #     # self.draw_custom_shape(self.custom_shape)
    #     self.draw_custom_shape(self.custom_shape_select, select_id=select_id)
    #     return

    def test_select(self, context, location):
        px_scale = context.preferences.system.ui_scale
        x_min = self.matrix_basis.to_translation().x + (x_l * px_scale)
        x_max = self.matrix_basis.to_translation().x + (x_r * px_scale)
        y_min = self.matrix_basis.to_translation().y + (y_d * px_scale)
        y_max = self.matrix_basis.to_translation().y + (y_u * px_scale)
        select = 1 if x_min < location[0] < x_max and y_min < location[1] < y_max else -1

        return select

    def setup(self):
        if not hasattr(self, "custom_shape"):
            self.custom_shape = self.new_custom_shape('TRIS', toggler_shape_verts)

        if not hasattr(self, "arrow_shape"):
            self.arrow_shape = self.new_custom_shape('TRIS', up_arrow_verts)
        
        ## Keep default full alpha
        # self.alpha = 1.0
        # self.alpha_highlight = 1.0

    def invoke(self, context, event):
        self.mx = self.init_mouse_x = event.mouse_x
        self.my = self.init_mouse_y = event.mouse_y
        self.replace = False
        self.init_margin = get_addon_prefs().toolbar_margin
        # print(event.value, event.type)
        # self.init_value = self.target_get_value("offset")

        # if self.target_set_operator:
        #     context.window_manager.gizmo_operator_context = 'INVOKE_DEFAULT'
        #     return self.target_set_operator.invoke(context, event)

        return {'RUNNING_MODAL'}

    # def execute(self, context):
    #     print('test')
    #     return {'FINISHED'}


    def exit(self, context, cancel):
        ## Just cancel if move above 10px
        if abs(self.init_mouse_x - self.mx) > 10 or abs(self.init_mouse_y - self.my) > 10:
            return

        settings = context.scene.storytools_settings
        # print('self.target_set_operator: ', self.target_set_operator)
        # print(dir(self))
        # if self.target_set_operator:
        #     # self.gizmo_operator_context = 'EXEC_DEFAULT'
        #     return self.target_set_operator.execute(context)

        ## Replaced if dragged
        # if self.replace:
        #     prefs = get_addon_prefs()
        #     if settings.show_session_toolbar:
        #         # Toobar was visible
        #         if prefs.toolbar_margin > 0:
        #             # No hide, just finish replacing
        #             return
        #         else:
        #             # Reset margin then hide
        #             prefs.toolbar_margin = self.init_margin
        #     else:
        #         # Toolbar was invisible
        #         if prefs.toolbar_margin <= 0:
        #             # Keep invisible -> reset margin and leave
        #             prefs.toolbar_margin = self.init_margin
        #             return
        ## /

        settings.show_session_toolbar = not settings.show_session_toolbar

        ## Refresh all 3D areas
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()


    def modal(self, context, event, tweak):
        self.mx = event.mouse_x
        self.my = event.mouse_y

        ## Place when dragged
        # settings = context.scene.storytools_settings
        # offset = self.my - self.init_mouse_y
        # if abs(offset) > 10:
        #     # Trigger placement instead of toggle
        #     self.replace = True

        # if self.replace:
        #     prefs = get_addon_prefs()
        #     if settings.show_session_toolbar:
        #         prefs.toolbar_margin = self.init_margin + offset
        #     else:
        #         prefs.toolbar_margin = offset
        # context.area.tag_redraw()
        ## /


        ## Dragged opts
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

    # @staticmethod
    # def my_target_operator(context):
    #     wm = context.window_manager
    #     op = wm.operators[-1] if wm.operators else None
    #     if isinstance(op, STORYTOOLS_OT_toggle_bottom_bar):
    #         return op
    #     return None

    def setup(self, context):
        ## --- Toggle button
        self.gz_toggle_bar = self.gizmos.new("VIEW3D_GT_toggler_shape_widget")
        # props = self.gz_toggle_bar.target_set_operator("storytools.toggle_bottom_bar")
        # props.prop_name = 'show_session_toolbar'
        self.gz_toggle_bar.scale_basis = 1

        # self.gz_toggle_bar.use_draw_hover = True # only draw shape when hovering mouse
        # self.gz_toggle_bar.use_draw_modal = True # dunno

        # self.gz_toggle_bar.show_drag = False # not exists
        # self.gz_toggle_bar.icon = # not exists
        # self.gz_toggle_bar.draw_options = {'BACKDROP', 'OUTLINE'} # not exists

        """
        ## Simple Single button_2d
        self.gz_toggle_bar = self.gizmos.new("GIZMO_GT_button_2d")
        fn.set_gizmo_settings(self.gz_toggle_bar, 'ADD', scale_basis=10, alpha=0.6) # PLUS
        props = self.gz_toggle_bar.target_set_operator("storytools.toggle_bottom_bar")
        """

    def draw_prepare(self, context):
        prefs = get_addon_prefs()
        settings = context.scene.storytools_settings
        px_scale = context.preferences.system.ui_scale

        # show toggle:
        # self.gz_toggle_bar.matrix_basis = Matrix.Translation((400, 6 * px_scale, 0))

        
        ## Toggle right aligned (next to sidebar)
        # sidebar = next((r for r in context.area.regions if r.type == 'UI'), None)
        # x_loc = context.region.width - sidebar.width - 40
        
        ## Togge centered
        x_loc = context.region.width / 2
        
        y_loc = 4 * px_scale + fn.get_header_margin(context, overlap=True)

        mat = Matrix.Translation((x_loc, y_loc, 0))
        if context.scene.storytools_settings.show_session_toolbar:
            mat = mat @ vertical_flip_mat

        self.gz_toggle_bar.matrix_basis = mat

    # def refresh(self, context):
    #     pass


class STORYTOOLS_OT_toggle_bottom_bar(Operator):
    bl_idname = "storytools.toggle_bottom_bar"
    bl_label = 'Toggle Bottom Bar'
    bl_description = "Toggle Storytools Bar"
    bl_options = {'REGISTER'} # , 'INTERNAL'

    prop_name : bpy.props.StringProperty(default='show_session_toolbar')

    def execute(self, context):
        # print('-- switch toolbar --')
        # print('prop_name: ', self.prop_name)
        settings = context.scene.storytools_settings
        # setattr(settings, self.prop_name, not getattr(settings, self.prop_name))
        settings.show_session_toolbar = not settings.show_session_toolbar
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        return {"FINISHED"}

classes=(
    # VIEW3D_GT_button_widget,
    STORYTOOLS_OT_toggle_bottom_bar,
    VIEW3D_GT_toggler_shape_widget,
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
