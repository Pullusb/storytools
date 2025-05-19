import bpy
from mathutils.geometry import intersect_line_plane
from mathutils import Vector
from .. import fn

class STORYTOOLS_OT_dolly_zoom_cam(bpy.types.Operator):
    bl_idname = "storytools.dolly_zoom_cam"
    bl_label = "Dolly Focale Change"
    bl_description = "Dolly/vertigo zoom effect: change focal length while adapting camera position to compensate\
        \nFocus on active object or 3D cursor if there is None"
    bl_options = {'REGISTER', 'UNDO'}

    # Properties for the operator
    focal_length : bpy.props.FloatProperty(name="Focal Length")
    
    initial_focal_length : bpy.props.FloatProperty()
    
    target_position : bpy.props.FloatVectorProperty(subtype='XYZ')
    
    initial_camera_position : bpy.props.FloatVectorProperty(subtype='XYZ')
    
    @classmethod
    def poll(cls, context):
        return context.scene.camera is not None and context.scene.camera.data.type == 'PERSP'

    def update_camera(self, context):
        camera = context.scene.camera
        if not camera:
            self.report({'ERROR'}, "No active camera in scene")
            return {'CANCELLED'}
            
        # Update camera focal length
        camera.data.lens = self.focal_length
        
        # Calculate and update camera position
        new_position = fn.calculate_dolly_zoom_position(
            Vector(self.initial_camera_position),
            Vector(self.target_position),
            self.initial_focal_length,
            self.focal_length
        )
        
        camera.matrix_world.translation = new_position
        return {'FINISHED'}

    def invoke(self, context, event):
        camera = context.scene.camera
        if not camera:
            self.report({'ERROR'}, "No active camera in scene")
            return {'CANCELLED'}
        
        # Store initial camera settings
        self.initial_focal_length = camera.data.lens
        self.focal_length = self.initial_focal_length
        self.initial_camera_position = camera.matrix_world.translation.copy()

        self.prev_mouse_x = event.mouse_x
        
        # Get target position - active object or 3D cursor
        if context.active_object:
            pos = context.active_object.matrix_world.translation.copy()
        else:
            pos = context.scene.cursor.location.copy()
        
        ## Center on camera view
        aim = Vector((0,0,1))
        aim.rotate(camera.matrix_world)
        pos = intersect_line_plane(self.initial_camera_position, self.initial_camera_position + aim * 10000, pos, aim)
        if pos is None:
            self.report({'ERROR'}, "Cannot find intersection point forward camera")
            return {'CANCELLED'}
        self.target_position = pos

        ## run modal
        context.window.cursor_set("SCROLL_X")
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def exit(self, context):
        context.window.cursor_set("DEFAULT")
        context.area.header_text_set(None) # Reset header

    def modal(self, context, event):        
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            # Restore initial focal length and position
            camera = context.scene.camera
            if camera:
                camera.data.lens = self.initial_focal_length
                camera.matrix_world.translation = self.initial_camera_position
            self.exit(context)
            return {'CANCELLED'}

        if event.type in {'LEFTMOUSE', 'RET', 'NUMPAD_ENTER', 'SPACE'}:
            self.exit(context)
            return {'FINISHED'}

        if event.type == 'MOUSEMOVE':
            # Update focal length based on mouse movement
            delta = event.mouse_x - self.prev_mouse_x
            focal_offset = delta * 0.1
            self.focal_length = self.initial_focal_length + focal_offset
            self.update_camera(context)
            context.area.header_text_set(f'Focal Length : {self.initial_focal_length:.2f}mm -> {self.focal_length:.2f}mm ({focal_offset:.2f} offset)')
        return {'RUNNING_MODAL'}

classes=(
STORYTOOLS_OT_dolly_zoom_cam,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)