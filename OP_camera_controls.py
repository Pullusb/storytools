import bpy
from bpy.types import Operator
from mathutils import Vector
from . import fn
import gpu
from gpu_extras.batch import batch_for_shader

class STORYTOOLS_OT_camera_depth(Operator):
    bl_idname = "storytools.camera_depth"
    bl_label = 'Camera Depth Move'
    bl_description = "Move Camera Depth (forward and backward)"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.scene.camera

    def invoke(self, context, event):
        self.cam = context.scene.camera
        if any(self.cam.lock_location):
            self.report({'ERROR'}, 'Camera location is locked')
            return {'CANCELLED'}

        self.init_pos = self.cam.location.copy()
        self.init_mouse_x = event.mouse_x
        context.window.cursor_set("SCROLL_X")
        context.window_manager.modal_handler_add(self)
        
        # camera forward vector
        self.cam_forward_vec = self.cam.matrix_world.to_quaternion() @ Vector((0,0,-1))
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        # Shift precision move
        fac = 0.01 if event.shift else 0.1
        delta = event.mouse_x - self.init_mouse_x
        # self.cam.scale = self.init_pos * (1 + delta * fac)
        move_val = delta * fac
        self.cam.matrix_world.translation = self.init_pos + self.cam_forward_vec * move_val
        
        if event.type == 'LEFTMOUSE':
            context.window.cursor_set("DEFAULT")
            
            fn.key_object(self.cam, scale=False, use_autokey=True)

            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cam.location = self.init_pos
            context.window.cursor_set("DEFAULT")
            return {'CANCELLED'}
        
        return {'RUNNING_MODAL'}

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
    bl_description = "Pan Camera, X/Y to lock on axis\
                    \n+ Ctrl autolock on major Axis\
                    \n+ Shift Slower move"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.scene.camera

    def cam_pan_draw_callback(self, context):
        # Draw lock lines
        if not self.final_lock:
            return
        if self.final_lock == 'X':
            coords = self.lock_x_coords
            color = (1, 0, 0, 0.15)
        elif self.final_lock == 'Y':
            coords = self.lock_y_coords
            color = (0, 1, 0, 0.15)
        else:
            return
        
        gpu.state.blend_set('ALPHA')
        gpu.state.line_width_set(2)

        shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINES', {"pos": coords})
        shader.uniform_float("color", color)
        batch.draw(shader)

        gpu.state.line_width_set(1)
        gpu.state.blend_set('NONE')

    
    # def execute(self, context):
    #     context.area.tag_redraw()
    #     # return {"CANCELLED"}
    #     ## Button disappear on OK click
    #     ## Crash when using redo
    #     ## Need to lauch a sub-ops with it's own draw
    #     return {"FINISHED"}

    # def draw(self, context):
    #     layout = self.layout
    #     layout.label(text='Camera location is locked')
    #     ob_lock_location_cam_draw_panel(self, context)

    def invoke(self, context, event):
        self.cam = context.scene.camera

        if any(self.cam.lock_location):
            # print('locked!')
            self.report({'ERROR'}, 'Camera location is locked')
            return {'CANCELLED'}

            ## redo panel changes crash (probably cause of the mix)
            self.ob = self.cam # need to assign 'ob' variable
            return context.window_manager.invoke_props_dialog(self)
            
        self.final_lock = self.lock = None
        self.init_pos = self.cam.location.copy() # to restore if cancelled
        self.init_mouse = Vector((event.mouse_x, event.mouse_y))
        self.lock_text = 'Camera Pan'
        self.local_x = self.cam.matrix_world.to_quaternion() @ Vector((1,0,0))
        self.local_y = self.cam.matrix_world.to_quaternion() @ Vector((0,1,0))
        context.window.cursor_set("SCROLL_XY")

        self.update_position(context, event)

        ## Draw handler
        center = fn.get_cam_frame_world_center(self.cam)
        self.lock_x_coords = [center + self.local_x * 10000, center + self.local_x * -10000]
        self.lock_y_coords = [center + self.local_y * 10000, center + self.local_y * -10000]
        wm = context.window_manager
        # args = (self, context)
        args = (context,)
        self._handle = bpy.types.SpaceView3D.draw_handler_add(self.cam_pan_draw_callback, args, 'WINDOW', 'POST_VIEW')

        wm.modal_handler_add(self)
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

        self.final_lock = lock
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
            
            fn.key_object(self.cam, scale=False, use_autokey=True)

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
        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        context.area.tag_redraw()


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
    bl_label = "Attach Toggle"
    bl_description = "Parent / Unparent object to active Camera"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.object

    def execute(self, context):
        if not context.object:
            self.report({'ERROR'}, 'No active object')
            return {"CANCELLED"}
        
        if context.object == context.scene.camera:
            self.report({'ERROR'}, 'The active object is the camera')
            return {"CANCELLED"}

        mat = context.object.matrix_world.copy()
        if context.object.parent == context.scene.camera:
            # unparent
            context.object.parent = None # remove parent

        elif not context.object.parent:
            # parent
            context.object.parent = context.scene.camera # remove parent

        context.object.matrix_world = mat

        ## TODO: dynamic parent ? maybe need to double the key (custom keying)
        fn.key_object(context.object, use_autokey=True)

        return {"FINISHED"}


class STORYTOOLS_OT_camera_lock_toggle(Operator):
    bl_idname = "storytools.camera_lock_toggle"
    bl_label = 'Toggle Lock Camera To View'
    bl_description = "In Camera view: Toggle 'lock camera to view' (active viewport)\
        \nIn free view: Go to camera"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        if context.space_data.region_3d.view_perspective != 'CAMERA':
            context.space_data.region_3d.view_perspective = 'CAMERA'
            return {"FINISHED"}

        ## Toggle lock only if in camera view 
        sd = context.space_data
        sd.lock_camera = not sd.lock_camera
        return {"FINISHED"}

class STORYTOOLS_OT_camera_key_transform(Operator):
    bl_idname = "storytools.camera_key_transform"
    bl_label = 'Key Camera Transforms'
    bl_description = "Key current camera location and rotation"
    bl_options = {'REGISTER', 'INTERNAL'}


    @classmethod
    def poll(cls, context):
        return context.scene.camera

    def execute(self, context):
        ret = fn.key_object(context.scene.camera, scale=False)
        if ret:
            self.report({'INFO'}, ret)
        return {"FINISHED"}

classes=(
    STORYTOOLS_OT_attach_toggle,
    STORYTOOLS_OT_camera_pan,
    STORYTOOLS_OT_camera_rotate,
    STORYTOOLS_OT_camera_depth,
    STORYTOOLS_OT_camera_lock_toggle,
    STORYTOOLS_OT_camera_key_transform,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)