import bpy
import gpu

from time import time
from bpy.types import Operator
from math import pi
from mathutils import Vector, Matrix, geometry
from gpu_extras.batch import batch_for_shader
from .. import fn
from .. import draw

size = 0.5
cross = [
    # X axis
    Vector((0 - size, 0, 0)),
    Vector((0 + size, 0, 0)),
    # Y axis
    Vector((0, 0 - size, 0)),
    Vector((0, 0 + size, 0)),
    # Z axis
    Vector((0, 0, 0 - size)),
    Vector((0, 0, 0 + size))
]

class STORYTOOLS_OT_place_gp_object(Operator):
    bl_idname = "storytools.place_gp_object"
    bl_label = "Place New GP Object"
    bl_description = "Add and place a new Grease Pencil object\
        \nClick to start modal then click again to place\
        \nAlternatively drag to position\
        \nShift: Place on ground level instead of camera view level"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        return fn.is_minimap_viewport(context)

    def invoke(self, context, event):
        self.current_area = context.area
        self.init_mouse = Vector((event.mouse_x, event.mouse_y))
        self.start_time = time()
        self.drag_mode = False
        self.place_on_ground = event.shift
        self.placement_valid = False
        
        # Calculate button size similar to snap_3d_cursor
        # button_size = fn.get_addon_prefs().toolbar_backdrop_size
        ## hardcoded value (14) for minimap buttons
        self.distance_to_drag = 10
        
        # Get initial 3D position from mouse click
        self.cursor_pos = self.get_3d_position_from_mouse(context, event)
        
        # Set up line draw handlers
        args = (self, context)
       
        self.line_coords = []
        self.line_color = (1.0, 0.6, 0.3, 0.8)
        self.line_width = 2.0
        self.line_ghost = True
        self._line_handle = bpy.types.SpaceView3D.draw_handler_add(draw.line_draw_callback, (self, context), 'WINDOW', 'POST_VIEW')
        
        # Setup text
        self.text_body = 'Click/Drag to place new grease pencil'
        self.text_size = 16.0
        self.text_position = (20, 120)
        self._text_handle = bpy.types.SpaceView3D.draw_handler_add(draw.text_draw_callback_px, args, 'WINDOW', 'POST_PIXEL')

        context.window.cursor_set("CROSSHAIR")  # Set cursor to crosshair for better positioning
        context.window_manager.modal_handler_add(self)
        context.area.tag_redraw()
        return {'RUNNING_MODAL'}

    def update_position(self, context, event):
        # Update cross position with current mouse position
        new_pos = self.get_3d_position_from_mouse(context, event)
        self.cursor_pos = new_pos
        
        ## update text:
        # text = f"New GP Placement: x:{new_pos.x:.1f}, y:{new_pos.y:.1f}, z:{new_pos.z:.1f}"

        if self.placement_valid:
            text = "Click to place GP"
        else:
            text = "Release to place GP"

        if cam := context.scene.camera:
            distance = (cam.matrix_world.to_translation() - new_pos).length
            text += f"\nDistance to Camera: {distance:.1f}"
            
            ## calculate rotation to apply on overlay
            _, rot, _ = cam.matrix_world.decompose()
            rot_mat = rot.to_matrix().to_4x4() @ Matrix.Rotation(-pi/2, 4, 'X')
            rot_mat = rot_mat.to_3x3()
        else:
            rot_mat = Matrix.Rotation(0, 3, 'Z')

        placement_type = "ground level" if self.place_on_ground else "camera view level"
        text += f"\nMode (shift): {placement_type}"
        text += f"\nLocation: ({new_pos.x:.1f}, {new_pos.y:.1f}, {new_pos.z:.1f})"

        self.text_body = text
        context.area.header_text_set(text)
        ## Update line coordinates


        ## Create matrix to affect placement
        line_matrix = Matrix.LocRotScale(new_pos, rot_mat, Vector((1, 1, 1)))
        self.line_coords = [line_matrix @ v for v in cross]

        # size = 0.5
        # self.line_coords = [
        #     # X axis
        #     Vector((new_pos.x - size, new_pos.y, new_pos.z)),
        #     Vector((new_pos.x + size, new_pos.y, new_pos.z)),
        #     # Y axis
        #     Vector((new_pos.x, new_pos.y - size, new_pos.z)),
        #     Vector((new_pos.x, new_pos.y + size, new_pos.z)),
        #     # Z axis
        #     Vector((new_pos.x, new_pos.y, new_pos.z - size)),
        #     Vector((new_pos.x, new_pos.y, new_pos.z + size))
        # ]

        fn.refresh_areas()

    def get_3d_position_from_mouse(self, context, event):
        # Get 3D position from mouse coordinates
        region = context.region
        rv3d = context.space_data.region_3d
        
        # Get mouse coordinates
        mouse_coord = Vector((event.mouse_region_x, event.mouse_region_y))
        
        # Get view vector and origin
        view_vector = fn.region_to_location(mouse_coord, Vector((0, 0, -1000)))
        view_origin = rv3d.view_matrix.inverted().translation
        view_origin = Vector((*view_vector.xy, view_origin.z))
        
        if self.place_on_ground:
            # Cast ray to ground plane (Z=0)
            ground_point = geometry.intersect_line_plane(
                view_origin, view_vector, Vector((0, 0, 0)), Vector((0, 0, 1))
            )
            return ground_point
        else:
            # If we have a camera, place at camera's view plane
            if context.scene.camera:
                cam = context.scene.camera
                cam_mat = cam.matrix_world
                cam_loc = cam_mat.to_translation()
                
                # Create a plane parallel to camera view
                # Get up vector of the camera (-y)
                cam_forward = cam_mat.to_quaternion() @ Vector((0, -1, 0))
                
                # Create a plane at camera position perpendicular to forward vector
                cam_plane_point = geometry.intersect_line_plane(
                    view_origin, view_vector, cam_loc, cam_forward
                )
                
                if cam_plane_point:
                    return cam_plane_point
                
                # Fallback to camera height if intersection fails
                cam_height = cam_loc.z
                return geometry.intersect_line_plane(
                    view_origin, view_vector, Vector((0, 0, cam_height)), Vector((0, 0, 1))
                )
            else:
                # Default height if no camera
                default_height = 0.0 # 1.7  # Average human height
                height_plane_point = geometry.intersect_line_plane(
                    view_origin, view_vector, Vector((0, 0, default_height)), Vector((0, 0, 1))
                )
                return height_plane_point

    def exit_modal(self, context):
        context.window.cursor_set("DEFAULT")
        context.area.header_text_set(None)
        draw.stop_callback(self, context)
        fn.refresh_areas()

    def modal(self, context, event):
        mouse = Vector((event.mouse_x, event.mouse_y))
        
        # Check for drag mode on initial mouse movement
        if not self.drag_mode and not self.placement_valid:
            mouse_dist = (mouse - self.init_mouse).length
            if event.type == 'MOUSEMOVE' and mouse_dist > self.distance_to_drag:
                self.drag_mode = True
        
        # Handle mouse movement in drag mode
        if event.type == 'MOUSEMOVE':
            self.update_position(context, event)
        
        # Toggle ground placement with Shift
        elif event.type in {'LEFT_SHIFT', 'RIGHT_SHIFT'}:
            if event.value == 'PRESS':
                self.place_on_ground = True
                if self.drag_mode:
                    self.update_position(context, event)
            elif event.value == 'RELEASE':
                self.place_on_ground = False
                if self.drag_mode:
                    self.update_position(context, event)
        
                # Handle mouse button events
        elif event.type == 'LEFTMOUSE':
            if event.value == 'RELEASE':
                if self.drag_mode:
                    # Create object at current position after dragging
                    bpy.ops.storytools.create_object("INVOKE_DEFAULT", use_location=True, face_camera=True, location=self.cursor_pos)
                    self.exit_modal(context)
                    return {'FINISHED'}
                elif not self.placement_valid:
                    # First click just completed, prepare for second click
                    self.placement_valid = True
                    self.text_body = "Click again at position to place object"
                    context.area.tag_redraw()
                else:
                    # Second click, place the object
                    self.update_position(context, event)  # Get final position
                    bpy.ops.storytools.create_object("INVOKE_DEFAULT", use_location=True, face_camera=True, location=self.cursor_pos)
                    self.exit_modal(context)
                    return {'FINISHED'}
        
        # Cancel with right mouse or ESC
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.exit_modal(context)
            return {'CANCELLED'}
        
        return {'RUNNING_MODAL'}

classes=(
STORYTOOLS_OT_place_gp_object,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)