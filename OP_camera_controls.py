import bpy
from bpy.types import Operator


# class STORYTOOLS_OT_turn_front(Operator):
#     bl_idname = "storytools.turn_front"
#     bl_label = "Turn Front"
#     bl_description = "Turn object front in direction of camera"
#     bl_options = {"REGISTER", "UNDO"}

#     @classmethod
#     def poll(cls, context):
#         return context.object

#     def execute(self, context):
#         if not context.object:
#             self.report({'ERROR'}, 'No active object')
#             return {"CANCELLED"}
#         # TODO:
#         # Either set object orientation
#         # Or create a constraint to camera ?
#         print('Super simple ops !')        
#         return {"FINISHED"}

class STORYTOOLS_OT_attach_toggle(Operator):
    bl_idname = "storytools.attach_toggle"
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


class STORYTOOLS_OT_camera_lock_toggle(Operator):
    bl_idname = "storytools.camera_lock_toggle"
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

class STORYTOOLS_OT_camera_key_transform(Operator):
    bl_idname = "storytools.camera_key_transform"
    bl_label = 'Key Transforms'
    bl_description = "Key current camera location and rotation"
    bl_options = {'REGISTER', 'INTERNAL'}


    @classmethod
    def poll(cls, context):
        return context.scene.camera

    def execute(self, context):
        cam = context.scene.camera
        cam.keyframe_insert('location', group='Object Transforms')
        cam.keyframe_insert('rotation_euler', group='Object Transforms')
        return {"FINISHED"}

classes=(
    STORYTOOLS_OT_attach_toggle,
    STORYTOOLS_OT_camera_lock_toggle,
    STORYTOOLS_OT_camera_key_transform,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)