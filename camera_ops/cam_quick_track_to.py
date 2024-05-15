import bpy
from bpy.types import Operator
from .. import fn

class STORYTOOLS_OT_add_track_to_constraint(Operator):
    bl_idname = "storytools.add_track_to_constraint"
    bl_label = "Add TrackTo constraint"
    bl_description = "Create 'Track-to' constraint on camera, also known as 'Look at'\
        \nIf an empty is selected, used as target, else create a new empty"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.scene.camera

    def execute(self, context):
        # if not context.object:
        #     self.report({'ERROR'}, 'No active object')
        #     return {"CANCELLED"}

        empty_selection = [o for o in context.selected_objects if o.type == 'EMPTY']
        if empty_selection:
            emtpy = empty_selection[0]
        else:
            # create an empty
            pass

        # TODO: use the empty to create a track to constraint
        # TODO: expose track to constraints info and influence in subpanel

        return {"FINISHED"}


classes = (STORYTOOLS_OT_add_track_to_constraint,)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)