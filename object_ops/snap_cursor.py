import bpy

from bpy.types import Operator
from time import time
from mathutils import Vector, geometry
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

    def invoke(self, context, event):
        ## store the initial matrix of the cursor
        self.init_cursor_mat = context.scene.cursor.matrix.copy()
        self.init_mouse = Vector((event.mouse_region_x, event.mouse_region_y))
        self.start_time = time()
        button_size = fn.get_addon_prefs().toolbar_backdrop_size
        self.distance_to_drag = button_size * 0.7

        self.drag_mode = False

        ## Optional handler to show snap position
        # args = (self, context) # Dcb
        # self._pos_handle = bpy.types.SpaceView3D.draw_handler_add(draw.origin_position_callback, args, 'WINDOW', 'POST_VIEW') # Dcb
        # context.window.cursor_set("SCROLL_XY")
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
        # return {"CANCELLED"}

    def exit_modal(self, context):
        # context.area.header_text_set(None)
        # context.window.cursor_set("DEFAULT")
        draw.stop_callback(self, context) # Dcb

    def modal(self, context, event): 
        mouse = Vector((event.mouse_region_x, event.mouse_region_y))

        if not self.drag_mode:
            if time() - self.start_time < 0.25 and (mouse - self.init_mouse).length > (self.distance_to_drag * 0.7):
                ## is considered dragged
                self.drag_mode = True

        if event.type == 'MOUSEMOVE':
            if self.drag_mode:
                # TODO: only if active object is a GP object !
                if context.object and context.object.type == 'GREASEPENCIL':
                    ## set the cursor on the drawing plane
                    plane_co, plane_no = fn.get_gp_draw_plane(context)

                    rv3d = context.region_data
                    view_mat = rv3d.view_matrix.inverted()
                    
                    ## view origin in world space
                    origin = view_mat.inverted().translation
                    
                    ## Mouse in world space with arbitrary depth to raycast
                    arbitrary_depth_coord = view_mat @ Vector((0, 0, -5))
                    mouse_3d = fn.region_to_location(mouse, arbitrary_depth_coord)
                    # fn.empty_at(origin, "origin", size=0.1)
                    ## "raycast" to the plane
                    drawing_plane_hit = geometry.intersect_line_plane(origin, mouse_3d, plane_co, plane_no, True)
                    if drawing_plane_hit:
                        context.scene.cursor.location = drawing_plane_hit
                    # else:
                    #     # fallback to what ?
                    #     context.scene.cursor.location = mouse_3d


                    ## Further possibilities:
                    ## Align rotation as well with plane ?
                    ## Store previous cusor location to restore (don't know how that would be proposed to user)
                else:
                    # Code logic to use with geometry objects
                    pass

        if event.type == 'LEFTMOUSE':

            ## if less than 0.2 seconds, and in button, consider a click and trigger single click method
            if time() - self.start_time < 0.25 and (mouse - self.init_mouse).length < self.distance_to_drag:
                if event.shift:
                    bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)
                else:
                    bpy.ops.view3d.snap_cursor_to_selected()
                return {'FINISHED'}
                # return {'CANCELLED'}

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
