import bpy
from bpy.types import Operator
from mathutils import Vector

class STORYTOOLS_OT_set_origin_bottom(Operator):
    bl_idname = "storytools.set_origin_bottom"
    bl_label = "Set Origin To Bottom"
    bl_description = "Set the origin of the selected Grease Pencil object to its bottom"
    bl_options = {"REGISTER", "UNDO"}

    def invoke(self, context, event):
        obj = context.object
        if obj.animation_data and obj.animation_data.action:
            ## Only confirmation dialog, 
            message = "Active object has animation data!\
                \nChanging the origin may cause unexpected results."
            return context.window_manager.invoke_confirm(
                self, event, title=self.bl_label, message=message, confirm_text="Set Origin Anyway", icon='WARNING')
        return self.execute(context)
    
    # def draw(self, context):
    #     layout = self.layout
    #     layout.label(text="Object has animation data", icon="ERROR")
    #     layout.label(text="Changing the origin may cause unexpected results.")

    def execute(self, context):
        # TODO: with grease pencil objects, move origin down according to the drawing axis 
        obj = context.object

        # if obj.animation_data:
        #     self.report({'WARNING'}, "Object has animation data. Changing the origin may cause unexpected results.")

        # Get the bounding box of the object
        bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        
        # Find the minimum Z coordinate of the bounding box
        min_z = min(corner.z for corner in bbox_corners)
        new_origin = Vector((0, 0, min_z))
        
        # Set the origin to the bottom of the bounding box
        obj.location = obj.location - new_origin
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
        obj.location = obj.location + new_origin

        return {"FINISHED"}


classes = (
    STORYTOOLS_OT_set_origin_bottom,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
