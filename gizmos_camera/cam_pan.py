import bpy
import gpu

from bpy.types import Operator
from mathutils import Vector
from gpu_extras.batch import batch_for_shader
from bpy.app.handlers import persistent

from .. import fn
from .. import draw

## ! Unused !
## Standalone Camera Pan 
## Pan and shift are merged in cam_move, stored in case of button split in the future)

class STORYTOOLS_OT_camera_pan(Operator):
    bl_idname = "storytools.camera_pan"
    bl_label = 'Object Pan Translate'
    bl_description = "Pan Camera, X/Y to lock on axis\
                    \n+ Ctrl : Autolock on major axis\
                    \n+ Shift : Precision mode"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.scene.camera

    def invoke(self, context, event):
        self.cam = context.scene.camera

        if any(self.cam.lock_location):
            # print('locked!')
            self.report({'ERROR'}, 'Camera location is locked')
            return {'CANCELLED'}

            ## redo panel changes crash (probably cause of the mix)
            self.ob = self.cam # need to assign 'ob' variable
            return context.window_manager.invoke_props_dialog(self)

        self.shift_pressed = event.shift
        self.cumulated_delta = Vector((0, 0))
        self.current_delta = Vector((0, 0))

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

        args = (self, context)
        self._handle = bpy.types.SpaceView3D.draw_handler_add(draw.lock_axis_draw_callback, args, 'WINDOW', 'POST_VIEW')

        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def update_position(self, context, event):
        mouse_co = Vector((event.mouse_x, event.mouse_y))
        lock = self.lock
        
        ## Slower with shift
        fac = 0.01 if event.shift else 0.1
        if event.shift != self.shift_pressed:
            self.shift_pressed = event.shift
            self.cumulated_delta += self.current_delta
            self.init_mouse = mouse_co

        self.current_delta = (mouse_co - self.init_mouse) * fac
        move_2d = self.cumulated_delta + self.current_delta
        
        # Ctrl: override lock to "major" direction
        if event.ctrl:
            if abs(move_2d.x) >= abs(move_2d.y):
                lock = 'X'
            else:
                lock = 'Y'

        move_vec = Vector((0,0,0))
        if not lock or lock == 'X': 
            move_vec += self.local_x * (move_2d.x)
        if not lock or lock == 'Y': 
            move_vec += self.local_y * (move_2d.y)

        self.final_lock = lock
        # set location
        self.cam.location = self.init_pos + move_vec
        
        ## set header text (optional)
        self.lock_text = f'Camera Pan X: {move_2d.x:.3f}, Y: {move_2d.y:.3f}'
        self.lock_text += f' | Lock Axis {lock}' if lock else ''
        context.area.header_text_set(self.lock_text)

    def modal(self, context, event):
        self.update_position(context, event)
        
        if event.type in ('X','Y') and event.value == 'PRESS':
            self.lock = event.type if self.lock != event.type else None
        
        elif event.type == 'LEFTMOUSE': # and event.value == 'RELEASE'
            context.window.cursor_set("DEFAULT")
            
            fn.key_object(self.cam, scale=False, use_autokey=True)

            draw.stop_callback(self, context)
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cam.location = self.init_pos
            draw.stop_callback(self, context)
            return {'CANCELLED'}
        
        return {'RUNNING_MODAL'}


classes=(
    STORYTOOLS_OT_camera_pan,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    