# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.types import (
    Operator,
    GizmoGroup,
    Gizmo
    )

from mathutils import Matrix, Vector
from .preferences import get_addon_prefs


class STORYTOOLS_OT_turn_front(Operator):
    bl_idname = "storytools.turn_front"
    bl_label = "Turn Front"
    bl_description = "Turn object front in direction of camera"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.object

    def execute(self, context):
        if not context.object:
            self.report({'ERROR'}, 'No active object')
            return {"CANCELLED"}
        # TODO:
        # Either set object orientation
        # Or create a constraint to camera ?
        print('Super simple ops !')        
        return {"FINISHED"}


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

class STORYTOOLS_OT_camera_lock_toggle(Operator):
    bl_idname = "stools.camera_lock_toggle"
    bl_label = 'Toggle Lock Camera To View'
    bl_description = "Toggle camera lock to view in active viewport"
    bl_options = {'REGISTER', 'INTERNAL'}


    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        sd = context.space_data
        sd.lock_camera = not sd.lock_camera
        # context.area.tag_redraw()
        return {"FINISHED"}

class STORYTOOLS_GGT_toolbar(GizmoGroup):
    # bl_idname = "STORYTOOLS_GGT_toolbar"
    bl_label = "Story Tool Bar"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'PERSISTENT', 'SCALE'}

    @classmethod
    def poll(cls, context):
        return context.space_data.region_3d.view_perspective == 'CAMERA'
        # return True

    icon_size = 25

    def setup(self, context):
        # print('0')
        
        gz = self.gizmos.new("GIZMO_GT_button_2d")
        # gz.icon = 'LOCKVIEW_ON' if context.space_data.lock_camera else 'LOCKVIEW_OFF'
        gz.icon = 'LOCKVIEW_ON'
        # gz.color = (0.0, 0.0, 0.0) # default 0.0
        gz.color_highlight = (0.5, 0.5, 0.5) # default 0.5
        gz.alpha = 0.5
        gz.alpha_highlight = 0.1
        gz.show_drag = False
        gz.draw_options = {'BACKDROP', 'OUTLINE'}
        gz.scale_basis = 14
        props = gz.target_set_operator("stools.camera_lock_toggle")
        
        # print('---')
        # for a in dir_gz:
        #     print(a, getattr(gz, a))
        # print('===')
        

        self.gz_lock_cam = gz

    def draw_prepare(self, context):
        # Organize position according to len(self.gizmos)
        region = context.region
        ui_scale = context.preferences.view.ui_scale
        self.gz_lock_cam.matrix_basis = Matrix.Translation(
            (region.width / 2 - self.icon_size, self.icon_size + 2 * ui_scale, 0))
            ## On right border
            # (2 * ui_scale + region.width - self.icon_size * ui_scale, region.height / 2 - self.icon_size, 0))

        # self.gz_lock_cam.icon = 'LOCKVIEW_ON' if context.space_data.lock_camera else 'LOCKVIEW_OFF'
        self.gz_lock_cam.color = (0.4, 0.0,0.0) if context.space_data.lock_camera else (0.0, 0.0, 0.0)
        self.gz_lock_cam.color_highlight = (1.0, 0.5, 0.5) if context.space_data.lock_camera else (0.5, 0.5, 0.5)
    
    # def refresh(self, context):
    #     self.gz_lock_cam.icon = 'LOCKVIEW_ON' if context.space_data.lock_camera else 'LOCKVIEW_OFF'
    #     context.area.tag_redraw()

classes=(
    STORYTOOLS_OT_camera_lock_toggle,
    STORYTOOLS_GGT_toolbar,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)