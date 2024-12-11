import bpy

from bpy.types import Operator
from time import time
from mathutils import Vector, Matrix, geometry
from .. import draw
from .. import fn

class STORYTOOLS_OT_snap_3d_cursor(Operator):
    bl_idname = "storytools.snap_3d_cursor"
    bl_label = 'Snap 3D Cursor'
    bl_description = "Snap 3D Cursor\
        \nClick: Cursor to selected\
        \nShift + Click: Send Selection to cursor\
        \nClick-Drag: Cursor on GP drawing plane or geometry"
    bl_options = {'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return True

    all_scene : bpy.props.BoolProperty(default=True)

    set_cursor_rotation : bpy.props.BoolProperty(default=False, options={'SKIP_SAVE'})

    def invoke(self, context, event):
        ## store the initial matrix of the cursor
        self.init_cursor_mat = context.scene.cursor.matrix.copy()
        self.init_mouse = Vector((event.mouse_region_x, event.mouse_region_y))
        self.start_time = time()
        button_size = fn.get_addon_prefs().toolbar_backdrop_size
        self.distance_to_drag = button_size * 0.7

        self.drag_mode = False

        self.on_gp_object = context.object and context.object.type == 'GREASEPENCIL'

        self._grid_handle = None

        ## show snapping plane position (just comment to disable)
        if fn.get_addon_prefs().use_visual_hint and self.on_gp_object:
            ## for draw.draw_callback_wall (but not adapted for this case)
            # r3d = context.space_data.region_3d
            # ## Prepare coordinate for GPU draw
            # d = 1000
            # z_offset = 0.006
            # self.coords = [
            #     Vector((-d,-d, -z_offset)),
            #     Vector((d,-d, -z_offset)),
            #     Vector((0, d, -z_offset)),
            # ]
            # for v in self.coords:
            #     v.rotate(r3d.view_rotation)
            #     v += context.object.matrix_world.to_translation()
            
            # self.front_coords = [
            #     Vector((-d,-d, z_offset)),
            #     Vector((d,-d, z_offset)),
            #     Vector((0, d, z_offset)),
            # ]
            # for v in self.front_coords:
            #     v.rotate(r3d.view_rotation)
            #     v += context.object.matrix_world.to_translation()

            ## calculate grid
            gp_plane_matrix = fn.get_gp_draw_plane_matrix(context)
            if gp_plane_matrix:
                ## Define the half size of the plane
                half_size = 10

                ## Calculate the corners of the plane in local space
                ## 4 corners
                # local_corners = [
                #     Vector((-half_size, -half_size, 0)),
                #     Vector((half_size, -half_size, 0)),
                #     Vector((half_size, half_size, 0)),
                #     Vector((-half_size, half_size, 0))
                # ]
                # self.coords = [gp_plane_matrix @ corner for corner in local_corners]

                subdiv = context.space_data.overlay.gpencil_grid_subdivisions
                grid_size = 1.0 / subdiv
                # grid_size = 1.0 / (subdiv * 2) # on half the squares
                
                # grid_size = 0.125
                num_lines = int((half_size / grid_size) * 2) 

                grid = []

                for i in range(-num_lines // 2, num_lines // 2 + 1):
                    grid.append(Vector((i * grid_size, -half_size, 0)))
                    grid.append(Vector((i * grid_size, half_size, 0)))
                    grid.append(Vector((-half_size, i * grid_size, 0)))
                    grid.append(Vector((half_size, i * grid_size, 0)))

                self.coords = [gp_plane_matrix @ corner for corner in grid]

                # fn.empty_at(self.coords[0], "corner1", size=0.1)
                # fn.empty_at(self.coords[1], "corner2", size=0.1)

                # self.current_area = context.area # test also without and multi screen, maybe better
                args = (self, context) # Dcb
                self._grid_handle = bpy.types.SpaceView3D.draw_handler_add(draw.gp_plane_callback, args, 'WINDOW', 'POST_VIEW') # Dcb
    
                ## set the cursor on the drawing plane
                # self.plane_co, self.plane_no = fn.get_gp_draw_plane(context)
                self.plane_co = gp_plane_matrix.to_translation()
                self.plane_no = Vector((0.0, 0.0, 1.0))
                self.plane_no.rotate(gp_plane_matrix)
                
                self.cursor_rotation = gp_plane_matrix.to_euler()

                rv3d = context.region_data
                view_mat = rv3d.view_matrix.inverted()
                
                ## view origin in world space
                self.origin = view_mat.translation
                ## Mouse in world space with arbitrary depth to raycast
                self.arbitrary_depth_coord = view_mat @ Vector((0, 0, -1000))

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def exit_modal(self, context):
        context.window.cursor_set("DEFAULT")
        context.area.header_text_set(None)
        draw.stop_callback(self, context) # Dcb

    def modal(self, context, event):
        mouse = Vector((event.mouse_region_x, event.mouse_region_y))

        if not self.drag_mode:
            if time() - self.start_time < 0.25 and (mouse - self.init_mouse).length > (self.distance_to_drag * 0.7):
                ## Pass here once when considered dragged
                self.drag_mode = True
                context.window.cursor_set("SCROLL_XY")

        if event.type == 'MOUSEMOVE':
            if self.drag_mode:                
                if self.on_gp_object:
                    # rot_mode = 'ON' if self.cursor_rotation else 'OFF' (do ont refresh while drawging)
                    # context.area.header_text_set(f"Cursor on Grease Pencil Canvas | Align Cursor Rotation: {rot_mode} (R to switch)")
                    context.area.header_text_set(f"Cursor on Grease Pencil Canvas | R: Toggle align cursor rotation to plane")
                    if self.set_cursor_rotation:
                        ## Align cursor 
                        # context.scene.cursor.rotation_euler = rv3d.view_rotation.to_euler() # align to view
                        context.scene.cursor.rotation_euler = self.cursor_rotation
                    else:
                        context.scene.cursor.matrix = self.init_cursor_mat

                    ## Project on GP plane (calculated in invoke)
                    mouse_3d = fn.region_to_location(mouse, self.arbitrary_depth_coord)
                    ## "raycast" to the plane
                    drawing_plane_hit = geometry.intersect_line_plane(self.origin, mouse_3d, self.plane_co, self.plane_no, True)

                    if drawing_plane_hit:
                        context.scene.cursor.location = drawing_plane_hit

                else:
                    # Code logic to use with geometry objects
                    context.area.header_text_set(f"Cursor to view")
                    bpy.ops.view3d.cursor3d('INVOKE_DEFAULT')

        if event.type == 'LEFTMOUSE':

            ## if less than 0.2 seconds, and in button, consider a click and trigger single click method
            if time() - self.start_time < 0.25 and (mouse - self.init_mouse).length < self.distance_to_drag:
                if event.shift:
                    bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)
                else:
                    bpy.ops.view3d.snap_cursor_to_selected()
                self.exit_modal(context)
                return {'CANCELLED'}

            ## More time but still in circle "cancel the drag" ?
            if self.drag_mode and (mouse - self.init_mouse).length < self.distance_to_drag:
                # User got back in the circle... either apply the drag or cancel it
                context.scene.cursor.matrix = self.init_cursor_mat

            ## Just exit are 
            self.exit_modal(context)
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            # reset cursor matrix and exit
            context.scene.cursor.matrix = self.init_cursor_mat
            self.exit_modal(context)
            return {'CANCELLED'}

        if event.type == 'R' and event.value == 'PRESS':
            if self.on_gp_object:
                self.set_cursor_rotation = not self.set_cursor_rotation
                context.area.tag_redraw()

        return {'RUNNING_MODAL'}

    def execute(self, context):
        return {"FINISHED"}


classes=(
STORYTOOLS_OT_snap_3d_cursor,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
