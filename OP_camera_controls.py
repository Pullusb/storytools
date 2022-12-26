import bpy
from bpy.types import Operator
from mathutils import Vector


''' ## ops based version, only valid in object mode
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
        ## !!! Work only in object mode
        orientation = 'VIEW'
        with context.temp_override(selected_objects=[context.scene.camera]):
            bpy.ops.transform.translate('INVOKE_DEFAULT',
                orient_type=orientation, constraint_axis=self.constraint_axis)        
        return {"FINISHED"}
'''

class STORYTOOLS_OT_camera_pan(Operator):
    bl_idname = "storytools.camera_pan"
    bl_label = 'Object Pan Translate'
    bl_description = "Translate active object"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.scene.camera

    def invoke(self, context, event):
        self.cam = context.scene.camera
        # self.use_x, self.use_y = True
        self.lock = None
        self.init_pos = self.cam.location.copy() # to restore if cancelled
        self.init_mouse = Vector((event.mouse_x, event.mouse_y))
        self.lock_text = 'Camera Pan'
        self.local_x = self.cam.matrix_world.to_quaternion() @ Vector((1,0,0))
        self.local_y = self.cam.matrix_world.to_quaternion() @ Vector((0,1,0))
        context.window.cursor_set("SCROLL_XY")
        context.window_manager.modal_handler_add(self)
        self.update_position(context, event)
        return {'RUNNING_MODAL'}

    def update_position(self, context, event):
        mouse_co = Vector((event.mouse_x, event.mouse_y))
        lock = self.lock
        
        ## Slower with shift
        fac = 0.01 if event.shift else 0.1

        move_2d = mouse_co - self.init_mouse
        
        # Ctrl: override lock to "major" direction
        if event.ctrl:
            if abs(move_2d.x) >= abs(move_2d.y):
                lock = 'X'
            else:
                lock = 'Y'

        move_vec = Vector((0,0,0))
        if not lock or lock == 'X': 
            move_vec += self.local_x * (move_2d.x * fac)
        if not lock or lock == 'Y': 
            move_vec += self.local_y * (move_2d.y * fac)

        # set location
        self.cam.location = self.init_pos + move_vec
        
        ## set header text (optional)
        local_move = move_2d * fac
        self.lock_text = f'Camera Pan X: {local_move.x:.3f}, Y: {local_move.y:.3f}'
        self.lock_text += f' | Lock Axis {lock}' if lock else ''
        context.area.header_text_set(self.lock_text)

    def modal(self, context, event):
        self.update_position(context, event)
        
        if event.type in ('X','Y') and event.value == 'PRESS':
            self.lock = event.type if self.lock != event.type else None
        
        elif event.type == 'LEFTMOUSE': # and event.value == 'RELEASE'
            context.window.cursor_set("DEFAULT")
            # set key autokeying
            if context.scene.tool_settings.use_keyframe_insert_auto:
                self.cam.keyframe_insert('location')
                # Better to insert all
                self.cam.keyframe_insert('rotation_euler')
                self.cam.keyframe_insert('scale')

            self.stop(context)
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cam.location = self.init_pos
            self.stop(context)
            return {'CANCELLED'}
        
        return {'RUNNING_MODAL'}
    
    def stop(self, context):
        # remove draw handler and text set
        context.area.header_text_set(None) # reset header
        context.window.cursor_set("DEFAULT")
        context.area.tag_redraw()
    
    def execute(self, context):
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