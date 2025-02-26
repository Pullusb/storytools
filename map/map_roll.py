import bpy
import gpu
import math
import mathutils
from bpy.types import Operator
from mathutils import Vector, Matrix, Quaternion
from time import time
from .. import fn
from .. import draw

class STORYTOOLS_OT_roll_minimap_viewport(Operator):
    bl_idname = "storytools.roll_minimap_viewport"
    bl_label = 'Roll Minimap Viewport'
    bl_description = "Roll Minimap View\
        \n+ Shift: Fine tuning\
        \n+ Ctrl: Snap to 15 degree increments\
        \nSingle click to reset roll"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        return fn.is_minimap_viewport(context)

    def execute(self, context):
        # Remove text overlay
        if hasattr(self, '_text_handle'):
            bpy.types.SpaceView3D.draw_handler_remove(self._text_handle, 'WINDOW')
            context.area.tag_redraw()
            
        context.area.header_text_set(None)
        context.window.cursor_set("DEFAULT")
        return {'FINISHED'}

    def modal(self, context, event):
        if event.type == 'MOUSEMOVE':
            # Handle shift key transition
            if event.shift != self.shift_pressed:
                self.shift_pressed = event.shift
                self.cumulated_rotation += self.current_rotation
                self.init_mouse_x = event.mouse_x
            
            # Calculate delta movement and apply rotation
            delta_x = event.mouse_x - self.init_mouse_x
            
            # Apply different sensitivity based on shift key
            sensitivity = 0.005 if event.shift else 0.01
            self.current_rotation = delta_x * sensitivity
            rotation_amount = self.cumulated_rotation + self.current_rotation
            
            # Snap to increments if ctrl is pressed
            if event.ctrl:
                snap_angle = math.radians(15)  # 15 degree increments
                rotation_amount = round(rotation_amount / snap_angle) * snap_angle
            
            # Calculate new rotation
            rotation = self.init_rotation.copy()
            euler = rotation.to_euler()
            euler.z -= rotation_amount
            new_rotation = euler.to_quaternion()
            
            # Apply the rotation
            context.space_data.region_3d.view_rotation = new_rotation
            
            # Update text display (commented out)
            # degrees = math.degrees(euler.z) % 360
            # self.text_body = f"Roll: {degrees:.1f}°"
            
            # Display in header
            degrees = math.degrees(euler.z) % 360
            context.area.header_text_set(f"Roll Viewport: {degrees:.1f}°")

        elif event.type in {'LEFTMOUSE', self.input_type} and event.value == 'RELEASE':
            # Check if this was a quick click without much movement
            if (time() - self.start_time < 0.20 and 
                abs(self.current_rotation + self.cumulated_rotation) < 0.03):
                # Reset rotation to world Y axis up
                view_axis = mathutils.Vector((0.0, 0.0, 1.0))
                upright_quat = view_axis.to_track_quat('Z', 'Y')
                # Rotate 180 degrees around Z to get -Y up instead of Y
                rot_z_180 = mathutils.Quaternion((0.0, 0.0, 1.0), math.radians(180))
                upright_quat = rot_z_180 @ upright_quat
                context.space_data.region_3d.view_rotation = upright_quat
            
            self.execute(context)
            return {'FINISHED'}

        elif event.type == 'ESC':
            # Restore original rotation
            context.space_data.region_3d.view_rotation = self.init_rotation
            self.execute(context)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self.current_area = context.area
        self.input_type = event.type
        self.init_mouse_x = event.mouse_x
        self.init_rotation = context.space_data.region_3d.view_rotation.copy()
        
        # Initialize rotation tracking
        self.shift_pressed = event.shift
        self.cumulated_rotation = 0.0
        self.current_rotation = 0.0
        self.start_time = time()
        
        # Text overlay code (commented out)
        # self.text_body = "Roll: 0.0°"
        # self.text_position = (context.area.width / 2 - 60, event.mouse_region_y + 80)
        # self.text_size = 18.0
        # self.text_color = (0.0, 0.5, 1.0)
        # args = (self, context)
        # self._text_handle = bpy.types.SpaceView3D.draw_handler_add(draw.text_draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
        
        context.window.cursor_set("SCROLL_X")
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


classes=(
STORYTOOLS_OT_roll_minimap_viewport,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)