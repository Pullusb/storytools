import bpy
from bpy.types import Operator
from mathutils import Vector


class STORYTOOLS_OT_camera_pan(Operator):
    bl_idname = "storytools.camera_pan"
    bl_label = 'Pan Camera'
    bl_description = "Pan camera view"
    bl_options = {'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.scene.camera

    def invoke(self, context, event):
        ## Ctrl:incremental step, shift: Precision
        ## need to use only at triggering time...
        self.constraint_axis = (False, False, False)
        if event.ctrl: 
            self.constraint_axis = (True, False, False)
        elif event.shift:
            self.constraint_axis = (False, True, False)
        return self.execute(context)

    def execute(self, context):
        orientation = 'VIEW'
        ## ? switch to local outside of cam ? seem not needed
        # if context.space_data.region_3d.view_perspective != 'CAMERA':
        #     orientation = 'LOCAL'

        with context.temp_override(selected_objects=[context.scene.camera]):
            bpy.ops.transform.translate('INVOKE_DEFAULT',
                orient_type=orientation, constraint_axis=self.constraint_axis)
        
        # transform.translate(value=(0, 0, 0), orient_axis_ortho='X', orient_type='GLOBAL', 
        # orient_matrix=((0, 0, 0), (0, 0, 0), (0, 0, 0)), orient_matrix_type='GLOBAL', 
        # constraint_axis=(False, False, False), mirror=False, use_proportional_edit=False, 
        # proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, 
        # use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, 
        # snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, 
        # use_snap_selectable=False, snap_point=(0, 0, 0), snap_align=False, snap_normal=(0, 0, 0), 
        # gpencil_strokes=False, cursor_transform=False, texture_space=False, remove_on_cancel=False, 
        # view2d_edge_pan=False, release_confirm=False, use_accurate=False, use_automerge_and_split=False)
        
        ## for more control need a custom pan modal
        return {"FINISHED"}

# Not really needed, already in Grease pencil tools
class STORYTOOLS_OT_camera_rotate(Operator):
    bl_idname = "storytools.camera_rotate"
    bl_label = 'Rotate Camera'
    bl_description = "Rotate camera"
    bl_options = {'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.scene.camera

    def invoke(self, context, event):
        self.horizontal = event.ctrl
        return self.execute(context)

    def execute(self, context):
        if self.horizontal: # WIP
            ## use view
            cam = context.scene.camera
            aim = context.space_data.region_3d.view_rotation @ Vector((0.0, 0.0, 1.0)) # view vector
            # aim = cam.matrix_world.to_quaternion() @ Vector((0.0, 0.0, 1.0)) # view vector
            z_up_quat = aim.to_track_quat('Z','Y') # track Z, up Y
            q = cam.matrix_world.to_quaternion() # store current rotation

            if cam.parent:
                q = cam.parent.matrix_world.inverted().to_quaternion() @ q
                cam_quat = cam.parent.matrix_world.inverted().to_quaternion() @ z_up_quat
            else:
                cam_quat = z_up_quat
            cam.rotation_euler = cam_quat.to_euler('XYZ')

            # get diff angle (might be better way to get view axis rot diff)
            diff_angle = q.rotation_difference(cam_quat).to_euler('ZXY').z
            # print('diff_angle: ', math.degrees(diff_angle))
            # set_cam_view_offset_from_angle(context, diff_angle)
            
            # cam.rotation_euler.z += diff_angle
            cam.rotation_euler.rotate_axis("Z", diff_angle)
            
            #neg = -angle
            #rot_mat2d = mathutils.Matrix([[math.cos(neg), -math.sin(neg)], [math.sin(neg), math.cos(neg)]])


            return {"FINISHED"}
        
        orientation = 'VIEW'
        with context.temp_override(selected_objects=[context.scene.camera]):
            bpy.ops.transform.rotate('INVOKE_DEFAULT', orient_axis='Z') # orient_type='VIEW'
        return {"FINISHED"}

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
    STORYTOOLS_OT_camera_pan,
    STORYTOOLS_OT_camera_rotate,
    STORYTOOLS_OT_camera_lock_toggle,
    STORYTOOLS_OT_camera_key_transform,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)