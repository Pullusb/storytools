import bpy
import gpu

from bpy.types import Operator
from mathutils import Vector
from gpu_extras.batch import batch_for_shader
from bpy.app.handlers import persistent

from .. import fn
from .. import draw


class STORYTOOLS_OT_camera_shift(Operator):
    bl_idname = "storytools.camera_shift"
    bl_label = 'Object Shift Translate'
    bl_description = "Shift Camera, X/Y to lock on axis\
                    \n+ Ctrl : Autolock on major axis\
                    \n+ Shift : Precision mode"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
 
    @classmethod
    def poll(cls, context):
        return context.scene.camera and context.scene.camera.data.type == 'PERSP'

    def invoke(self, context, event):
        self.cam = context.scene.camera

        if any(self.cam.lock_location):
            self.report({'ERROR'}, 'Camera location is locked')
            return {'CANCELLED'}

        self.shift_pressed = event.shift
        self.cumulated_delta = Vector((0, 0))
        self.current_delta = Vector((0, 0))

        self.final_lock = self.lock = None
        self.init_shift_x = self.cam.data.shift_x  # to restore if cancelled
        self.init_shift_y = self.cam.data.shift_y  # to restore if cancelled
        self.init_mouse = Vector((event.mouse_x, event.mouse_y))
        self.lock_text = 'Camera Shift'

        self.local_x = self.cam.matrix_world.to_quaternion() @ Vector((1,0,0))
        self.local_y = self.cam.matrix_world.to_quaternion() @ Vector((0,1,0))
        context.window.cursor_set("SCROLL_XY")

        self.update_shift(context, event)

        center = fn.get_cam_frame_world_center(self.cam)
        self.lock_x_coords = [center + self.local_x * 10000, center + self.local_x * -10000]
        self.lock_y_coords = [center + self.local_y * 10000, center + self.local_y * -10000]
        
        wm = context.window_manager
        args = (self, context)
        self._handle = bpy.types.SpaceView3D.draw_handler_add(draw.lock_axis_draw_callback, args, 'WINDOW', 'POST_VIEW')

        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def update_shift(self, context, event):
        mouse_co = Vector((event.mouse_x, event.mouse_y))
        lock = self.lock
        
        fac = 0.001 if event.shift else 0.01
        if event.shift != self.shift_pressed:
            self.shift_pressed = event.shift
            self.cumulated_delta += self.current_delta
            self.init_mouse = mouse_co

        self.current_delta = (mouse_co - self.init_mouse) * fac
        move_2d = self.cumulated_delta + self.current_delta
        
        if event.ctrl:
            if abs(move_2d.x) >= abs(move_2d.y):
                lock = 'X'
            else:
                lock = 'Y'

        move_vec = Vector((0, 0))
        if not lock or lock == 'X': 
            move_vec.x = move_2d.x
        if not lock or lock == 'Y': 
            move_vec.y = move_2d.y

        self.final_lock = lock
        self.cam.data.shift_x = self.init_shift_x + move_vec.x
        self.cam.data.shift_y = self.init_shift_y + move_vec.y
        
        self.lock_text = f'Camera Shift X: {move_2d.x:.3f}, Y: {move_2d.y:.3f}'
        self.lock_text += f' | Lock Axis {lock}' if lock else ''
        context.area.header_text_set(self.lock_text)

    def modal(self, context, event):
        self.update_shift(context, event)
        
        if event.type in ('X','Y') and event.value == 'PRESS':
            self.lock = event.type if self.lock != event.type else None
        
        elif event.type == 'LEFTMOUSE':
            context.window.cursor_set("DEFAULT")
            
            ## TODO: Need custom function or adapt current key_object to key datapath
            # fn.key_object(self.cam, scale=False, use_autokey=True)
            draw.stop_callback(self, context)
            if context.scene.tool_settings.use_keyframe_insert_auto:
                ## Key shift (only if already keyed ?) !
                # if self.cam.data.animation_data and (action := self.cam.data.animation_data.action):
                #     if action.fcurves.find('shift_x'):
                #         self.cam.data.keyframe_insert('shift_x')
                #     if action.fcurves.find('shift_y'):
                #         self.cam.data.keyframe_insert('shift_y')

                ## Only Key:
                self.cam.data.keyframe_insert('shift_x')
                self.cam.data.keyframe_insert('shift_y')
                
                # Do not key axis if not moved
                # if self.cam.data.shift_x != self.init_shift_x:
                #     self.cam.data.keyframe_insert('shift_x')
                # if self.cam.data.shift_y != self.init_shift_y:
                #     self.cam.data.keyframe_insert('shift_y')
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cam.data.shift_x = self.init_shift_x
            self.cam.data.shift_y = self.init_shift_y
            draw.stop_callback(self, context)
            return {'CANCELLED'}
        
        return {'RUNNING_MODAL'}


classes=(
    STORYTOOLS_OT_camera_shift,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    