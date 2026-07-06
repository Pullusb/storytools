import bpy

from bpy.types import Operator
from mathutils import Vector, Matrix
from mathutils.geometry import intersect_line_plane
from math import degrees

from .. import fn
from .. import draw
from .cam_move import setup_top_view_map

## FIXME: pivoting on both axis makes weird angular rotation on camera
## Use same behavior as cam on a turntable with locked Z up to avoid roll and keep natural horizon when rotating on both axis (yaw then pitch or reverse)

class STORYTOOLS_OT_camera_aim(Operator):
    bl_idname = "storytools.camera_aim"
    bl_label = 'Camera Pan/Tilt'
    bl_description = "Pivot Camera on itself (Pan / Tilt), X/Y to lock on axis\
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

        ## Get camera local axes for rotation
        self.local_x = self.cam.matrix_world.to_quaternion() @ Vector((1, 0, 0))
        self.local_y = self.cam.matrix_world.to_quaternion() @ Vector((0, 1, 0))

        context.window.cursor_set("SCROLL_XY")

        self.update_rotation(context, event)

        ## Draw handler for lock axis visual hint
        center = fn.get_cam_frame_world_center(self.cam)
        self.lock_x_coords = [center + self.local_x * 10000, center + self.local_x * -10000]
        self.lock_y_coords = [center + self.local_y * 10000, center + self.local_y * -10000]
        
        ## Draw handler to show initial camera frame during rotation
        # FIXME : In turntable mode, should draw line based on world axis
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
        fac = 0.0005 if event.shift else 0.01 # 0.001
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
        rot_x = 0.0  # tilt (around camera local X)
        rot_y = 0.0  # pan/yaw (around camera local Y)

        if not lock or lock == 'X':
            rot_y = -rot_2d.x  # mouse X -> yaw around local Y
        if not lock or lock == 'Y':
            rot_x = rot_2d.y  # mouse Y -> tilt around local X (inverted for natural feel)

        self.final_lock = lock

        ## Apply rotation around camera's own position
        ## Get local axes from initial matrix (stable reference)
        init_local_x = self.init_mat.to_quaternion() @ Vector((1, 0, 0))
        init_local_y = self.init_mat.to_quaternion() @ Vector((0, 1, 0))

        rot_mat_x = Matrix.Rotation(rot_x, 4, init_local_x)
        rot_mat_y = Matrix.Rotation(rot_y, 4, init_local_y)

        ## Compose rotation:
        # -> apply yaw (x) then tilt (y) goes diagonally faster
        # -> apply tilt (y) then yaw (x) has more natural to control but we probably want to still align Zup...
        combined_rot = rot_mat_y @ rot_mat_x

        ## Tests to apply directly
        # rot_mat = Matrix.LocRotScale(self.init_mat.to_translation(), combined_rot.to_quaternion(), Vector((1,1,1)))
        # self.cam.matrix_world = self.init_mat @ rot_mat

        ## Apply rotation to initial matrix, preserving position
        mat = self.init_mat.copy()
        cam_pos = mat.translation.copy()
        mat.translation = Vector((0, 0, 0))
        mat = combined_rot @ mat
        mat.translation = cam_pos

        ## Apply new matrix with rotation applyed (when rotating on both axis, this rolls view)
        self.cam.matrix_world = mat

        ### TurnTable pivot mode (avoid roll): From New position, apply lock to track quat Z
        ## Should be ok to use view rotation if also used in free_nav.
        # aim = context.space_data.region_3d.view_rotation @ Vector((0.0, 0.0, 1.0))

        # FIXME: This should be adapted to keep initial view angle... (or only used when cam is horizontal ?...)
        aim = self.cam.matrix_world.to_quaternion() @ Vector((0.0, 0.0, 1.0))
        z_up_quat = aim.to_track_quat('Z','Y')
        cam_quat = z_up_quat
        self.cam.rotation_euler = cam_quat.to_euler('XYZ')
        
        ### / Calc with parent (copied from GPtools)
        # q = self.cam.matrix_world.to_quaternion() # store current rotation

        # if self.cam.parent:
        #     q = self.cam.parent.matrix_world.inverted().to_quaternion() @ q
        #     cam_quat = self.cam.parent.matrix_world.inverted().to_quaternion() @ z_up_quat
        # else:
        #     cam_quat = z_up_quat
        # self.cam.rotation_euler = cam_quat.to_euler('XYZ')
        ### /

        # combined_rot @ mat
        # aim = combined_rot @ Vector((0.0, 0.0, 1.0))
        # print(aim)
        # q = self.cam.matrix_world.to_quaternion()

        ## Set header text
        self.lock_text = f'Camera Aim: Yaw: {degrees(rot_y):.2f}°, Tilt: {degrees(rot_x):.2f}°'
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
