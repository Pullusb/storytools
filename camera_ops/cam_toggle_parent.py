import bpy
from bpy.types import Operator
from .. import fn

class STORYTOOLS_OT_attach_toggle(Operator):
    bl_idname = "storytools.attach_toggle"
    bl_label = "Attach Toggle"
    bl_description = "Parent / Unparent object to active Camera"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.object

    def execute(self, context):
        if not context.object:
            self.report({'ERROR'}, 'No active object')
            return {"CANCELLED"}
        
        if context.object == context.scene.camera:
            self.report({'ERROR'}, 'The active object is the camera')
            return {"CANCELLED"}

        mat = context.object.matrix_world.copy()
        if context.object.parent == context.scene.camera:
            # unparent
            context.object.parent = None # remove parent

        elif not context.object.parent:
            # parent
            context.object.parent = context.scene.camera # remove parent

        context.object.matrix_world = mat

        ## TODO: dynamic parent ? maybe need to double the key (custom keying)
        fn.key_object(context.object, use_autokey=True)

        return {"FINISHED"}


classes = (STORYTOOLS_OT_attach_toggle,)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)