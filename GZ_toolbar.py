# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.types import (
    Operator,
    GizmoGroup,
    Gizmo
    )

from mathutils import Matrix, Vector
from .preferences import get_addon_prefs


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

    icon_size = 25 # currently more vertical gap size
    gap_size = 15

    @staticmethod
    def set_gizmo_settings(gz, icon,
            color=(0.0, 0.0, 0.0),
            color_highlight=(0.5, 0.5, 0.5),
            alpha=0.5,
            alpha_highlight=0.1,
            show_drag=False,
            draw_options={'BACKDROP', 'OUTLINE'},
            scale_basis=14):
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

    def setup(self, context):
        # FIXME: set bigger icon size and backdrop size
        ## --- Object

        self.object_gizmos = []
        
        ## Object Scale
        self.gz_ob_pan = self.gizmos.new("GIZMO_GT_button_2d")
        self.set_gizmo_settings(self.gz_ob_pan, 'VIEW_PAN', show_drag=True)
        props = self.gz_ob_pan.target_set_operator("storytools.object_pan") 
        self.object_gizmos.append(self.gz_ob_pan)

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
        # props = self.gz_cam_pan.target_set_operator("transform.translate")
        # props.orient_type = 'VIEW'
        
        props = self.gz_cam_pan.target_set_operator("storytools.camera_pan")
        # props = self.gz_cam_pan.target_set_operator("storytools.object_pan")

        self.camera_gizmos.append(self.gz_cam_pan)

        # ## Camera Rotation
        # self.gz_cam_rot = self.gizmos.new("GIZMO_GT_button_2d")
        # self.set_gizmo_settings(self.gz_cam_rot, 'DRIVER_ROTATIONAL_DIFFERENCE', show_drag=True)
        # props = self.gz_cam_rot.target_set_operator("storytools.camera_rotate")
        # self.camera_gizmos.append(self.gz_cam_rot)

        ## Camera lock
        self.gz_lock_cam = self.gizmos.new("GIZMO_GT_button_2d")
        self.set_gizmo_settings(self.gz_lock_cam, 'OUTLINER_OB_CAMERA') # LOCKVIEW_ON
        # self.gz_lock_cam.icon = 'LOCKVIEW_ON' if context.space_data.lock_camera else 'LOCKVIEW_OFF'
        props = self.gz_lock_cam.target_set_operator("storytools.camera_lock_toggle")
        self.camera_gizmos.append(self.gz_lock_cam)

        ## Camera key position
        self.gz_key_cam = self.gizmos.new("GIZMO_GT_button_2d")
        self.set_gizmo_settings(self.gz_key_cam, 'DECORATE_KEYFRAME')
        props = self.gz_key_cam.target_set_operator("storytools.camera_key_transform")
        self.camera_gizmos.append(self.gz_key_cam)        

        # self.object_gizmos.append()

    def draw_prepare(self, context):
        region = context.region
        count = len(self.gizmos)
        ## FIXME : Need to adapt for system resolution ?:
        # bpy.context.preferences.system.dpi : 72 (on 1080 laptop)
        
        ui_scale = context.preferences.view.ui_scale
        self.bar_width = (count * (self.icon_size * ui_scale)) + (count - 1) * (self.gap_size * ui_scale)
        vertical_pos = self.icon_size + 2 * ui_scale
        
        left_pos = region.width / 2 - self.bar_width / 2 - self.icon_size / 2
        next_pos = self.icon_size * ui_scale + self.gap_size * ui_scale

        """# define position individually 
        self.gz_lock_cam.matrix_basis = Matrix.Translation((left_pos, vertical_pos, 0))
            # (region.width / 2 - self.icon_size, vertical_pos, 0)) # center
            ## On right bor0der
            # (2 * ui_scale + region.width - self.icon_size * ui_scale, region.height / 2 - self.icon_size, 0))

        self.gz_key_cam.matrix_basis = Matrix.Translation((left_pos + next_pos, vertical_pos, 0))
        """

        for i, gz in enumerate(self.gizmos):
            gz.matrix_basis = Matrix.Translation((left_pos + (i * next_pos), vertical_pos, 0))
            # if gz == self.gz_lock_cam:
            #     gz.color = (0.4, 0.0,0.0) if context.space_data.lock_camera else (0.0, 0.0, 0.0)
            #     gz.color_highlight = (1.0, 0.5, 0.5) if context.space_data.lock_camera else (0.5, 0.5, 0.5)    
    
        # self.gz_lock_cam.icon = 'LOCKVIEW_ON' if context.space_data.lock_camera else 'LOCKVIEW_OFF'
        self.gz_lock_cam.color = (0.4, 0.0,0.0) if context.space_data.lock_camera else (0.0, 0.0, 0.0)
        self.gz_lock_cam.color_highlight = (1.0, 0.5, 0.5) if context.space_data.lock_camera else (0.5, 0.5, 0.5)

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