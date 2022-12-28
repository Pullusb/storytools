# SPDX-License-Identifier: GPL-2.0-or-later

# Gizmo doc

import bpy
from bpy.types import (
    Operator,
    GizmoGroup,
    Gizmo
    )

from mathutils import Matrix, Vector
from .preferences import get_addon_prefs
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

class STORYTOOLS_GGT_toolbar(GizmoGroup):
    # bl_idname = "STORYTOOLS_GGT_toolbar"
    bl_label = "Story Tool Bar"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'PERSISTENT', 'SCALE'}

    @classmethod
    def poll(cls, context):
        # return context.space_data.region_3d.view_perspective == 'CAMERA'
        return True

    icon_size = 34 # currently more vertical gap size
    gap_size = 28

    @staticmethod
    def set_gizmo_settings(gz, icon,
            color=(0.0, 0.0, 0.0),
            color_highlight=(0.5, 0.5, 0.5),
            alpha=0.6,
            alpha_highlight=0.6, # 0.1
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
        # gz.line_width = 3.0 # no affect on 2D gizmo ?
        
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

    def setup(self, context):
        # FIXME: set bigger icon size and backdrop size
        ## --- Object

        self.object_gizmos = []
        
        ## Object Pan
        self.gz_ob_pan = self.gizmos.new("GIZMO_GT_button_2d")
        self.set_gizmo_settings(self.gz_ob_pan, 'VIEW_PAN', show_drag=True)
        props = self.gz_ob_pan.target_set_operator("storytools.object_pan") 
        self.object_gizmos.append(self.gz_ob_pan)
        
        ## Object Depth
        self.gz_ob_depth = self.gizmos.new("GIZMO_GT_button_2d")
        self.set_gizmo_settings(self.gz_ob_depth, 'EMPTY_SINGLE_ARROW', show_drag=True) # 
        props = self.gz_ob_depth.target_set_operator("storytools.object_depth_move")
        self.object_gizmos.append(self.gz_ob_depth)

        ## Object Scale
        self.gz_ob_scale = self.gizmos.new("GIZMO_GT_button_2d")
        self.set_gizmo_settings(self.gz_ob_scale, 'FULLSCREEN_ENTER', show_drag=True)
        props = self.gz_ob_scale.target_set_operator("storytools.object_scale")
        self.object_gizmos.append(self.gz_ob_scale)

        ## Object Align to view
        self.gz_ob_align_to_view = self.gizmos.new("GIZMO_GT_button_2d")
        self.set_gizmo_settings(self.gz_ob_align_to_view, 'AXIS_FRONT')
        props = self.gz_ob_align_to_view.target_set_operator("storytools.align_with_view")
        self.object_gizmos.append(self.gz_ob_align_to_view)
        

        ## --- Camera
        self.camera_gizmos = []
        
        ## Camera Pan
        self.gz_cam_pan = self.gizmos.new("GIZMO_GT_button_2d")
        self.set_gizmo_settings(self.gz_cam_pan, 'VIEW_PAN', show_drag=True) # ARROW_LEFTRIGHT
        props = self.gz_cam_pan.target_set_operator("storytools.camera_pan")
        self.camera_gizmos.append(self.gz_cam_pan)
        
        ## Camera Depth
        self.gz_cam_depth = self.gizmos.new("GIZMO_GT_button_2d")
        self.set_gizmo_settings(self.gz_cam_depth, 'EMPTY_SINGLE_ARROW', show_drag=True)
        props = self.gz_cam_depth.target_set_operator("storytools.camera_depth")
        self.camera_gizmos.append(self.gz_cam_depth)

        # ## Camera Rotation
        # self.gz_cam_rot = self.gizmos.new("GIZMO_GT_button_2d")
        # self.set_gizmo_settings(self.gz_cam_rot, 'DRIVER_ROTATIONAL_DIFFERENCE', show_drag=True)
        # props = self.gz_cam_rot.target_set_operator("storytools.camera_rotate")
        # self.camera_gizmos.append(self.gz_cam_rot)

        ## Camera lock
        self.gz_lock_cam = self.gizmos.new("GIZMO_GT_button_2d")
        self.set_gizmo_settings(self.gz_lock_cam, 'OUTLINER_OB_CAMERA')
        props = self.gz_lock_cam.target_set_operator("storytools.camera_lock_toggle")
        self.camera_gizmos.append(self.gz_lock_cam)

        ## Camera key position
        self.gz_key_cam = self.gizmos.new("GIZMO_GT_button_2d")
        self.set_gizmo_settings(self.gz_key_cam, 'DECORATE_KEYFRAME')
        props = self.gz_key_cam.target_set_operator("storytools.camera_key_transform")
        self.camera_gizmos.append(self.gz_key_cam)        

    def draw_prepare(self, context):
        region = context.region
        count = len(self.gizmos)

        ## FIXME : Need to adapt for system resolution ?:
        # bpy.context.preferences.system.dpi : 72 (on 1080 laptop) at 1.0 UI scale

        section_separator = 20
        ui_scale = context.preferences.view.ui_scale
        self.bar_width = (count * (self.icon_size * ui_scale)) + (count - 1) * (self.gap_size * ui_scale) + section_separator
        vertical_pos = self.icon_size + 2 * ui_scale
        
        left_pos = region.width / 2 - self.bar_width / 2 - self.icon_size / 2
        next_pos = self.icon_size * ui_scale + self.gap_size * ui_scale

        obj_color = (0.6, 0.3, 0.2)
        obj_color_hl = (0.7, 0.4, 0.3)
        cam_color = (0.2, 0.2, 0.6)
        cam_color_hl = (0.3, 0.3, 0.8)

        separator_flag = False
        
        ## On right border
        # (2 * ui_scale + region.width - self.icon_size * ui_scale, region.height / 2 - self.icon_size, 0))

        for i, gz in enumerate(self.gizmos):
            
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
            gz.matrix_basis = Matrix.Translation((left_pos + (i * next_pos), vertical_pos, 0))
            
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
        
        self.gz_lock_cam.color = (0.5, 0.1, 0.1) if context.space_data.lock_camera else cam_color
        self.gz_lock_cam.color_highlight = (0.6, 0.2, 0.2) if context.space_data.lock_camera else cam_color_hl

    # def refresh(self, context):
    #     self.gz_lock_cam.icon = 'LOCKVIEW_ON' if context.space_data.lock_camera else 'LOCKVIEW_OFF'
    #     context.area.tag_redraw()

classes=(
    STORYTOOLS_GGT_toolbar,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)