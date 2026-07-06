import bpy

from bpy.types import Operator
from mathutils import Vector, Matrix
from mathutils.geometry import intersect_line_plane
from math import degrees

from .. import fn
from .. import draw
from .cam_move import setup_top_view_map

## Note: some terms used interchangeably in code yaw = Pan, pitch = Tilt

class STORYTOOLS_OT_camera_aim(Operator):
    bl_idname = "storytools.camera_aim"
    bl_label = 'Camera Pan/Tilt'
    bl_description = "Camera Pan/Tilt\
                    \nPivot Camera on itself (Pan left-right / Tilt up-down), X/Y to lock on axis\
                    \n+ Ctrl : Autolock on major axis\
                    \n+ Shift : Precision mode"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.scene.camera

    def invoke(self, context, event):
        self.cam = context.scene.camera

        if any(self.cam.lock_rotation):
            self.report({'ERROR'}, 'Camera rotation is locked')
            return {'CANCELLED'}

        self.shift_pressed = event.shift
        self.cumulated_delta = Vector((0, 0))
        self.current_delta = Vector((0, 0))

        self.final_lock = self.lock = None
        self.init_mat = self.cam.matrix_world.copy()  # to restore if cancelled
        self.init_mouse = Vector((event.mouse_x, event.mouse_y))
        self.lock_text = 'Camera Pan/Tilt'

        ## World-relative rotation axis (turntable style, independent of camera roll):
        ## yaw (left-right) around world Z
        ## pitch (up-down) around the horizontal axis perpendicular to the view (aligned on world)
        self.yaw_axis = Vector((0, 0, 1)) # world Z
        init_quat = self.init_mat.to_quaternion()
        view_dir = init_quat @ Vector((0, 0, -1))
        # view vec cross world Z -> horizontal axis perpendicular to view
        pitch_axis = self.yaw_axis.cross(view_dir)
        if pitch_axis.length_squared < 1e-8:
            ## Looking straight up/down: local X is horizontal, use it directly
            pitch_axis = init_quat @ Vector((1, 0, 0))
            pitch_axis.z = 0.0
        pitch_axis.normalize()
        self.pitch_axis = pitch_axis

        context.window.cursor_set("SCROLL_XY")

        self.update_rotation(context, event)

        ### Lock visual hint section
        ## Draw handler for lock axis visual hint
        center = fn.get_cam_frame_world_center(self.cam)

        ## Local lock axis (here should align with current pan-tilt)
        # self.lock_x_coords = [center + self.pitch_axis * 10000, center + self.pitch_axis * -10000]
        # self.lock_y_coords = [center + self.yaw_axis * 10000, center + self.yaw_axis * -10000]
        
        # circle_3d_coords = fn.circle_3d(0, 0, radius=20, segments=64)
        cam_translation = self.init_mat.to_translation()
        ## calculate X-loc circle radius size without z dimension
        circle_lock_x = fn.circle_3d(0, 0, radius=(Vector(center).xy - cam_translation.xy).length, segments=100)
        ## No special radius needed for Y-loc circle, just need to rotate to align
        circle_lock_y = fn.circle_3d(0, 0, radius=1, segments=64) # radius=(center_v - cam_translation).length # no need to match camera frame
        
        ## Calculate rotation to apply to lock circle for pitch
        top_vec = Vector((0, 0, 1))
        rot_diff = top_vec.rotation_difference(pitch_axis)
        ## Offset z based on center (flatten pairs to avoid getting dotted lines)
        self.lock_x_coords = fn.to_flatten_pairs([v + Vector((0, 0, center[2]-cam_translation.z)) + cam_translation for v in circle_lock_x], closed=False) 
        self.lock_y_coords = fn.to_flatten_pairs([rot_diff @ v + cam_translation for v in circle_lock_y], closed=False)

        ## Draw handler to show initial camera frame during rotation (ghost of source position)
        init_cam_frame = fn.get_cam_frame_world(self.cam, context.scene)
        init_cam_frame += [init_cam_frame[0], init_cam_frame[-1], init_cam_frame[1], init_cam_frame[2]]  # Add top and bottom pair
        self.line_coords = init_cam_frame
        self.line_color = (0.5, 0.5, 0.5, 0.5)
        self._line_handle = bpy.types.SpaceView3D.draw_handler_add(draw.line_draw_callback, (self, context), 'WINDOW', 'POST_VIEW')

        wm = context.window_manager
        args = (self, context)
        self._handle = bpy.types.SpaceView3D.draw_handler_add(draw.lock_axis_draw_callback, args, 'WINDOW', 'POST_VIEW')

        setup_top_view_map(self, context)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def update_rotation(self, context, event):
        mouse_co = Vector((event.mouse_x, event.mouse_y))
        lock = self.lock

        ## Slower with shift (precision mode)
        fac = 0.0002 if event.shift else 0.004
        if event.shift != self.shift_pressed:
            self.shift_pressed = event.shift
            self.cumulated_delta += self.current_delta
            self.init_mouse = mouse_co

        self.current_delta = (mouse_co - self.init_mouse) * fac
        rot_2d = self.cumulated_delta + self.current_delta

        # Ctrl: override lock to "major" direction
        if event.ctrl:
            if abs(rot_2d.x) >= abs(rot_2d.y):
                lock = 'X'
            else:
                lock = 'Y'

        ## Build rotation from mouse delta
        rot_x = 0.0  # tilt (around world-horizontal axis)
        rot_y = 0.0  # pan/yaw (around world Z)

        if not lock or lock == 'X':
            rot_y = -rot_2d.x  # mouse X -> yaw around world Z
        if not lock or lock == 'Y':
            rot_x = -rot_2d.y  # mouse Y -> tilt around horizontal axis (inverted for natural feel)

        self.final_lock = lock

        ## Turntable composition: pitch around the initial horizontal axis first,
        ## then yaw around world Z. Keeps horizon level (no added roll) on combined moves.
        rot_mat_pitch = Matrix.Rotation(rot_x, 4, self.pitch_axis)
        rot_mat_yaw = Matrix.Rotation(rot_y, 4, self.yaw_axis)
        combined_rot = rot_mat_yaw @ rot_mat_pitch

        ## Apply rotation to initial matrix, preserving position
        mat = self.init_mat.copy()
        cam_pos = mat.translation.copy()
        mat.translation = Vector((0, 0, 0))
        mat = combined_rot @ mat
        mat.translation = cam_pos

        self.cam.matrix_world = mat

        ## Set header text
        self.lock_text = f'Camera Aim: Pan: {degrees(rot_y):.2f}°, Tilt: {degrees(rot_x):.2f}°'
        self.lock_text += f' | Lock Axis {lock}' if lock else ''
        context.area.header_text_set(self.lock_text)

    def modal(self, context, event):
        self.update_rotation(context, event)

        if event.type in ('X', 'Y') and event.value == 'PRESS':
            self.lock = event.type if self.lock != event.type else None

        elif event.type == 'LEFTMOUSE':
            context.window.cursor_set("DEFAULT")

            fn.key_object(self.cam, scale=False, use_autokey=True)

            draw.stop_callback(self, context)
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cam.matrix_world = self.init_mat
            draw.stop_callback(self, context)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

classes=(
    STORYTOOLS_OT_camera_aim,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
