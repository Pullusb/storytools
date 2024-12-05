import bpy

from bpy.types import Operator

class STORYTOOLS_OT_autokey_switch(Operator):
    bl_idname = "storytools.autokey_switch"
    bl_label = 'Autokey Toggle'
    bl_description = "Toggle autokey (in all scenes)"
    bl_options = {'REGISTER', 'INTERNAL'} # 'UNDO',

    @classmethod
    def poll(cls, context):
        return True

    all_scene : bpy.props.BoolProperty(default=True)

    def execute(self, context):
        new_state = not context.scene.tool_settings.use_keyframe_insert_auto

        if self.all_scene:
            scenes = bpy.data.scenes 
        else:
            scenes = [context.scene]
        
        for scene in scenes:
            scene.tool_settings.use_keyframe_insert_auto = new_state

        ## TODO For cross scene modification, should be a preferences
        ## and add a msgbus subscribed to autolock prop.
        return {"FINISHED"}


classes=(
STORYTOOLS_OT_autokey_switch,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
