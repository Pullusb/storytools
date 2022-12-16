# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.types import Operator
from .preferences import get_addon_prefs



class STORYTOOLS_OT_opsname_modal(Operator):
    bl_idname = "storytools."
    bl_label = "Opsname Modal"
    bl_description = "Description that shows in blender tooltips"
    bl_options = {"REGISTER", "UNDO"} # INTERNAL

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'MESH'#True

    shift : bpy.props.BoolProperty(name='Shifter', default=False)

    def invoke(self, context, event):
        # if context.mode not in ('PAINT_GPENCIL', 'EDIT_GPENCIL'):
        #     return {"CANCELLED"}
        self.shift = event.shift
        self.homogen_pressure = event.ctrl

        ## for a modal
        # context.window_manager.modal_handler_add(self)
        # return {'RUNNING_MODAL'}
        return self.execute(context)


    # def modal(self, context, event):
        # return {'PASS_THROUGH'}
        # return {"RUNNING_MODAL"}

    def execute(self, context):
        print('Hi!')        
        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "shift")


classes=(
#STORYTOOLS_OT_opsname,
STORYTOOLS_OT_opsname_modal,
)

def register(): 
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)